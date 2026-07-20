from __future__ import annotations

import io
import json
import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.audit_artifacts import audit_artifacts
from scripts.curate_artifacts import apply_curation, plan_curation
from scripts.regenerate_offline_fixtures import regenerate
from scripts.validate_outputs import validate_outputs
from src.common.io import ensure_directory
from src.common.logging_utils import _StructuredFormatter, redact_log_value, setup_logging
from src.config.catalog import domains_to_process, entities_to_process, output_exists
from src.config.schemas import (
    stable_identifier,
    validate_domains_config,
    validate_entities_config,
    validate_languages_config,
)
from src.perplexity.clients import (
    ChatPolicy,
    CompletionUsage,
    ProviderAdapter,
    ProviderOfflineError,
    ProviderRequestError,
    RequestLimiter,
    _retry_after_seconds,
    complete_chat_result,
)
from src.perplexity.translation import process_translations_detailed
from src.pipeline import (
    ArtifactRecord,
    PipelineResult,
    PipelineRunner,
    RunManifest,
    StageItemResult,
    StageResult,
    StageSpec,
    StageStatus,
    StructuredPayloadError,
    parse_curriculum_response,
    parse_research_response,
    parse_structured_response,
    parse_translation_response,
    payload_markdown,
    validate_generated_text,
    validate_translation,
)
from src.pipeline.artifacts import create_run_directory, sha256_file, sha256_text, write_json_atomic
from src.pipeline.history import list_runs, prune_runs, retention_candidates, summarize_runs
from src.pipeline.stages import get_research_files, process_research_directory_detailed
from src.visualization.runner import run as run_visualizations


def test_typed_configuration_assigns_stable_ids_and_rejects_bad_provenance() -> None:
    assert stable_identifier("Karl Friston") == "karl_friston"
    domains = validate_domains_config(
        {
            "domains": [
                {
                    "name": "Research Domain",
                    "description": "A domain",
                    "category": "science",
                    "keywords": ["one"],
                    "source_urls": ["https://example.com/source"],
                    "verification_date": "2026-07-17",
                }
            ]
        }
    )
    assert domains[0].id == "research_domain"
    assert domains[0].source_urls == ("https://example.com/source",)
    with pytest.raises(ValueError, match="unsafe source"):
        validate_entities_config(
            {
                "entities": [
                    {
                        "name": "reader",
                        "description": "A reader",
                        "category": "audience",
                        "source_urls": ["file:///private/source"],
                    }
                ]
            }
        )


def test_catalog_filters_and_output_lookup_use_stable_ids(tmp_path: Path) -> None:
    config = {
        "domains": [
            {"name": "Bio Chemistry", "priority": "high", "category": "science"},
            {"name": "Art", "priority": "low", "category": "humanities"},
        ],
        "entities": [
            {"name": "Reader One", "priority": "high"},
            {"name": "Reader Two", "priority": "low"},
        ],
    }
    assert [item["name"] for item in domains_to_process(config, priority="high")] == [
        "Bio Chemistry"
    ]
    assert [item["name"] for item in domains_to_process(config, category="humanities")] == ["Art"]
    assert [item["name"] for item in entities_to_process(config, priority="low")] == ["Reader Two"]
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    (output_dir / "bio_chemistry_research_20260718.json").write_text("{}", encoding="utf-8")
    assert output_exists(output_dir, "Bio Chemistry", kind="research")
    assert not output_exists(output_dir, "Unknown", kind="research")
    with pytest.raises(ValueError, match="duplicate"):
        validate_languages_config({"target_languages": ["Spanish", "spanish"]})
    with pytest.raises(ValueError, match="stable slug"):
        validate_domains_config(
            {
                "domains": [
                    {
                        "name": "Bad category",
                        "description": "A domain",
                        "category": "not a slug",
                    }
                ]
            }
        )
    with pytest.raises(ValueError, match="duplicates"):
        validate_entities_config(
            {
                "entities": [
                    {
                        "name": "reader",
                        "description": "A reader",
                        "category": "audience",
                        "source_urls": ["https://example.com", "https://example.com"],
                    }
                ]
            }
        )
    with pytest.raises(ValueError, match="publication mode"):
        validate_domains_config(
            {
                "domains": [
                    {
                        "name": "Unverified",
                        "description": "A domain",
                        "category": "science",
                        "keywords": [],
                    }
                ]
            },
            require_provenance=True,
        )


def test_artifact_manifest_and_atomic_json_round_trip(tmp_path: Path) -> None:
    run_dir = create_run_directory(tmp_path / "runs", "safe run/one")
    output = run_dir / "output.txt"
    output.write_text("result", encoding="utf-8")
    record = ArtifactRecord.from_path(str(output), kind="text", stage="render", item_id="x")
    manifest = RunManifest(
        run_id="safe-run-one",
        stages=[StageResult("render", output_paths=[str(output)])],
        artifacts=[record],
        provenance={"evidence_status": "offline_fixture"},
    )
    path = tmp_path / "manifest.json"
    manifest.write(str(path))
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["artifacts"][0]["sha256"] == sha256_text("result")
    assert payload["provider_metadata"] == {}
    assert payload["prompt_versions"] == {}
    write_json_atomic(tmp_path / "atomic.json", {"ok": True})
    assert json.loads((tmp_path / "atomic.json").read_text(encoding="utf-8"))["ok"]


def test_pipeline_dependencies_resume_and_optional_failures(tmp_path: Path) -> None:
    calls: list[str] = []
    specs = [
        StageSpec("acquire"),
        StageSpec("prepare", depends_on=("acquire",)),
        StageSpec("optional", depends_on=("acquire",), required=False),
        StageSpec("render", depends_on=("prepare",)),
    ]

    def handler(name: str, status: StageStatus = StageStatus.SUCCEEDED):
        def run(_context):
            calls.append(name)
            return StageResult(
                name,
                status=status,
                items={name: StageItemResult(name, status)},
            )

        return run

    first = PipelineRunner(specs, work_root=tmp_path / "runs", run_id="demo")
    result = first.run(
        {
            "acquire": handler("acquire"),
            "prepare": handler("prepare"),
            "optional": handler("optional", StageStatus.FAILED),
            "render": handler("render"),
        }
    )
    assert result.ok is True
    assert result.ok
    assert calls == ["acquire", "prepare", "optional", "render"]

    calls.clear()
    resumed = PipelineRunner(specs, work_root=tmp_path / "runs", run_id="demo")
    resumed_result = resumed.run(
        {name: handler(name) for name in ("acquire", "prepare", "optional", "render")}
    )
    assert resumed_result.ok is True
    assert calls == []


def test_pipeline_publishes_item_artifacts_and_refuses_tampered_resume(tmp_path: Path) -> None:
    output = tmp_path / "result.txt"

    def render(_context):
        output.write_text("published", encoding="utf-8")
        digest = sha256_file(output)
        return StageResult(
            "render",
            items={
                "demo": StageItemResult(
                    "demo",
                    output_paths=[str(output)],
                    artifact_hashes={str(output): digest},
                    provenance={"evidence_status": "offline_fixture"},
                    usage={"prompt_tokens": 2, "completion_tokens": 3},
                )
            },
        )

    runner = PipelineRunner(
        [StageSpec("render")],
        work_root=tmp_path / "runs",
        run_id="artifact-demo",
    )
    result = runner.run({"render": render})
    assert result.ok
    manifest = json.loads((tmp_path / "runs" / "artifact-demo" / "manifest.json").read_text())
    assert manifest["artifacts"][0]["item_id"] == "demo"
    assert manifest["artifacts"][0]["artifact_id"].startswith("render:demo:")
    assert manifest["usage"]["total_tokens"] == 5

    output.write_text("tampered", encoding="utf-8")
    resumed = PipelineRunner(
        [StageSpec("render")],
        work_root=tmp_path / "runs",
        run_id="artifact-demo",
    )
    tampered = resumed.run({"render": render})
    assert tampered.ok is False
    assert any("changed" in error for error in tampered.errors)


def test_pipeline_budget_stops_before_downstream_stage_and_does_not_publish_failures(
    tmp_path: Path,
) -> None:
    partial = tmp_path / "partial.txt"
    calls: list[str] = []

    def first(_context):
        calls.append("first")
        partial.write_text("unpublished partial", encoding="utf-8")
        return StageResult(
            "first",
            items={
                "item": StageItemResult(
                    "item",
                    usage={"actual_cost_usd": 0.02, "total_tokens": 10},
                    output_paths=[str(partial)],
                )
            },
        )

    def second(_context):
        calls.append("second")
        return StageResult("second")

    result = PipelineRunner(
        [StageSpec("first"), StageSpec("second", depends_on=("first",))],
        work_root=tmp_path / "runs",
        run_id="budget",
        budget_limit_usd=0.01,
    ).run({"first": first, "second": second})
    assert result.ok is False
    assert calls == ["first"]
    assert any("exceeds budget" in error for error in result.errors)
    manifest = json.loads((tmp_path / "runs" / "budget" / "manifest.json").read_text())
    assert manifest["artifacts"] == []


def test_pipeline_refuses_artifacts_outside_declared_output_roots(tmp_path: Path) -> None:
    outside = tmp_path / "outside.txt"

    def write_outside(_context):
        outside.write_text("should not publish", encoding="utf-8")
        return StageResult(
            "render",
            items={"item": StageItemResult("item", output_paths=[str(outside)])},
        )

    result = PipelineRunner(
        [StageSpec("render")],
        work_root=tmp_path / "runs",
        run_id="root-boundary",
        allowed_output_roots=[tmp_path / "allowed"],
    ).run({"render": write_outside})
    assert result.ok is False
    assert any("outside allowed output roots" in error for error in result.errors)
    manifest = json.loads(
        (tmp_path / "runs" / "root-boundary" / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["artifacts"] == []


def test_pipeline_blocks_required_dependents_and_detects_cycles(tmp_path: Path) -> None:
    runner = PipelineRunner(
        [StageSpec("a"), StageSpec("b", depends_on=("a",))],
        work_root=tmp_path,
        run_id="blocked",
    )
    result = runner.run({"a": lambda _ctx: StageResult("a", errors=["nope"])})
    assert result.ok is False
    assert next(stage for stage in result.stages if stage.name == "b").status == StageStatus.BLOCKED
    with pytest.raises(ValueError, match="cycle"):
        PipelineRunner(
            [StageSpec("a", depends_on=("b",)), StageSpec("b", depends_on=("a",))],
            work_root=tmp_path,
            run_id="cycle",
        )


def test_quality_checks_distinguish_structure_from_truth() -> None:
    report = validate_generated_text("# Heading\n\ncontent", require_sections=True)
    assert report.valid
    assert not validate_generated_text("short", min_words=2).valid
    translation = validate_translation("# A\nsource", "# A\ntranslated", "Spanish")
    assert translation.valid
    assert parse_research_response("source https://example.com").citations
    parsed = parse_curriculum_response("# One\n\ncontent")
    assert parsed.sections["One"] == "content"
    assert parse_translation_response("# A\nsource", "# A\ntranslated", "Spanish").quality.valid


def test_provider_adapter_offline_and_malformed_payloads() -> None:
    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **_kwargs: SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))]
                )
            )
        )
    )
    policy = ChatPolicy(model="local", min_content_length=1, jitter_seconds=0)
    adapter = ProviderAdapter(client, provider="local", policy=policy)
    result = adapter.complete([{"role": "user", "content": "hello"}])
    assert result.content == "ok"
    with pytest.raises(ProviderOfflineError):
        complete_chat_result(
            client,
            [{"role": "user", "content": "hello"}],
            policy,
            offline=True,
        )
    bad_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **_kwargs: SimpleNamespace(choices=[]))
        )
    )
    with pytest.raises(ProviderRequestError):
        complete_chat_result(
            bad_client,
            [{"role": "user", "content": "hello"}],
            policy,
        )
    limiter = RequestLimiter(1)
    with limiter:
        pass
    cancelled = threading.Event()
    cancelled.set()
    with pytest.raises(ProviderRequestError, match="cancelled"):
        ProviderAdapter(
            client,
            provider="local",
            policy=policy,
            cancellation_event=cancelled,
        ).complete([{"role": "user", "content": "hello"}])


def test_provider_retry_classification_honors_retry_after_and_redacts_keys() -> None:
    class RateLimitError(Exception):
        status_code = 429

        def __init__(self) -> None:
            self.response = SimpleNamespace(headers={"Retry-After": "0"})
            super().__init__("Bearer sk-secret-value")

    attempts = {"count": 0}

    def create(**_kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RateLimitError()
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))],
            usage=SimpleNamespace(prompt_tokens=2, completion_tokens=3, total_tokens=5),
        )

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    result = complete_chat_result(
        client,
        [{"role": "user", "content": "hello"}],
        ChatPolicy(model="local", max_retries=2, jitter_seconds=0),
    )
    assert result.attempts == 2
    assert result.usage.total_tokens == 5

    class BadRequest(Exception):
        status_code = 400

    permanent = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **_kwargs: (_ for _ in ()).throw(BadRequest("sk-secret"))
            )
        )
    )
    with pytest.raises(ProviderRequestError) as error:
        complete_chat_result(
            permanent,
            [{"role": "user", "content": "hello"}],
            ChatPolicy(model="local", max_retries=3, jitter_seconds=0),
        )
    assert "sk-secret" not in str(error.value)
    assert "BadRequest" in str(error.value)


def test_provider_cancellation_interrupts_backoff_without_exposing_prompt() -> None:
    class ServerError(Exception):
        status_code = 503

    cancelled = threading.Event()

    def create(**_kwargs):
        cancelled.set()
        raise ServerError("sensitive prompt content")

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    with pytest.raises(ProviderRequestError, match="cancelled") as error:
        complete_chat_result(
            client,
            [{"role": "user", "content": "private prompt"}],
            ChatPolicy(model="local", max_retries=3, backoff_seconds=10, jitter_seconds=0),
            cancellation_event=cancelled,
        )
    assert "sensitive prompt" not in str(error.value)


def test_provider_retry_matrix_and_http_date_retry_after() -> None:
    class ClientError(Exception):
        status_code = 400

    client_error = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **_kwargs: (_ for _ in ()).throw(ClientError())
            )
        )
    )
    with pytest.raises(ProviderRequestError) as permanent:
        complete_chat_result(
            client_error,
            [{"role": "user", "content": "hello"}],
            ChatPolicy(model="local", max_retries=4, backoff_seconds=0, jitter_seconds=0),
        )
    assert permanent.value.attempts == 1
    assert permanent.value.retryable is False

    class ServerError(Exception):
        status_code = 503

    attempts = {"count": 0}

    def retryable_create(**_kwargs):
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise ServerError()
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="successful response"))]
        )

    successful = complete_chat_result(
        SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=retryable_create))),
        [{"role": "user", "content": "hello"}],
        ChatPolicy(model="local", max_retries=2, backoff_seconds=0, jitter_seconds=0),
    )
    assert successful.attempts == 2

    class TimeoutError(Exception):
        pass

    timeout_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **_kwargs: (_ for _ in ()).throw(TimeoutError())
            )
        )
    )
    with pytest.raises(ProviderRequestError) as timeout:
        complete_chat_result(
            timeout_client,
            [{"role": "user", "content": "hello"}],
            ChatPolicy(model="local", max_retries=2, backoff_seconds=0, jitter_seconds=0),
        )
    assert timeout.value.retryable is True
    retry_after = format_datetime(datetime.now(timezone.utc) - timedelta(seconds=1), usegmt=True)
    rate_limited = SimpleNamespace(response=SimpleNamespace(headers={"Retry-After": retry_after}))
    assert _retry_after_seconds(rate_limited) is not None
    assert _retry_after_seconds(rate_limited) >= 0


def test_provider_usage_prefers_provider_reported_cost_and_logs_redact_secrets() -> None:
    usage = CompletionUsage(
        prompt_tokens=3,
        completion_tokens=4,
        total_tokens=7,
        estimated_cost_usd=0.01,
        actual_cost_usd=0.007,
    )
    payload = usage.as_dict()
    assert payload["actual_cost_usd"] == 0.007
    assert payload["requests"] == 1
    assert "sk-super-secret" not in redact_log_value("Bearer sk-super-secret")

    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **_kwargs: SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content="usable"))],
                    usage=SimpleNamespace(
                        prompt_tokens=3,
                        completion_tokens=4,
                        total_tokens=7,
                        cost=0.007,
                    ),
                )
            )
        )
    )
    result = complete_chat_result(
        client,
        [{"role": "user", "content": "hello"}],
        ChatPolicy(model="local", max_retries=1, jitter_seconds=0),
    )
    assert result.usage.actual_cost_usd == 0.007


def test_structured_log_formatter_redacts_credentials_and_preserves_run_id() -> None:
    formatter = _StructuredFormatter()
    record = logging.LogRecord(
        "start",
        logging.INFO,
        __file__,
        1,
        "Bearer sk-secret-value for prompt content",
        (),
        None,
    )
    record.run_id = "run-123"
    payload = json.loads(formatter.format(record))
    assert payload["run_id"] == "run-123"
    assert "sk-secret-value" not in payload["message"]
    assert "prompt content" in payload["message"]


def test_provider_retry_exhaustion_reports_attempt_count_without_prompt() -> None:
    class ServerError(Exception):
        status_code = 503

    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **_kwargs: (_ for _ in ()).throw(ServerError("private prompt"))
            )
        )
    )
    with pytest.raises(ProviderRequestError) as error:
        complete_chat_result(
            client,
            [{"role": "user", "content": "private prompt"}],
            ChatPolicy(model="local", max_retries=2, backoff_seconds=0, jitter_seconds=0),
        )
    assert error.value.attempts == 2
    assert error.value.retryable is True
    assert "private prompt" not in str(error.value)


def test_provider_limiter_caps_concurrent_requests() -> None:
    from concurrent.futures import ThreadPoolExecutor

    lock = threading.Lock()
    active = 0
    peak = 0

    def create(**_kwargs):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        time.sleep(0.01)
        with lock:
            active -= 1
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="bounded response"))]
        )

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    adapter = ProviderAdapter(
        client,
        provider="local",
        policy=ChatPolicy(model="local", max_retries=1, jitter_seconds=0),
        limiter=RequestLimiter(2),
    )
    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(
            executor.map(
                lambda _item: adapter.complete([{"role": "user", "content": "hello"}]),
                range(6),
            )
        )
    assert len(results) == 6
    assert peak <= 2


def test_structured_logging_redacts_sensitive_values() -> None:
    logger_name = "start-structured-test"
    logger = logging.getLogger(logger_name)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    logger.propagate = False
    logger = setup_logging(name=logger_name, structured=True)
    stream = io.StringIO()
    logger.handlers[0].setStream(stream)
    logger.error("provider failed with Bearer sk-private-token")
    payload = json.loads(stream.getvalue())
    assert payload["level"] == "ERROR"
    assert "sk-private-token" not in payload["message"]


def test_safe_directory_boundary_rejects_symlink(tmp_path: Path) -> None:
    target = tmp_path / "real"
    target.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable on this filesystem")
    with pytest.raises(ValueError, match="symlink"):
        ensure_directory(link / "nested")


def test_structured_response_serialization_and_script_quality() -> None:
    research = parse_research_response("source https://example.com.")
    assert research.as_dict()["citations"] == ["https://example.com"]
    curriculum = parse_curriculum_response("# One\n\nSame\n\n# Two\n\nSame")
    assert curriculum.as_dict()["quality"]["warnings"]
    hindi = validate_translation("# शीर्षक\nsource", "# शीर्षक\nअनुवाद", "Hindi")
    assert hindi.valid
    assert not validate_translation("# عنوان\nsource", "# Title\ntranslated", "Arabic").valid


def test_strict_provider_schemas_reject_malformed_and_empty_payloads() -> None:
    research = parse_structured_response(
        json.dumps(
            {
                "schema_version": "1.0",
                "kind": "research",
                "content": "A sourced report",
                "citations": ["https://example.com/source"],
            }
        ),
        "research",
    )
    assert research.citations == ("https://example.com/source",)
    curriculum = parse_structured_response(
        json.dumps(
            {
                "schema_version": "1.0",
                "kind": "curriculum",
                "sections": {"Introduction": "A detailed section"},
            }
        ),
        "curriculum",
    )
    assert curriculum.sections == {"Introduction": "A detailed section"}
    with pytest.raises(StructuredPayloadError, match="valid JSON"):
        parse_structured_response("not json", "research")
    with pytest.raises(StructuredPayloadError, match="at least one citation"):
        parse_structured_response(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "kind": "research",
                    "content": "uncited",
                    "citations": [],
                }
            ),
            "research",
        )
    with pytest.raises(StructuredPayloadError, match="empty"):
        parse_structured_response(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "kind": "translation",
                    "content": "",
                    "target_language": "Spanish",
                }
            ),
            "translation",
        )


def test_structured_provider_schema_rejects_wrong_envelopes_and_renders_fenced_json() -> None:
    fenced = parse_structured_response(
        "```json\n"
        + json.dumps(
            {
                "schema_version": "1.0",
                "kind": "research",
                "content": "Sourced material",
                "citations": ["https://example.com", "https://example.com"],
            }
        )
        + "\n```",
        "research",
    )
    assert fenced.citations == ("https://example.com",)
    assert payload_markdown(fenced) == "Sourced material"

    with pytest.raises(StructuredPayloadError, match="schema_version"):
        parse_structured_response(
            json.dumps(
                {
                    "schema_version": "2.0",
                    "kind": "research",
                    "content": "source",
                    "citations": ["https://example.com"],
                }
            ),
            "research",
        )
    with pytest.raises(StructuredPayloadError, match="kind"):
        parse_structured_response(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "kind": "translation",
                    "content": "source",
                    "citations": [],
                }
            ),
            "research",
        )
    with pytest.raises(ValueError, match="unsupported"):
        parse_structured_response("{}", "unsupported")
    with pytest.raises(StructuredPayloadError, match="sections"):
        parse_structured_response(
            json.dumps({"schema_version": "1.0", "kind": "curriculum", "sections": {}}),
            "curriculum",
        )
    with pytest.raises(StructuredPayloadError, match="target_language"):
        parse_structured_response(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "kind": "translation",
                    "content": "translated",
                }
            ),
            "translation",
        )


def test_artifact_audit_is_non_destructive_and_reports_provenance(tmp_path: Path) -> None:
    target = tmp_path / "data" / "written_curriculums" / "reader"
    target.mkdir(parents=True)
    (target / "complete_curriculum.md").write_text("# no metadata", encoding="utf-8")
    (target / "README.md").write_text("directory guidance", encoding="utf-8")
    (target / "AGENTS.md").write_text("repository guidance", encoding="utf-8")
    run_state = tmp_path / "data" / "written_curriculums" / ".runs" / "run-1"
    run_state.mkdir(parents=True)
    (run_state / "manifest.json").write_text("{}", encoding="utf-8")
    report = audit_artifacts(tmp_path)
    assert report["summary"]["file_count"] == 1
    assert report["summary"]["unprovenanced_count"] == 1
    assert (target / "complete_curriculum.md").exists()


def test_artifact_curation_is_plan_first_and_hash_checked(tmp_path: Path) -> None:
    root = tmp_path / "project"
    artifact = root / "data" / "written_curriculums" / "reader.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("review me", encoding="utf-8")
    audit_path = root / "data" / "artifact-manifests" / "current.json"
    audit_path.parent.mkdir(parents=True)
    audit_path.write_text(json.dumps(audit_artifacts(root)), encoding="utf-8")
    keep_path = tmp_path / "review.json"
    keep_path.write_text(json.dumps({"keep": []}), encoding="utf-8")
    plan = plan_curation(audit_path, keep_path)
    assert plan["candidate_count"] == 1
    assert artifact.exists()
    artifact.write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="changed since audit"):
        apply_curation(plan, archive_dir=tmp_path / "archive", remove=False)

    artifact.write_text("review me", encoding="utf-8")
    changed = apply_curation(plan, archive_dir=tmp_path / "archive", remove=False)
    assert changed == ["data/written_curriculums/reader.md"]
    assert not artifact.exists()
    assert (tmp_path / "archive" / "data" / "written_curriculums" / "reader.md").exists()


def test_output_validator_checks_json_markdown_and_publication_metadata(tmp_path: Path) -> None:
    curriculum = tmp_path / "data" / "written_curriculums" / "reader"
    translations = tmp_path / "data" / "translated_curriculums" / "reader"
    curriculum.mkdir(parents=True)
    translations.mkdir(parents=True)
    (curriculum / "complete_curriculum.json").write_text(
        json.dumps(
            {
                "sections": {"Introduction": "A useful section."},
                "metadata": {"provider": "offline_fixture", "evidence_status": "offline"},
            }
        ),
        encoding="utf-8",
    )
    (curriculum / "broken.json").write_text("{not-json", encoding="utf-8")
    (translations / "spanish.md").write_text("# Traducción\n\nContenido", encoding="utf-8")

    report = validate_outputs(tmp_path)
    assert report["summary"]["file_count"] == 3
    assert report["summary"]["invalid_count"] == 1
    assert any(item["path"].endswith("spanish.md") for item in report["files"])

    publication_report = validate_outputs(tmp_path, publication=True)
    assert publication_report["summary"]["invalid_count"] == 2
    translation = next(
        item for item in publication_report["files"] if item["path"].endswith("spanish.md")
    )
    assert any("translation missing language" in error for error in translation["errors"])


def test_output_validator_checks_visualization_manifest_hashes(tmp_path: Path) -> None:
    curriculum = tmp_path / "data" / "written_curriculums" / "reader"
    visuals = tmp_path / "data" / "visualizations"
    curriculum.mkdir(parents=True)
    source = curriculum / "complete_curriculum_1.md"
    source.write_text("# Introduction\n\nA useful section.", encoding="utf-8")

    run_visualizations(str(tmp_path / "data" / "written_curriculums"), str(visuals))
    report = validate_outputs(tmp_path)
    manifest = next(
        item for item in report["files"] if item["path"].endswith("visualization_manifest.json")
    )
    assert manifest["valid"] is True
    chart = visuals / "charts" / "curriculum_metrics.png"
    chart.write_bytes(b"changed")
    invalid = validate_outputs(tmp_path)
    manifest = next(
        item for item in invalid["files"] if item["path"].endswith("visualization_manifest.json")
    )
    assert manifest["valid"] is False
    assert any("hash mismatch" in error for error in manifest["errors"])


def test_artifact_and_output_audits_reject_symlinked_entries(tmp_path: Path) -> None:
    data_root = tmp_path / "data" / "written_curriculums"
    data_root.mkdir(parents=True)
    external = tmp_path / "external"
    external.mkdir()
    (external / "escaped.md").write_text("outside", encoding="utf-8")
    link = data_root / "escaped"
    try:
        link.symlink_to(external, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    assert audit_artifacts(tmp_path)["summary"]["error_count"] >= 1
    report = validate_outputs(tmp_path)
    assert report["summary"]["invalid_count"] >= 1


def test_detailed_research_stage_preserves_outputs_and_input_hashes(
    tmp_path: Path, monkeypatch
) -> None:
    research_dir = tmp_path / "research"
    output_dir = tmp_path / "curricula"
    research_dir.mkdir()
    fep = tmp_path / "Synthetic_FEP-ActInf.md"
    fep.write_text("foundation", encoding="utf-8")
    source = research_dir / "reader_research_1.md"
    source.write_text("source", encoding="utf-8")

    output = output_dir / "reader" / "complete_curriculum_20260717_000000_000000.md"

    def fake_process(*_args, **_kwargs):
        output.parent.mkdir(parents=True)
        output.write_text("# Curriculum\n\nOffline output", encoding="utf-8")
        output.with_suffix(".json").write_text(
            json.dumps(
                {
                    "metadata": {
                        "provider": "offline_fixture",
                        "usage": {"prompt_tokens": 1, "completion_tokens": 2},
                    }
                }
            ),
            encoding="utf-8",
        )
        return output

    monkeypatch.setattr("src.pipeline.stages.process_research_file", fake_process)
    success, failed, items = process_research_directory_detailed(
        object(),
        research_dir,
        fep,
        output_dir,
        "curriculum",
    )
    assert (success, failed) == (1, 0)
    assert items[0]["output_paths"]
    assert items[0]["input_hashes"]["research"] == sha256_file(source)
    assert items[0]["usage"]["prompt_tokens"] == 1


def test_research_bundle_is_processed_once_with_json_metadata_preferred(tmp_path: Path) -> None:
    research_dir = tmp_path / "research"
    research_dir.mkdir()
    (research_dir / "domain_research_20260717.json").write_text("{}", encoding="utf-8")
    (research_dir / "domain_research_20260717.md").write_text("markdown", encoding="utf-8")
    assert get_research_files(research_dir) == [research_dir / "domain_research_20260717.json"]


def test_translation_stage_keeps_per_item_source_hashes_and_stable_ids(tmp_path: Path) -> None:
    curriculum_root = tmp_path / "curricula"
    for name, content in (
        ("alpha", "# Alpha\n\nUnique alpha curriculum content."),
        ("beta", "# Beta\n\nUnique beta curriculum content."),
    ):
        entity_dir = curriculum_root / name
        entity_dir.mkdir(parents=True)
        (entity_dir / "complete_curriculum_20260717_000000.md").write_text(
            content, encoding="utf-8"
        )

    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **_kwargs: SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(
                                content="Translated curriculum content with enough words."
                            )
                        )
                    ],
                    usage=SimpleNamespace(prompt_tokens=4, completion_tokens=6, total_tokens=10),
                )
            )
        )
    )
    success, failed, items = process_translations_detailed(
        client,
        str(curriculum_root),
        str(tmp_path / "translations"),
        ["Spanish"],
        max_concurrent=1,
        delay_seconds=0,
    )
    assert (success, failed) == (2, 0)
    by_id = {item["item_id"]: item for item in items}
    assert set(by_id) == {"alpha:spanish", "beta:spanish"}
    assert by_id["alpha:spanish"]["input_hashes"]["source"] == sha256_text(
        "# Alpha\n\nUnique alpha curriculum content."
    )
    assert by_id["beta:spanish"]["input_hashes"]["source"] == sha256_text(
        "# Beta\n\nUnique beta curriculum content."
    )


def test_offline_fixture_regeneration_is_manifested_and_reproducible(tmp_path: Path) -> None:
    first = regenerate(tmp_path / "fixtures", run_id="fixture-run")
    second = regenerate(tmp_path / "fixtures", run_id="fixture-run-2")
    assert first["ok"] is True
    assert second["ok"] is True
    assert len(first["stages"]) == 5
    assert all(stage["status"] == "succeeded" for stage in first["stages"].values())
    first_manifest = Path(first["manifest_path"])
    assert first_manifest.exists()
    assert len(json.loads(first_manifest.read_text(encoding="utf-8"))["artifacts"]) == 7
    assert all(
        artifact["metadata"].get("evidence_status") == "offline_fixture"
        for artifact in json.loads(first_manifest.read_text(encoding="utf-8"))["artifacts"]
    )


def test_run_history_summarizes_and_prunes_only_manifest_runs(tmp_path: Path) -> None:
    root = tmp_path / "runs"
    regenerate(root, run_id="one")
    regenerate(root, run_id="two")
    summaries = list_runs(root / ".runs")
    assert {summary.run_id for summary in summaries} == {"one", "two"}
    assert summarize_runs(summaries)["run_count"] == 2
    candidates = retention_candidates(summaries, keep=1)
    planned = prune_runs(candidates)
    assert planned and all(Path(path).exists() for path in planned)
    removed = prune_runs(candidates, apply=True)
    assert removed == planned
    assert all(not Path(path).exists() for path in removed)


def test_run_history_skips_malformed_manifests_and_validates_retention() -> None:
    with pytest.raises(ValueError, match="keep"):
        retention_candidates([], keep=-1)
    with pytest.raises(ValueError, match="older_than_days"):
        retention_candidates([], older_than_days=-1)


def test_research_stage_reports_missing_and_empty_inputs(tmp_path: Path) -> None:
    research_dir = tmp_path / "research"
    research_dir.mkdir()
    empty = research_dir / "empty_research_1.md"
    empty.write_text("", encoding="utf-8")
    unrelated = research_dir / "not_research_notes.md"
    unrelated.write_text("ignore", encoding="utf-8")
    missing_fep = tmp_path / "missing.md"
    success, failed, items = process_research_directory_detailed(
        object(),
        research_dir,
        missing_fep,
        tmp_path / "outputs",
        "domain",
    )
    assert success == 0 and failed == 1
    assert items[0]["item_id"] == "empty"
    with pytest.raises(ValueError, match="max_concurrent"):
        process_research_directory_detailed(
            object(), research_dir, missing_fep, tmp_path / "outputs", "domain", max_concurrent=0
        )


def test_gui_remote_binding_requires_explicit_authentication() -> None:
    from learning.curriculum_creation.generate_curriculum_gui import run_gui_server

    with pytest.raises(ValueError, match="allow-remote"):
        run_gui_server("0.0.0.0", 0, open_browser=False)
    with pytest.raises(ValueError, match="authentication token"):
        run_gui_server("0.0.0.0", 0, open_browser=False, allow_remote=True)


def test_orchestrator_planning_run_is_successful_without_visual_artifacts(tmp_path: Path) -> None:
    from learning.curriculum_creation.generate_custom_curriculum import (
        CurriculumConfig,
        CurriculumOrchestrator,
    )

    result = CurriculumOrchestrator(
        CurriculumConfig(
            target_domains=["biochemistry"],
            target_entities=["karl_friston"],
            target_languages=["Spanish"],
            custom_output_dir=tmp_path / "outputs",
            dry_run=True,
            run_id="planning-test",
        )
    ).run_complete_pipeline()
    assert result.ok
    visualization = next(stage for stage in result.stages if stage.name == "visualizations")
    assert visualization.status == StageStatus.SKIPPED


def test_cli_noninteractive_overrides_do_not_fall_into_interactive_mode(monkeypatch) -> None:
    import learning.curriculum_creation.generate_custom_curriculum as cli

    seen = {}

    class FakeOrchestrator:
        def __init__(self, config):
            seen["config"] = config

        def run_complete_pipeline(self):
            return PipelineResult(stages=[StageResult("test", required=False)])

    monkeypatch.setattr(cli, "CurriculumOrchestrator", FakeOrchestrator)
    monkeypatch.setattr(
        cli,
        "create_interactive_config",
        lambda: pytest.fail("non-interactive override entered interactive mode"),
    )
    assert cli.main(["--max-concurrent", "2"]) == 0
    assert seen["config"].max_concurrent_requests == 2


def test_cli_json_failure_is_bounded_and_machine_readable(monkeypatch, capsys) -> None:
    import learning.curriculum_creation.generate_custom_curriculum as cli

    class FailingOrchestrator:
        def __init__(self, _config):
            raise RuntimeError("Bearer sk-cli-secret")

    monkeypatch.setattr(cli, "CurriculumOrchestrator", FailingOrchestrator)
    assert cli.main(["--non-interactive", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert "sk-cli-secret" not in payload["errors"][0]


def test_gui_entrypoint_has_stable_argument_failure_code() -> None:
    from learning.curriculum_creation.generate_curriculum_gui import main

    with pytest.raises(SystemExit) as error:
        main(["--port", "0"])
    assert error.value.code == 2

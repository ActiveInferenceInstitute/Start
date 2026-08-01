from __future__ import annotations

import builtins
import json
import shutil
import threading
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest

import src.common.config as common_config
import src.common.io as common_io
import src.common.paths as common_paths
import src.config.catalog as catalog
import src.perplexity.clients as clients
import src.perplexity.domain as domain
import src.perplexity.entity as entity
import src.perplexity.translation as translation
import src.pipeline.parsers as parsers
import src.pipeline.quality as quality
import src.pipeline.schemas as response_schemas
import src.repos.clone_repo as clone_repo
import src.repos.cloning as cloning
import src.repos.manager as manager
import src.system.environment as environment
import src.system.reporting as reporting
import src.terminal.animations as animations
from src.config.schemas import (
    validate_domains_config,
    validate_entities_config,
    validate_languages_config,
)
from src.pipeline import (
    PipelineResult,
    PipelineRunner,
    RunConfig,
    StageItemResult,
    StageResult,
    StageSpec,
    StageStatus,
)
from src.pipeline.artifacts import (
    create_run_directory,
    read_json,
    safe_run_id,
    write_stage_checkpoint,
)
from src.pipeline.history import RunSummary, list_runs, prune_runs, retention_candidates
from src.pipeline.stages import process_research_directory_detailed, read_curriculum_inputs
from src.pipeline.usage import aggregate_usage, merge_usage, normalize_usage
from src.repos.clone_repo import _validate_destination
from src.repos.clone_repo import clone_repository as clone_with_gitpython


def test_config_loaders_cover_yaml_markdown_and_fail_closed_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(common_config, "data_root", lambda: tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    saved = common_config.save_yaml_config("selection", {"enabled": True})
    assert saved == config_dir / "selection.yaml"
    assert common_config.load_yaml_config("selection.yaml")["enabled"] is True

    saved.unlink()
    markdown = config_dir / "selection.md"
    markdown.write_text("---\nmode: review\n---\nNotes\n", encoding="utf-8")
    assert common_config.load_config("selection")["mode"] == "review"
    assert common_config.load_config("selection", prefer_yaml=False)["mode"] == "review"
    with pytest.raises(FileNotFoundError, match="No config file found"):
        common_config.load_config("missing")

    markdown.write_text("plain text\n", encoding="utf-8")
    with pytest.raises(ValueError, match="frontmatter"):
        common_config.load_markdown_config("selection")
    markdown.write_text("---\nmode: [\n---\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid YAML"):
        common_config.load_markdown_config("selection")
    markdown.write_text("---\n\n---\n", encoding="utf-8")
    with pytest.raises(ValueError, match="frontmatter is empty"):
        common_config.load_markdown_config("selection")
    with pytest.raises(ValueError, match="empty"):
        common_config.validate_config_data({}, "selection")


def test_paths_catalog_and_schema_reject_unsafe_or_ambiguous_values(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname='start'\n", encoding="utf-8")
    monkeypatch.delenv("START_REPO_ROOT", raising=False)
    assert common_paths.find_repo_root(root / "src" / "module.py") == root.resolve()
    assert common_paths.ensure_dir(tmp_path / "new").is_dir()
    assert common_paths.config_dir() == common_paths.data_root() / "config"
    with pytest.raises(RuntimeError, match="Unable to locate"):
        common_paths.find_repo_root(tmp_path / "not-a-project")

    monkeypatch.setattr(
        catalog,
        "load_config",
        lambda _name: {
            "domains": [{"name": "Bio", "description": "d", "category": "science"}],
            "entities": [{"name": "Reader", "description": "d", "category": "audience"}],
        },
    )
    assert catalog.load_domains_config()["domains"][0]["id"] == "bio"
    assert catalog.load_entities_config()["entities"][0]["id"] == "reader"

    with pytest.raises(ValueError, match="non-empty domains"):
        validate_domains_config({"domains": []})
    with pytest.raises(ValueError, match="must be a mapping"):
        validate_domains_config({"domains": ["science"]})
    with pytest.raises(ValueError, match="newlines"):
        validate_domains_config(
            {"domains": [{"name": "Bio\n", "description": "d", "category": "science"}]}
        )
    with pytest.raises(ValueError, match="priority"):
        validate_domains_config(
            {
                "domains": [
                    {"name": "Bio", "description": "d", "category": "science", "priority": "urgent"}
                ]
            }
        )
    with pytest.raises(ValueError, match="keywords"):
        validate_domains_config(
            {
                "domains": [
                    {"name": "Bio", "description": "d", "category": "science", "keywords": [""]}
                ]
            }
        )
    with pytest.raises(ValueError, match="ISO date"):
        validate_domains_config(
            {
                "domains": [
                    {
                        "name": "Bio",
                        "description": "d",
                        "category": "science",
                        "verification_date": "tomorrow",
                    }
                ]
            }
        )
    with pytest.raises(ValueError, match="non-empty entities"):
        validate_entities_config({"entities": []})
    with pytest.raises(ValueError, match="description"):
        validate_entities_config({"entities": [{"name": "Reader", "category": "audience"}]})
    with pytest.raises(ValueError, match="Language 0"):
        validate_languages_config({"target_languages": [42]})
    with pytest.raises(ValueError, match="non-empty name and script"):
        validate_languages_config(
            {"target_languages": ["English"], "script_mappings": {"English": ""}}
        )


def test_history_filters_old_runs_and_prunes_only_regular_manifest_dirs(tmp_path: Path) -> None:
    now = datetime.now(timezone.utc)
    old = RunSummary(
        "old",
        str(tmp_path / "old"),
        "failed",
        (now - timedelta(days=5)).isoformat(),
        None,
        0,
        1,
        {},
    )
    malformed = RunSummary(
        "bad-date", str(tmp_path / "bad"), "failed", "not-a-date", None, 0, 1, {}
    )
    current = RunSummary(
        "current",
        str(tmp_path / "current"),
        "succeeded",
        now.isoformat(),
        now.isoformat(),
        1,
        0,
        {},
    )
    (tmp_path / "old").mkdir()
    (tmp_path / "old" / "manifest.json").write_text("{}", encoding="utf-8")
    (tmp_path / "current").mkdir()
    (tmp_path / "current" / "manifest.json").write_text("{}", encoding="utf-8")
    assert [
        item.run_id
        for item in retention_candidates([current, old, malformed], keep=1, older_than_days=1)
    ] == ["old"]
    assert old.as_dict()["artifact_count"] == 0
    assert prune_runs([old], apply=False) == [str((tmp_path / "old").resolve())]
    assert prune_runs([old], apply=True) == [str((tmp_path / "old").resolve())]
    assert not (tmp_path / "old").exists()

    link = tmp_path / "linked-manifest"
    target = tmp_path / "target-manifest"
    target.mkdir()
    (target / "manifest.json").write_text("{}", encoding="utf-8")
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink support unavailable: {exc}")
    linked = RunSummary("link", str(link), "failed", None, None, 0, 0, {})
    assert prune_runs([linked], apply=True) == []
    assert list_runs(tmp_path / "missing") == []


def test_research_stage_covers_skip_cancel_failure_and_input_reading(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    research = tmp_path / "research"
    research.mkdir()
    foundation = tmp_path / "foundation.md"
    foundation.write_text("foundation", encoding="utf-8")
    empty = research / "empty_research_1.md"
    empty.write_text("", encoding="utf-8")
    source = research / "reader_research_1.md"
    source.write_text("source", encoding="utf-8")
    output = tmp_path / "outputs" / "reader" / "complete_curriculum_20260718_000000_000000.md"
    monkeypatch.setattr("src.pipeline.stages.process_research_file", lambda *_args, **_kwargs: None)
    success, failed, items = process_research_directory_detailed(
        object(), research, foundation, tmp_path / "outputs", "domain"
    )
    assert (success, failed) == (0, 2)
    assert {item["status"] for item in items} == {"failed"}

    output.parent.mkdir(parents=True)
    output.write_text("# Reader\n\nContent", encoding="utf-8")
    # Provide a verifiable sibling JSON so the fresh cache hit can be proven.
    from src.pipeline.provenance import file_input_record

    output.with_suffix(".json").write_text(
        json.dumps(
            {
                "metadata": {
                    "inputs": [
                        file_input_record(source, label="research"),
                        file_input_record(foundation, label="fep_actinf"),
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    existing_success, existing_failed, existing_items = process_research_directory_detailed(
        object(), research, foundation, tmp_path / "outputs", "domain", skip_existing=True
    )
    assert existing_success == 0 and existing_failed == 1
    assert (
        next(item for item in existing_items if item["item_id"] == "reader")["status"] == "skipped"
    )

    cancelled = threading.Event()
    cancelled.set()
    cancelled_success, cancelled_failed, cancelled_items = process_research_directory_detailed(
        object(), research, foundation, tmp_path / "other", "domain", cancellation_event=cancelled
    )
    assert cancelled_success == 0 and cancelled_failed == 2
    assert any("cancelled" in error for item in cancelled_items for error in item.get("errors", []))

    curricula = tmp_path / "curricula" / "reader"
    curricula.mkdir(parents=True)
    (curricula / "complete_curriculum_1.md").write_text("# Reader\ncontent", encoding="utf-8")
    (tmp_path / "curricula" / "empty").mkdir()
    (tmp_path / "curricula" / "empty" / "complete_curriculum_1.md").write_text(
        " \n", encoding="utf-8"
    )
    assert len(read_curriculum_inputs(tmp_path / "curricula")) == 1


def test_provider_failure_matrix_redacts_secrets_and_honors_cancellation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="timeout"):
        clients.ChatPolicy(model="x", timeout=float("nan"))
    with pytest.raises(ValueError, match="backoff"):
        clients.ChatPolicy(model="x", jitter_seconds=float("inf"))
    with pytest.raises(ValueError, match="token costs"):
        clients.ChatPolicy(model="x", input_cost_per_million=-1)
    with pytest.raises(ValueError, match="completion choice"):
        clients.validate_chat_response(SimpleNamespace(choices=[]))
    with pytest.raises(ValueError, match="shorter"):
        clients.validate_chat_response(
            SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="x"))]),
            min_content_length=2,
        )

    class RateLimitError(RuntimeError):
        status_code = 429

        def __init__(self, *args: object) -> None:
            super().__init__(*args)
            self.response = SimpleNamespace(headers={"Retry-After": "0"})

    calls = {"count": 0}

    def rate_limited(**_kwargs: object) -> object:
        calls["count"] += 1
        if calls["count"] == 1:
            raise RateLimitError("Bearer sk-provider-secret prompt text")
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="valid response"))],
            usage=SimpleNamespace(prompt_tokens=2, completion_tokens=3, total_tokens=5, cost=0.25),
        )

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=rate_limited)))
    result = clients.complete_chat_result(
        client,
        [{"role": "user", "content": "private prompt"}],
        clients.ChatPolicy(model="local", max_retries=2, backoff_seconds=0, jitter_seconds=0),
    )
    assert result.attempts == 2
    assert result.usage.as_dict()["actual_cost_usd"] == 0.25
    assert calls["count"] == 2

    with pytest.raises(clients.ProviderRequestError) as error:
        clients.complete_chat_result(
            SimpleNamespace(
                chat=SimpleNamespace(
                    completions=SimpleNamespace(
                        create=lambda **_kwargs: (_ for _ in ()).throw(ValueError("prompt secret"))
                    )
                )
            ),
            [{"role": "user", "content": "private prompt"}],
            clients.ChatPolicy(model="local", max_retries=1, backoff_seconds=0, jitter_seconds=0),
        )
    assert "prompt secret" not in str(error.value)

    cancelled = threading.Event()
    cancelled.set()
    with pytest.raises(clients.ProviderRequestError, match="cancelled"):
        clients.complete_chat_result(
            client,
            [{"role": "user", "content": "private prompt"}],
            clients.ChatPolicy(model="local"),
            cancellation_event=cancelled,
        )
    headers = SimpleNamespace(headers={"retry-after": format_datetime(datetime.now(timezone.utc))})
    assert clients._retry_after_seconds(SimpleNamespace(response=headers)) is not None
    assert (
        clients._retry_after_seconds(
            SimpleNamespace(response=SimpleNamespace(headers={"retry-after": "bad"}))
        )
        is None
    )


def test_translation_strict_schema_and_collision_safe_batch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    payload = json.dumps(
        {
            "schema_version": "1.0",
            "kind": "translation",
            "content": "# Heading\n\nContenido traducido con suficientes palabras.",
            "target_language": "Spanish",
            "citations": [],
        }
    )
    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **_kwargs: SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content=payload))],
                    usage=SimpleNamespace(prompt_tokens=2, completion_tokens=4, total_tokens=6),
                )
            )
        )
    )
    result = translation.translate_curriculum_result(
        client, "# Heading\n\nSource content", "Spanish", strict_schema=True
    )
    assert result.target_language == "Spanish"
    assert result.records[0]["evidence_status"] == "derived_translation"
    assert "Contenido" in result.content
    assert translation.split_content_into_chunks("", 10) == []
    with pytest.raises(ValueError, match="max_chunk"):
        translation.split_content_into_chunks("text", 0)
    assert all(len(chunk) <= 4 for chunk in translation.split_content_into_chunks("123456789", 4))

    fixed_time = datetime(2026, 1, 1, 12, 0, 0)
    monkeypatch.setattr(translation, "datetime", SimpleNamespace(now=lambda: fixed_time))
    first = translation.save_translation(
        str(tmp_path), "Display Entity", "Spanish", "Hola", entity_id="entity-id"
    )
    second = translation.save_translation(
        str(tmp_path), "Display Entity", "Spanish", "Hola", entity_id="entity-id"
    )
    assert first != second and second.stem.endswith("_1")

    curriculum = tmp_path / "curricula" / "entity"
    curriculum.mkdir(parents=True)
    (curriculum / "complete_curriculum_1.md").write_text(
        "# Heading\n\nSource content", encoding="utf-8"
    )
    monkeypatch.setattr(
        translation,
        "translate_curriculum_result",
        lambda *_args, **_kwargs: translation.TranslationResult(
            "# Heading\n\nTranslated content", "Spanish"
        ),
    )
    success, failed, items = translation.process_translations_detailed(
        client, str(tmp_path / "curricula"), str(tmp_path / "translations"), ["Spanish"]
    )
    assert (success, failed) == (1, 0)
    assert items[0]["status"] == "succeeded"
    skipped_success, skipped_failed, skipped = translation.process_translations_detailed(
        client, str(tmp_path / "curricula"), str(tmp_path / "translations"), ["Spanish"]
    )
    assert (skipped_success, skipped_failed) == (0, 0)
    assert skipped[0]["status"] == "skipped"


def test_strict_research_and_entity_payloads_record_provenance(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    research_payload = json.dumps(
        {
            "schema_version": "1.0",
            "kind": "research",
            "content": "Analysis https://example.com",
            "citations": ["https://example.com"],
        }
    )
    curriculum_payload = json.dumps(
        {
            "schema_version": "1.0",
            "kind": "curriculum",
            "sections": {"Overview": "Curriculum content"},
            "citations": [],
        }
    )
    responses = iter(
        [
            clients.CompletionResult(research_payload, "local", "perplexity", 1),
            clients.CompletionResult(curriculum_payload, "local", "perplexity", 1),
        ]
    )
    monkeypatch.setattr(domain, "chat_result", lambda *_args, **_kwargs: next(responses))
    foundation = tmp_path / "Synthetic_FEP-ActInf.md"
    foundation.write_text("foundation", encoding="utf-8")
    result = domain.analyze_domain(
        object(),
        "Domain content",
        str(foundation),
        str(tmp_path / "domain"),
        domain_name="Display Domain",
        strict_schema=True,
    )
    assert result.metadata["evidence_status"] == "synthetic_foundation"
    assert result.metadata["citations_analysis"] == ["https://example.com"]
    assert all(Path(path).exists() for path in result.output_paths)

    entity_payload = json.dumps(
        {
            "schema_version": "1.0",
            "kind": "research",
            "content": "Audience https://example.com",
            "citations": ["https://example.com"],
        }
    )
    monkeypatch.setattr(
        entity,
        "chat_result",
        lambda *_args, **_kwargs: clients.CompletionResult(
            entity_payload, "local", "perplexity", 1
        ),
    )
    entity_input = tmp_path / "audience.md"
    entity_input.write_text("Description: researchers", encoding="utf-8")
    result = entity.research_target_audience(
        object(), str(entity_input), str(foundation), str(tmp_path / "entity"), strict_schema=True
    )
    assert result.entity_description == "researchers"
    assert result.metadata["evidence_status"] == "synthetic_foundation"
    assert Path(result.output_paths[0]).is_file()


def test_gitpython_clone_boundary_and_provider_configuration_edges(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    linked_root = tmp_path / "linked"
    linked_target = tmp_path / "target"
    linked_target.mkdir()
    try:
        linked_root.symlink_to(linked_target, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink support unavailable: {exc}")
    with pytest.raises(ValueError, match="symlink"):
        _validate_destination(linked_root / "child")
    (tmp_path / "file").write_text("not a directory", encoding="utf-8")
    with pytest.raises(ValueError, match="not a directory"):
        _validate_destination(tmp_path / "file")
    nonempty = tmp_path / "nonempty"
    nonempty.mkdir()
    (nonempty / "data").write_text("data", encoding="utf-8")
    with pytest.raises(FileExistsError, match="not empty"):
        _validate_destination(nonempty)
    with pytest.raises(ValueError, match="Unsafe branch"):
        clone_with_gitpython("https://example.com/repo.git", tmp_path / "clone", branch="-bad")

    with pytest.raises(ValueError, match="API key"):
        clients.PerplexityConfig(api_key="")
    with pytest.raises(ValueError, match="base URL"):
        clients.OpenRouterConfig(api_key="configured", base_url="file:///tmp")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "configured-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "configured-key")
    assert clients.build_perplexity_client().base_url.host == "api.perplexity.ai"
    assert clients.build_openrouter_client().base_url.host == "openrouter.ai"


def test_environment_setup_and_health_checks_are_fail_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    with pytest.raises(ValueError, match="sync_command"):
        environment.setup_project_environment(tmp_path, sync_command=[])
    assert environment.setup_project_environment(tmp_path)[0] is False

    (tmp_path / "pyproject.toml").write_text("[project]\nname='start'\n", encoding="utf-8")
    monkeypatch.setattr(environment, "run_uv_sync", lambda **_kwargs: (False, "sync failed"))
    monkeypatch.setattr(environment, "load_project_env", lambda *_args: None)
    monkeypatch.setattr(environment, "validate_environment", lambda _root: (False, ["missing key"]))
    ok, messages = environment.setup_project_environment(tmp_path, sync_command=["uv", "sync"])
    assert ok is False
    assert any("synchronization failed" in message for message in messages)
    assert (tmp_path / ".env").is_file()

    monkeypatch.undo()
    success, output = environment.run_uv_sync(
        tmp_path, command=["/usr/bin/printf", "sync-ok"], timeout=1
    )
    assert success and output == "sync-ok"
    monkeypatch.setattr(
        environment.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            environment.subprocess.TimeoutExpired("sync", 1)
        ),
    )
    assert environment.run_uv_sync(tmp_path)[0] is False

    (tmp_path / "src").mkdir()
    (tmp_path / "data" / "config").mkdir(parents=True)
    (tmp_path / "data" / "prompts").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "data" / "config" / "domains.yaml").write_text("domains: []", encoding="utf-8")
    (tmp_path / "data" / "config" / "entities.yaml").write_text("entities: []", encoding="utf-8")
    (tmp_path / "data" / "config" / "languages.yaml").write_text(
        "target_languages: []", encoding="utf-8"
    )
    (tmp_path / "src" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "data" / "domain_research").mkdir(parents=True)
    (tmp_path / "data" / "domain_research" / "Synthetic_FEP-ActInf.md").write_text(
        "synthetic", encoding="utf-8"
    )
    monkeypatch.setattr(environment, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        "src.system.dependencies.run_comprehensive_dependency_check",
        lambda: SimpleNamespace(all_required_available=True, missing_required=[]),
    )
    monkeypatch.setattr(
        "src.system.dependencies.validate_api_keys",
        lambda: {"perplexity": True, "openrouter": True},
    )
    healthy, details = environment.run_health_check()
    assert healthy is True
    assert details["dependencies"]["healthy"] is True
    assert details["file_system"]["healthy"] is True


def test_reporting_uses_bounded_commands_and_structured_requirements(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert reporting.run_command_safely(["/usr/bin/printf", "ok"])[0] is True
    monkeypatch.setattr(
        reporting.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            reporting.subprocess.TimeoutExpired("command", 1)
        ),
    )
    assert reporting.run_command_safely(["command"])[2] == "Command timed out"

    monkeypatch.setattr(reporting.paths, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(reporting, "get_basic_system_info", lambda: {"hostname": "host"})
    monkeypatch.setattr(
        reporting, "get_python_environment_info", lambda: {"python_version": "3.12"}
    )
    monkeypatch.setattr(reporting, "get_memory_info", lambda: {"total_gb": 8.0})
    monkeypatch.setattr(
        reporting,
        "get_disk_usage",
        lambda *_args: {
            "/": {"total_gb": 10.0, "used_gb": 2.0, "free_gb": 8.0, "percent_used": 20.0}
        },
    )
    monkeypatch.setattr(
        reporting,
        "get_network_info",
        lambda: {"ip_addresses": ["127.0.0.1"], "internet_connected": True, "errors": []},
    )
    monkeypatch.setattr(reporting, "get_git_info", lambda: {})
    monkeypatch.setattr(reporting, "get_cpu_info", lambda: {"logical_cores": 4})
    report = reporting.generate_system_report()
    assert report.hostname == "host"
    assert "DISK USAGE" not in reporting.format_system_report(report, detailed=False)

    monkeypatch.setattr(reporting, "get_memory_info", lambda: {"total_gb": 0.5})
    monkeypatch.setattr(reporting, "get_disk_usage", lambda *_args: {})
    monkeypatch.setattr(reporting, "get_network_info", lambda: {"internet_connected": False})
    requirements = reporting.check_system_requirements()
    assert requirements["sufficient_memory"] is False
    assert requirements["sufficient_disk_space"] is False
    assert requirements["internet_connected"] is False


def test_animation_effects_cover_rendering_and_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(animations, "get_terminal_size", lambda: (5, 10))
    monkeypatch.setattr(animations.random, "random", lambda: 0.0)
    monkeypatch.setattr(animations.random, "choice", lambda value: value[0])
    monkeypatch.setattr(animations.random, "randint", lambda _low, high: high)
    rain = animations.MatrixRain(duration=0, density=1.0)
    rain._update_drops()
    rain.columns[0] = [
        {"char": "a", "row": 0, "age": 0, "max_age": 10},
        {"char": "b", "row": 1, "age": 3, "max_age": 10},
        {"char": "c", "row": 2, "age": 5, "max_age": 10},
    ]
    assert "a" in rain._render_frame()
    assert list(rain.animate())[-1]
    assert "text" not in animations.matrix_banner("a very long banner", width=12)

    monkeypatch.setattr(animations.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        animations.LoadingSpinner, "animate", lambda _self, _duration: iter(["frame"])
    )
    assert any("SYSTEM READY" in frame for frame in animations.boot_sequence(["step"], delay=0))
    monkeypatch.setattr(animations.time, "time", iter([0.0, 0.0, 1.0]).__next__)
    assert len(list(animations.dramatic_pause("wait", duration=0.5))) == 2

    monkeypatch.setattr(animations, "typewriter_effect", lambda *_args, **_kwargs: iter(["a"]))
    monkeypatch.setattr(animations, "glitch_effect", lambda *_args, **_kwargs: iter(["b"]))
    monkeypatch.setattr(animations.MatrixRain, "animate", lambda _self: iter(["c"]))
    animations.print_animated("x", "typewriter")
    animations.print_animated("x", "glitch")
    animations.print_animated("x", "matrix", duration=0)


def test_repository_error_and_retention_paths_are_safe(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert cloning.get_cloned_repositories(tmp_path / "missing") == []
    clone_root = tmp_path / "clones"
    clone_root.mkdir()
    valid = clone_root / "valid"
    valid.mkdir()
    (valid / ".git").mkdir()
    incomplete = clone_root / "incomplete"
    incomplete.mkdir()
    linked = clone_root / "linked"
    linked_target = tmp_path / "linked-target"
    linked_target.mkdir()
    try:
        linked.symlink_to(linked_target, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink support unavailable: {exc}")
    assert cloning.get_cloned_repositories(clone_root) == [("valid", valid)]
    assert cloning.cleanup_failed_clones(clone_root) == ["incomplete"]

    assert cloning.validate_repository_url("https://example.invalid/repo") is False
    monkeypatch.setattr(
        cloning.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="refs", stderr=""),
    )
    assert cloning.validate_repository_url("https://example.invalid/repo") is True
    with pytest.raises(ValueError, match="max_concurrent"):
        cloning.clone_multiple_repositories([], max_concurrent=0, base_dir=clone_root)

    repository = tmp_path / "repository"
    (repository / ".git").mkdir(parents=True)
    # A real repository always ships .git/config; provide a safe one so the
    # update/status paths reach the git commands rather than the safety guard.
    (repository / ".git" / "config").write_text(
        "[core]\n\trepositoryformatversion = 0\n", encoding="utf-8"
    )
    responses = iter(
        [
            # update 1: branch fails
            SimpleNamespace(returncode=1, stdout="", stderr="branch failed"),
            # update 2: detached head
            SimpleNamespace(returncode=0, stdout="", stderr=""),
            # update 3: branch, fetch, merge all succeed
            SimpleNamespace(returncode=0, stdout="main", stderr=""),
            SimpleNamespace(returncode=0, stdout="", stderr=""),
            SimpleNamespace(returncode=0, stdout="", stderr=""),
            # update 4: branch ok, fetch ok, merge fails
            SimpleNamespace(returncode=0, stdout="main", stderr=""),
            SimpleNamespace(returncode=0, stdout="", stderr=""),
            SimpleNamespace(returncode=1, stdout="", stderr="merge failed"),
        ]
    )
    monkeypatch.setattr(cloning.subprocess, "run", lambda *_args, **_kwargs: next(responses))
    assert cloning.update_repository(repository) == (False, "Could not determine current branch")
    assert cloning.update_repository(repository) == (
        False,
        "Repository is detached; refusing to select an update branch",
    )
    assert cloning.update_repository(repository) == (True, "Successfully updated repository")
    assert cloning.update_repository(repository) == (False, "Failed to update: merge failed")
    monkeypatch.setattr(
        cloning.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            cloning.subprocess.TimeoutExpired("git", 1)
        ),
    )
    assert cloning.update_repository(repository)[1] == "Update operation timed out"

    monkeypatch.setattr(
        cloning.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("git unavailable")),
    )
    status = cloning.get_repository_status(repository)
    assert status["is_git_repo"] is True
    assert status["errors"]
    assert cloning.get_repository_status(linked)["errors"]

    monkeypatch.setattr(
        cloning,
        "clone_multiple_repositories",
        lambda names, **_kwargs: [cloning.CloneResult(name, True) for name in names],
    )
    category_results = cloning.clone_all_repositories(
        category="active_inference", base_dir=clone_root
    )
    assert category_results and all(result.success for result in category_results)


def test_repository_manager_handles_relative_paths_and_formatting(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(manager, "get_predefined_repositories", lambda: {})
    relative = manager.RepositoryManager("relative-clones")
    assert relative.base_dir.is_absolute()
    assert manager.create_repository_manager(tmp_path).base_dir == tmp_path.resolve()
    assert manager.create_repository_manager().base_dir.is_absolute()

    monkeypatch.setattr(manager, "get_cloned_repositories", lambda _root: [("one", tmp_path)])
    monkeypatch.setattr(manager, "get_repository_status", lambda _path: {"size_mb": 1.0})
    monkeypatch.setattr(manager, "update_repository", lambda _path: (True, "updated"))
    managed = manager.RepositoryManager(tmp_path / "managed")
    assert managed.list_cloned_repositories()["one"]["size_mb"] == 1.0
    assert managed.update_all_repositories() == [("one", True, "updated")]
    assert managed.get_repository_status("missing") is None

    monkeypatch.setattr(shutil, "which", lambda _name: None)
    monkeypatch.setattr(shutil, "disk_usage", lambda _path: (10, 9, 0))
    valid, issues = managed.validate_setup()
    assert valid is False
    assert any("Git" in issue or "disk" in issue for issue in issues)
    assert "FAILED CLONES" in manager.format_clone_results(
        [manager.CloneResult("bad", False, error_message="failed")]
    )
    status_text = manager.format_repository_status(
        {
            "one": {
                "path": str(tmp_path),
                "is_git_repo": True,
                "branch": None,
                "last_commit": "commit message",
                "uncommitted_changes": False,
                "size_mb": 1.0,
            }
        }
    )
    assert "unknown" in status_text and "commit message" in status_text


def test_reporting_fallbacks_cover_memory_and_git_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_import = builtins.__import__

    def no_psutil(name: str, *args: object, **kwargs: object):
        if name == "psutil":
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_psutil)
    monkeypatch.setattr(reporting.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        builtins,
        "open",
        lambda *_args, **_kwargs: StringIO("MemTotal:       4096 kB\nMemAvailable:   2048 kB\n"),
    )
    memory = reporting.get_memory_info()
    assert memory["total_gb"] > memory["available_gb"]
    monkeypatch.setattr(builtins, "open", lambda *_args, **_kwargs: StringIO("empty"))
    assert reporting.get_memory_info()["total_gb"] == 0.0

    monkeypatch.setattr(reporting.paths, "repo_root", lambda: Path("/not-a-repository"))
    assert reporting.get_git_info() == {"status": "Not a git repository"}
    monkeypatch.setattr(reporting.paths, "repo_root", lambda: Path("/"))
    monkeypatch.setattr(reporting.Path, "exists", lambda _path: True)
    monkeypatch.setattr(
        reporting.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("git failed")),
    )
    assert reporting.get_git_info()["status"] == "Error accessing git information"


def test_response_contracts_and_quality_gates_refuse_malformed_content(
    tmp_path: Path,
) -> None:
    research = response_schemas.parse_structured_response(
        "```json\n"
        '{"schema_version":"1.0","kind":"research","content":"evidence",'
        '"citations":["https://example.com","https://example.com"]}\n```',
        "research",
    )
    assert research.as_dict()["citations"] == ["https://example.com"]
    curriculum = response_schemas.parse_structured_response(
        json.dumps(
            {
                "schema_version": "1.0",
                "kind": "curriculum",
                "sections": {"Overview": "content"},
                "citations": [],
            }
        ),
        "curriculum",
    )
    assert response_schemas.payload_markdown(curriculum).startswith("# Overview")
    translation_payload = response_schemas.parse_structured_response(
        json.dumps(
            {
                "schema_version": "1.0",
                "kind": "translation",
                "content": "translated",
                "target_language": "Spanish",
                "citations": [],
            }
        ),
        "translation",
    )
    assert translation_payload.as_dict()["target_language"] == "Spanish"

    invalid_payloads = [
        ("not json", "research", "not valid JSON"),
        ("[]", "research", "JSON object"),
        ("{}", "unknown", "unsupported"),
        (json.dumps({"schema_version": "2.0", "kind": "research"}), "research", "schema_version"),
        (
            json.dumps({"schema_version": "1.0", "kind": "research", "content": "x"}),
            "research",
            "citation",
        ),
        (
            json.dumps(
                {"schema_version": "1.0", "kind": "curriculum", "sections": {}, "citations": []}
            ),
            "curriculum",
            "sections",
        ),
        (
            json.dumps(
                {"schema_version": "1.0", "kind": "translation", "content": "x", "citations": []}
            ),
            "translation",
            "target_language",
        ),
    ]
    for raw, kind, message in invalid_payloads:
        with pytest.raises((ValueError, response_schemas.StructuredPayloadError), match=message):
            response_schemas.parse_structured_response(raw, kind)

    assert not quality.validate_generated_text("", min_words=1).valid
    assert not quality.validate_generated_text("one two three", max_words=2).valid
    assert not quality.validate_generated_text("one two", require_citations=True).valid
    repetitive = quality.validate_generated_text("same. same. same. same. same. same.")
    assert repetitive.warnings
    assert not quality.validate_translation("# A\nsource", "translated", "Arabic").valid
    assert quality.validate_translation("# A\nsource", "# A\ntranslated", "Spanish").valid
    assert not quality.validate_translation(
        "# A\nsource\n# B\nsource", "# A\ntranslated", "Spanish", require_parity=True
    ).valid

    bad_visual = tmp_path / "bad.txt"
    bad_visual.write_text("x", encoding="utf-8")
    empty_json = tmp_path / "empty.json"
    empty_json.write_text("", encoding="utf-8")
    result = parsers.parse_visualization_response(
        [str(bad_visual), str(empty_json)], require_manifest=True
    )
    assert not result.quality.valid


def test_pipeline_contract_validation_and_handler_failures_are_recorded(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="unique"):
        PipelineRunner(
            [StageSpec("same"), StageSpec("same")], work_root=tmp_path, run_id="duplicate"
        )
    with pytest.raises(ValueError, match="unknown dependencies"):
        PipelineRunner(
            [StageSpec("child", depends_on=("missing",))],
            work_root=tmp_path,
            run_id="unknown",
        )

    wrong_type = PipelineRunner([StageSpec("wrong")], work_root=tmp_path, run_id="wrong-type")
    result = wrong_type.run({"wrong": lambda _context: "not a stage"})
    assert not result.ok and "TypeError" in result.errors[0]

    wrong_name = PipelineRunner([StageSpec("expected")], work_root=tmp_path, run_id="wrong-name")
    result = wrong_name.run({"expected": lambda _context: StageResult("other")})
    assert not result.ok and "expected" in result.errors[0]

    raised = PipelineRunner([StageSpec("raised")], work_root=tmp_path, run_id="raised")
    result = raised.run({"raised": lambda _context: (_ for _ in ()).throw(RuntimeError("boom"))})
    assert not result.ok and "RuntimeError" in result.errors[0]

    stopped = PipelineRunner(
        [StageSpec("first"), StageSpec("independent")], work_root=tmp_path, run_id="stopped"
    )
    result = stopped.run(
        {
            "first": lambda _context: StageResult("first", errors=["failed"]),
            "independent": lambda _context: StageResult("independent"),
        },
        continue_independent=False,
    )
    # The not-yet-run required stage is recorded as blocked so the run status
    # reflects the work that was skipped by the early stop.
    assert [stage.name for stage in result.stages] == ["first", "independent"]
    assert result.stages[-1].ok is False
    assert not result.ok


def test_provider_configuration_and_limiter_contract_edges() -> None:
    with pytest.raises(ValueError, match="Model name"):
        clients.ChatPolicy(model=" ")
    with pytest.raises(ValueError, match="delay"):
        clients.ChatPolicy(model="x", delay_seconds=-1)
    with pytest.raises(ValueError, match="backoff"):
        clients.ChatPolicy(model="x", max_backoff_seconds=-1)
    with pytest.raises(ValueError, match="min_content"):
        clients.ChatPolicy(model="x", min_content_length=0)
    with pytest.raises(ValueError, match="messages"):
        clients.complete_chat_result(
            SimpleNamespace(
                chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_kwargs: None))
            ),
            [{"role": "user", "content": ""}],
            clients.ChatPolicy(model="x"),
        )
    with pytest.raises(clients.ProviderOfflineError):
        clients.complete_chat_result(
            SimpleNamespace(
                chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_kwargs: None))
            ),
            [{"role": "user", "content": "content"}],
            clients.ChatPolicy(model="x"),
            offline=True,
        )
    limiter = clients.RequestLimiter(max_concurrent=1, min_interval_seconds=0)
    cancelled = threading.Event()
    cancelled.set()
    with pytest.raises(clients.ProviderRequestError, match="cancelled"):
        limiter.acquire(cancelled)
    assert clients.CompletionUsage(actual_cost_usd=None).as_dict()["actual_cost_usd"] == 0.0
    assert clients._retry_after_seconds(SimpleNamespace(response=None)) is None


def test_common_io_edges_preserve_atomic_and_path_boundaries(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert common_io.safe_name("  A path/name!  ") == "A_path_name"
    assert common_io.safe_name("...") == "item"
    assert common_io.path_within(tmp_path / "child", tmp_path)
    assert not common_io.path_within(tmp_path.parent, tmp_path)

    output = tmp_path / "output.txt"
    output.write_text("first", encoding="utf-8")
    assert common_io.next_available_path(output).name == "output_1.txt"
    with pytest.raises(ValueError, match="stem"):
        common_io.next_available_bundle(tmp_path, "", ["json"])
    with pytest.raises(ValueError, match="suffixes"):
        common_io.next_available_bundle(tmp_path, "bundle", [])
    output.with_name("bundle.json").write_text("existing", encoding="utf-8")
    assert common_io.next_available_bundle(tmp_path, "bundle", ["json"])[0].name == "bundle_1.json"
    with pytest.raises(TypeError, match="content"):
        common_io.write_text(tmp_path / "bad", 1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Expected a directory"):
        common_io.ensure_directory(output)

    with pytest.raises(ValueError, match="files cannot"):
        common_io.write_text_bundle({})
    with pytest.raises(ValueError, match="duplicate"):
        common_io.write_text_bundle({tmp_path / "same": "a", str(tmp_path / "same"): "b"})
    with pytest.raises(TypeError, match="contents"):
        common_io.write_text_bundle({tmp_path / "typed": 1})  # type: ignore[dict-item]
    output_json = tmp_path / "object.json"
    common_io.write_json(output_json, {"ok": True})
    assert common_io.read_json(output_json)["ok"] is True
    output_json.write_text("[]", encoding="utf-8")
    assert common_io.read_json(output_json) == []
    assert common_io.list_files(tmp_path / "missing") == []
    assert common_io.list_files(tmp_path, ["*.txt"])

    key_file = tmp_path / "keys.env"
    key_file.write_text("A=one\ncomment\nB=two=parts\n", encoding="utf-8")
    assert common_io.load_key_from_file(key_file, "B") == "two=parts"
    with pytest.raises(ValueError, match="not found"):
        common_io.load_key_from_file(key_file, "C")
    with pytest.raises(FileNotFoundError, match="Key file"):
        common_io.load_key_from_file(tmp_path / "missing.env", "A")
    domain_dir = tmp_path / "domains"
    domain_dir.mkdir()
    (domain_dir / "one.md").write_text("one", encoding="utf-8")
    (domain_dir / "skip.md").write_text("skip", encoding="utf-8")
    assert [path.stem for path in common_io.list_domain_markdown_files(domain_dir, ["skip"])] == [
        "one"
    ]


def test_provider_adapter_wrappers_and_configuration_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    usage = clients.CompletionUsage(prompt_tokens=1, completion_tokens=2)
    completion = clients.CompletionResult("text", "model", "provider", 1, usage)
    assert completion.as_dict()["usage"]["total_tokens"] == 0
    with pytest.raises(ValueError, match="max_concurrent"):
        clients.RequestLimiter(max_concurrent=0)
    with pytest.raises(ValueError, match="min_interval"):
        clients.RequestLimiter(min_interval_seconds=-1)
    assert (
        clients._retry_after_seconds(
            SimpleNamespace(response=SimpleNamespace(headers={"retry-after": "2"}))
        )
        == 2.0
    )
    assert (
        clients._retry_after_seconds(
            SimpleNamespace(response=SimpleNamespace(headers={"retry-after": "bad"}))
        )
        is None
    )

    with pytest.raises(ValueError, match="client"):
        clients.complete_chat_result(
            object(), [{"role": "user", "content": "text"}], clients.ChatPolicy(model="x")
        )
    with pytest.raises(ValueError, match="messages"):
        clients.complete_chat_result(
            SimpleNamespace(
                chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_kwargs: None))
            ),
            [{"role": "user"}],
            clients.ChatPolicy(model="x"),
        )
    response_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **_kwargs: SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content="text"))]
                )
            )
        )
    )
    adapter = clients.ProviderAdapter(
        response_client, provider="local", policy=clients.ChatPolicy(model="x")
    )
    assert (
        clients.complete_chat_result(
            response_client, [{"role": "user", "content": "text"}], clients.ChatPolicy(model="x")
        ).content
        == "text"
    )
    assert adapter.complete([{"role": "user", "content": "text"}]).content == "text"
    with pytest.raises(ValueError, match="provider"):
        clients.ProviderAdapter(response_client, provider=" ", policy=clients.ChatPolicy(model="x"))

    monkeypatch.setenv("PERPLEXITY_API_KEY", "short")
    monkeypatch.setenv("OPENROUTER_API_KEY", "short")
    with pytest.raises(ValueError, match="too short"):
        clients.build_perplexity_client()
    with pytest.raises(ValueError, match="too short"):
        clients.build_openrouter_client()
    monkeypatch.setattr(
        clients, "OpenAI", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("client error"))
    )
    with pytest.raises(EnvironmentError, match="Failed to create"):
        clients.build_perplexity_client(clients.PerplexityConfig(api_key="configured-key"))
    with pytest.raises(EnvironmentError, match="Failed to create"):
        clients.build_openrouter_client(clients.OpenRouterConfig(api_key="configured-key"))


def test_pipeline_contracts_usage_and_run_artifacts_are_serializable(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="stage name"):
        StageSpec(" ")
    with pytest.raises(ValueError, match="itself"):
        StageSpec("stage", depends_on=("stage",))
    with pytest.raises(ValueError, match="run_id"):
        RunConfig("", str(tmp_path))
    with pytest.raises(ValueError, match="work_dir"):
        RunConfig("run", "")
    with pytest.raises(ValueError, match="max_concurrent"):
        RunConfig("run", str(tmp_path), max_concurrent_requests=0)
    with pytest.raises(ValueError, match="budget"):
        RunConfig("run", str(tmp_path), budget_limit_usd=float("inf"))
    with pytest.raises(ValueError, match="allowed_output"):
        RunConfig("run", str(tmp_path), allowed_output_roots=("",))

    item = StageItemResult("ok", StageStatus.SUCCEEDED, output_paths=["out"], usage={"requests": 1})
    skipped = StageItemResult("skip", StageStatus.SKIPPED)
    failed = StageItemResult("bad", StageStatus.FAILED, errors=["broken"])
    stage = StageResult("stage", items={"ok": item, "skip": skipped, "bad": failed})
    # A stage containing a failed item must not report ok; the pipeline must
    # surface the partial failure instead of treating the run as green.
    assert not stage.ok and stage.attempted == 3
    assert set(stage.successes) == {"ok"}
    assert stage.skips == ["skip"]
    assert stage.failures == {"bad": "broken"}
    result = PipelineResult(stages=[stage], run_id="run")
    assert not bool(result)
    assert result.as_dict()["stages"]["stage"]["success"] == 1

    assert normalize_usage({"prompt_tokens": True, "completion_tokens": "2"})["prompt_tokens"] == 0
    assert normalize_usage(None)["requests"] == 0
    assert aggregate_usage({"first": {"requests": 1}, "second": {"requests": 2}})["requests"] == 3
    assert aggregate_usage(None)["requests"] == 0
    assert merge_usage({"requests": 1}, None)["requests"] == 1

    with pytest.raises(ValueError, match="run_id"):
        safe_run_id("...")
    run_dir = create_run_directory(tmp_path / "runs", "a run")
    checkpoint = write_stage_checkpoint(run_dir, "stage/name", {"ok": True})
    assert read_json(checkpoint)["ok"] is True
    with pytest.raises(ValueError, match="object"):
        checkpoint.write_text("[]", encoding="utf-8")
        read_json(checkpoint)
    run_root = tmp_path / "linked-runs"
    run_target = tmp_path / "run-target"
    run_target.mkdir()
    try:
        run_root.symlink_to(run_target, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink support unavailable: {exc}")
    with pytest.raises(ValueError, match="symlink"):
        create_run_directory(run_root, "run")
    regular_root = tmp_path / "regular-runs"
    regular_root.mkdir()
    run_link = regular_root / "linked-run"
    try:
        run_link.symlink_to(run_target, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink support unavailable: {exc}")
    with pytest.raises(ValueError, match="run directory"):
        create_run_directory(regular_root, "linked-run")


def test_gitpython_wrapper_covers_options_and_cleanup_failures(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    destination = tmp_path / "clone"
    calls: dict[str, object] = {}

    def clone_from(url: str, target: Path, **kwargs: object) -> object:
        calls.update({"url": url, "target": target, "kwargs": kwargs})
        target.mkdir()
        return SimpleNamespace(working_tree_dir=str(target))

    monkeypatch.setattr(clone_repo.Repo, "clone_from", clone_from)
    assert (
        clone_repo.clone_repository(
            "https://example.com/repo.git", destination, branch="main", shallow=True
        )
        == destination
    )
    assert calls["kwargs"] == {"branch": "main", "depth": 1, "single_branch": True}

    no_tree = tmp_path / "no-tree"

    def no_working_tree(_url: str, target: Path, **_kwargs: object) -> object:
        target.mkdir()
        return SimpleNamespace(working_tree_dir=None)

    monkeypatch.setattr(clone_repo.Repo, "clone_from", no_working_tree)
    with pytest.raises(RuntimeError, match="working tree"):
        clone_repo.clone_repository("https://example.com/repo.git", no_tree)
    assert not no_tree.exists()

    failed = tmp_path / "failed"

    def failing_clone(_url: str, target: Path, **_kwargs: object) -> object:
        target.mkdir()
        raise RuntimeError("clone failed")

    monkeypatch.setattr(clone_repo.Repo, "clone_from", failing_clone)
    with pytest.raises(RuntimeError, match="clone failed"):
        clone_repo.clone_repository("https://example.com/repo.git", failed)
    assert not failed.exists()
    assert clone_repo.main(["--url", "not-safe", "--dest", str(tmp_path / "bad")]) == 1
    assert clone_repo.parse_args(
        ["--url", "https://example.com/repo.git", "--dest", str(tmp_path / "args"), "--shallow"]
    ).shallow


def test_environment_command_and_health_error_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert (
        environment.run_uv_sync(tmp_path, command=[])[1]
        == "command must contain at least one executable"
    )
    assert (
        environment.run_uv_sync(tmp_path, command=["true"], timeout=0)[1]
        == "timeout must be greater than zero"
    )
    monkeypatch.setattr(
        environment.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("sync error")),
    )
    assert environment.run_uv_sync(tmp_path, command=["true"])[1] == "sync error"

    root = tmp_path / "project"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='start'\n", encoding="utf-8")
    monkeypatch.setattr(environment, "run_uv_sync", lambda **_kwargs: (True, "synced"))
    monkeypatch.setattr(environment, "load_project_env", lambda *_args: None)
    monkeypatch.setattr(environment, "validate_environment", lambda _root: (True, ["valid"]))
    monkeypatch.setattr(environment.shutil, "which", lambda _name: "/usr/local/bin/uv")
    ok, messages = environment.setup_project_environment(root)
    assert ok and "uv found" in " ".join(messages)

    monkeypatch.setattr(
        "src.system.dependencies.run_comprehensive_dependency_check",
        lambda: (_ for _ in ()).throw(RuntimeError("dependency error")),
    )
    monkeypatch.setattr(environment, "repo_root", lambda: root)
    (root / "src").mkdir()
    (root / "data" / "config").mkdir(parents=True)
    (root / "data" / "prompts").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src" / "__init__.py").write_text("", encoding="utf-8")
    (root / "data" / "domain_research").mkdir(parents=True)
    (root / "data" / "domain_research" / "Synthetic_FEP-ActInf.md").write_text(
        "foundation", encoding="utf-8"
    )
    for name in ("domains.yaml", "entities.yaml", "languages.yaml"):
        (root / "data" / "config" / name).write_text("{}", encoding="utf-8")
    unhealthy, details = environment.run_health_check()
    assert unhealthy is False
    assert "error" in details["dependencies"]


def test_environment_validation_reports_old_python_missing_keys_and_existing_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='start'\n", encoding="utf-8")
    (tmp_path / ".env").write_text("existing", encoding="utf-8")
    monkeypatch.setattr(environment, "run_uv_sync", lambda **_kwargs: (True, "synced"))
    monkeypatch.setattr(environment, "load_project_env", lambda *_args: None)
    monkeypatch.setattr(environment.shutil, "which", lambda _name: "/usr/local/bin/uv")
    ok, messages = environment.setup_project_environment(tmp_path)
    assert ok is False
    assert "file exists" in " ".join(messages)

    monkeypatch.setattr(environment.sys, "version_info", (3, 9, 0))
    monkeypatch.setattr(environment.sys, "base_prefix", environment.sys.prefix)
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    valid, messages = environment.validate_environment(tmp_path)
    assert valid is False
    joined = " ".join(messages)
    assert "3.10+ required" in joined
    assert "No virtual environment" in joined
    assert "key missing" in joined


def test_config_loader_rejects_empty_and_non_mapping_documents(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(common_config, "data_root", lambda: tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "empty.yaml").write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        common_config.load_yaml_config("empty")
    (config_dir / "list.yaml").write_text("- item\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        common_config.load_yaml_config("list")
    (config_dir / "front.md").write_text("---\n- item\n---\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        common_config.load_markdown_config("front")
    (config_dir / "open.md").write_text("---\nmode: review\n", encoding="utf-8")
    with pytest.raises(ValueError, match="closing"):
        common_config.load_markdown_config("open")
    with pytest.raises(ValueError, match="string"):
        common_config.validate_config_data({1: "value"}, "config")  # type: ignore[dict-item]
    (config_dir / "broken.yaml").write_text("key: [\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Failed to load"):
        common_config.load_config("broken")

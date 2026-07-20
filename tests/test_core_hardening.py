from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from fixtures import LocalCompletionServer

from src.common.config import load_config, validate_config_data
from src.common.io import (
    list_domain_markdown_files,
    list_files,
    load_key_from_file,
    next_available_bundle,
    next_available_path,
    path_within,
    safe_name,
    write_text_bundle,
)
from src.common.paths import find_repo_root
from src.perplexity.clients import ChatPolicy, _validate_config, validate_chat_response
from src.perplexity.curriculum import (
    _load_research_content,
    extract_sections,
    process_research_file,
    validate_curriculum_content,
)
from src.perplexity.translation import (
    process_translations_detailed,
    split_content_into_chunks,
    translate_curriculum_result,
)
from src.pipeline import PipelineResult, StageResult


def test_io_safety_and_file_helpers(tmp_path) -> None:
    assert safe_name("../A section: one") == "A_section_one"
    assert safe_name("") == "item"
    root = tmp_path / "root"
    child = root / "child"
    child.mkdir(parents=True)
    assert path_within(child, root)
    assert not path_within(tmp_path / "outside", root)
    existing = root / "file.txt"
    existing.write_text("one", encoding="utf-8")
    assert next_available_path(existing).name == "file_1.txt"
    (root / "a.md").write_text("a", encoding="utf-8")
    assert list_files(root, ["*.md"])[0].name == "a.md"
    assert list_domain_markdown_files(root) == [root / "a.md"]
    key_file = tmp_path / "keys.env"
    key_file.write_text("TOKEN=value\n", encoding="utf-8")
    assert load_key_from_file(key_file, "TOKEN") == "value"
    with pytest.raises(ValueError):
        load_key_from_file(key_file, "MISSING")


def test_bundle_publication_preflights_all_destinations(tmp_path) -> None:
    first, second = next_available_bundle(tmp_path, "artifact", (".md", ".json"))
    first.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError):
        write_text_bundle({first: "replacement", second: "new"})

    assert first.read_text(encoding="utf-8") == "existing"
    assert not second.exists()


def test_config_and_root_validation(tmp_path, monkeypatch) -> None:
    with pytest.raises(ValueError, match="Invalid configuration name"):
        load_config("../unsafe")
    with pytest.raises(ValueError, match="null"):
        validate_config_data({"value": None}, "test")
    monkeypatch.setenv("START_REPO_ROOT", str(tmp_path))
    with pytest.raises(RuntimeError, match="not a START project"):
        find_repo_root()
    monkeypatch.delenv("START_REPO_ROOT")


def test_provider_policy_and_response_validation() -> None:
    with pytest.raises(ValueError, match="timeout"):
        ChatPolicy(model="local", timeout=0)
    with pytest.raises(ValueError, match="completion choice"):
        validate_chat_response(SimpleNamespace(choices=[]))
    with pytest.raises(ValueError, match="min_content_length"):
        validate_chat_response(SimpleNamespace(choices=[]), min_content_length=0)
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="  answer  "))]
    )
    assert validate_chat_response(response) == "answer"
    with pytest.raises(ValueError, match="base URL"):
        _validate_config(
            type(
                "Config",
                (),
                {
                    "api_key": "key",
                    "base_url": "bad",
                    "model": "m",
                    "timeout": 1,
                    "max_retries": 1,
                    "backoff_seconds": 0,
                },
            )()
        )


def test_curriculum_validation_and_duplicate_sections(tmp_path) -> None:
    assert validate_curriculum_content("")["valid"] is False
    assert validate_curriculum_content("short", min_word_count=10)["valid"] is False
    with pytest.raises(ValueError, match="Duplicate"):
        extract_sections("## Same\nfirst\n## Same\nsecond")
    research = tmp_path / "research.json"
    research.write_text(json.dumps({"research_data": "Research text"}), encoding="utf-8")
    assert _load_research_content(str(research))[1] == "Research text"
    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="parse"):
        _load_research_content(str(bad))


def test_translation_chunking_and_parallel_processing(tmp_path) -> None:
    assert split_content_into_chunks("", 10) == []
    assert all(len(chunk) <= 10 for chunk in split_content_into_chunks("x" * 25, 10))
    curriculum = tmp_path / "curricula" / "reader"
    curriculum.mkdir(parents=True)
    (curriculum / "complete_curriculum_1.md").write_text("# Title\n\nSource text", encoding="utf-8")
    with LocalCompletionServer("A sufficiently detailed translated response.") as server:
        result = translate_curriculum_result(
            server.client(), "# Title\n\nSource text", "Spanish", model="local", delay_seconds=0
        )
    assert result.content.startswith("A sufficiently")

    (curriculum / "complete_curriculum_2.md").write_text("# Title\n\nSource text", encoding="utf-8")
    with LocalCompletionServer("A sufficiently detailed translated response.") as server:
        success, failed, _items = process_translations_detailed(
            server.client(),
            str(tmp_path / "curricula"),
            str(tmp_path / "translations"),
            ["Spanish", "French"],
            model="local",
            max_concurrent=2,
            delay_seconds=0,
        )
    assert success == 4
    assert failed == 0


def test_curriculum_generation_is_transactional(tmp_path) -> None:
    research = tmp_path / "reader_research.md"
    fep = tmp_path / "fep.md"
    research.write_text(
        "## First\n" + "source " * 40 + "\n\n## Second\n" + "source " * 40,
        encoding="utf-8",
    )
    fep.write_text("reference " * 20, encoding="utf-8")
    response = "generated " * 120
    with LocalCompletionServer(response) as server:
        output = process_research_file(
            server.client(),
            str(research),
            str(fep),
            str(tmp_path / "written"),
            model="local",
            max_retries=1,
            delay_seconds=0,
            save_intermediate_results=True,
        )
    assert output and output.exists()
    assert list((tmp_path / "written" / "reader").glob("*.md"))

    with LocalCompletionServer("") as server:
        with pytest.raises(RuntimeError, match="no partial output"):
            process_research_file(
                server.client(),
                str(research),
                str(fep),
                str(tmp_path / "failed"),
                model="local",
                max_retries=1,
            )
    assert not (tmp_path / "failed").exists()


def test_structured_pipeline_results() -> None:
    stage = StageResult("stage", successes=["a"], skips=["b"])
    pipeline = PipelineResult([stage], duration_seconds=0.1)
    assert pipeline.ok
    assert bool(pipeline)
    assert pipeline.as_dict()["stages"]["stage"]["success"] == 1


def test_pipeline_provider_failure_is_not_reported_as_success(monkeypatch, tmp_path) -> None:
    from learning.curriculum_creation.generate_custom_curriculum import (
        CurriculumConfig,
        CurriculumOrchestrator,
    )

    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    config = CurriculumConfig(
        target_domains=["biochemistry"],
        target_entities=["karl_friston"],
        target_languages=["Spanish"],
        custom_output_dir=tmp_path / "outputs",
        run_entity_research=False,
        run_curriculum_generation=False,
        run_visualizations=False,
        run_translations=False,
        skip_existing_research=False,
    )

    result = CurriculumOrchestrator(config).run_complete_pipeline()

    assert result.ok is False
    assert "domain_research" in result.failures
    domain_stage = next(stage for stage in result.stages if stage.name == "domain_research")
    assert domain_stage.errors


def test_pipeline_rejects_protected_output_roots() -> None:
    from learning.curriculum_creation.generate_custom_curriculum import CurriculumConfig

    config = CurriculumConfig(custom_output_dir="/")
    with pytest.raises(ValueError, match="protected"):
        config.output_directories()

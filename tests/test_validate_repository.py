from __future__ import annotations

from pathlib import Path

import pytest

from scripts import validate_repository


def test_validate_file_rejects_duplicate_yaml_keys(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(validate_repository, "ROOT", tmp_path)
    config = Path("config.yaml")
    (tmp_path / config).write_text("name: one\nname: two\n", encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate YAML key"):
        validate_repository.validate_file(config)


def test_authored_file_filters_exclude_generated_and_third_party() -> None:
    paths = [
        Path("src/module.py"),
        Path("data/domain_research/generated.md"),
        Path("data/written_curriculums/generated.md"),
        Path("examples/vfe/node_modules/package/README.md"),
        Path("uv.lock"),
    ]

    assert validate_repository.authored_text_files(paths) == [Path("src/module.py")]


def test_validate_authored_terms_flags_policy_violations(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(validate_repository, "ROOT", tmp_path)
    source = Path("src/example.py")
    (tmp_path / "src").mkdir()
    provider_line = "# " + "simulated" + " API test"
    stale_path_line = "# use " + "Languages" + "/old"
    (tmp_path / source).write_text(
        f"real line\n{provider_line}\n{stale_path_line}\n",
        encoding="utf-8",
    )

    failures = validate_repository.validate_authored_terms(source)

    assert any("prohibited authored terminology" in failure for failure in failures)
    expected_stale_message = "stale " + "Languages" + "/ path"
    assert any(expected_stale_message in failure for failure in failures)


def test_validate_authored_terms_allows_protocol_wording(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(validate_repository, "ROOT", tmp_path)
    source = Path("src/client.py")
    (tmp_path / "src").mkdir()
    (tmp_path / source).write_text("OpenAI-compatible protocol\n", encoding="utf-8")

    assert validate_repository.validate_authored_terms(source) == []


def test_validate_markdown_links_detects_broken_and_escaping_links(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(validate_repository, "ROOT", tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "page.md").write_text(
        "[ok](target.md)\n[missing](missing.md)\n[escape](../outside.md)\n",
        encoding="utf-8",
    )
    (docs / "target.md").write_text("ok\n", encoding="utf-8")

    failures = validate_repository.validate_markdown_links(Path("docs/page.md"))

    assert any("broken local link: missing.md" in failure for failure in failures)
    assert any("broken local link: ../outside.md" in failure for failure in failures)


def test_tracked_config_files_include_untracked_candidates() -> None:
    paths = [Path("pyproject.toml"), Path("README.md"), Path("data.json")]

    assert validate_repository.tracked_config_files(paths) == [
        Path("data.json"),
        Path("pyproject.toml"),
    ]

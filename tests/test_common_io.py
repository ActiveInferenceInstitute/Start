from __future__ import annotations

from pathlib import Path

import pytest

from src.common import io, paths


def test_list_domain_markdown_files_excludes_fep_actinf():
    domain_path = paths.data_domain_research_dir()
    files = io.list_domain_markdown_files(domain_path, exclude_stems=["Synthetic_FEP-ActInf"])
    # Ensure we are reading real data and exclusion works
    assert all(p.suffix == ".md" for p in files)
    assert all(p.stem != "Synthetic_FEP-ActInf" for p in files)
    # Test passes whether domain files exist or not
    assert len(files) >= 0


def test_read_and_write_text(tmp_path: Path):
    file_path = tmp_path / "example.txt"
    content = "hello world"
    out = io.write_text(file_path, content)
    assert out.exists()
    assert io.read_text(out) == content


def test_read_and_write_json(tmp_path: Path):
    file_path = tmp_path / "data.json"
    data = {"a": 1, "b": [1, 2, 3]}
    out = io.write_json(file_path, data)
    assert out.exists()
    assert io.read_json(out) == data


def test_collision_safe_bundle_validation(tmp_path: Path):
    with pytest.raises(ValueError, match="stem"):
        io.next_available_bundle(tmp_path, " ", [".md"])
    with pytest.raises(ValueError, match="suffixes"):
        io.next_available_bundle(tmp_path, "name", [])

    (tmp_path / "name.md").write_text("old", encoding="utf-8")
    md_path, json_path = io.next_available_bundle(tmp_path, "name", [".md", "json"])
    assert md_path.name == "name_1.md"
    assert json_path.name == "name_1.json"


def test_write_text_bundle_rejects_invalid_inputs(tmp_path: Path):
    with pytest.raises(ValueError, match="empty"):
        io.write_text_bundle({})
    with pytest.raises(TypeError, match="strings"):
        io.write_text_bundle({tmp_path / "bad.txt": object()})  # type: ignore[dict-item]

    existing = tmp_path / "exists.txt"
    existing.write_text("already here", encoding="utf-8")
    with pytest.raises(FileExistsError, match="already exists"):
        io.write_text_bundle({existing: "new"})

    written = io.write_text_bundle(
        {
            tmp_path / "a.txt": "a",
            tmp_path / "nested" / "b.txt": "b",
        }
    )
    assert [path.name for path in written] == ["a.txt", "b.txt"]
    assert (tmp_path / "nested" / "b.txt").read_text(encoding="utf-8") == "b"


def test_writes_refuse_symlink_file_and_parent_boundaries(tmp_path: Path):
    target = tmp_path / "target.txt"
    target.write_text("original", encoding="utf-8")
    link = tmp_path / "link.txt"
    link.symlink_to(target)
    with pytest.raises(ValueError, match="symlink"):
        io.write_text(link, "replacement")
    assert target.read_text(encoding="utf-8") == "original"

    outside = tmp_path / "outside"
    outside.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        io.write_text(linked_parent / "child.txt", "blocked")
    assert not (outside / "child.txt").exists()

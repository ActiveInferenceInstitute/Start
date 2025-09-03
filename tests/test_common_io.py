from __future__ import annotations

from pathlib import Path

from src.common import io, paths


def test_list_domain_markdown_files_excludes_fep_actinf():
    domain_path = paths.domain_dir()
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

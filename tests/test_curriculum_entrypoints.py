from __future__ import annotations

import importlib.util

import pytest

from src.perplexity.translation import split_content_into_chunks


def load_script(name: str):
    path = __import__("pathlib").Path("learning/curriculum_creation") / name
    spec = importlib.util.spec_from_file_location(name.replace(".", "_"), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_research_entrypoint_discovers_real_files(tmp_path) -> None:
    module = load_script("2_Write_Introduction.py")
    (tmp_path / "reader_research_1.md").write_text("content", encoding="utf-8")
    (tmp_path / "not_research_bad.md").write_text("content", encoding="utf-8")
    assert [path.name for path in module.get_research_files(tmp_path)] == ["reader_research_1.md"]


def test_translation_chunking_splits_long_sections() -> None:
    chunks = split_content_into_chunks("## Header\n" + "x" * 50, 10)
    assert chunks
    assert all(len(chunk) <= 10 for chunk in chunks)
    with pytest.raises(ValueError, match="greater than zero"):
        split_content_into_chunks("text", 0)

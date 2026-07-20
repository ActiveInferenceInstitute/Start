from __future__ import annotations

from src.perplexity.translation import save_translation, split_content_into_chunks


def test_split_content_chunks_preserves_headers():
    content = """
# Title
Intro
## A
Text A
## B
Text B
""".strip()
    chunks = split_content_into_chunks(content, max_chunk_size=20)
    assert any("## A" in c for c in chunks)
    assert any("## B" in c for c in chunks)


def test_save_translation(tmp_path):
    out = save_translation(str(tmp_path), "EntityX", "Spanish", "Hola mundo")
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "language: Spanish" in text
    assert "original_entity: EntityX" in text
    assert "entity_id: entityx" in text
    assert out.parent.name == "spanish"


def test_save_translation_rejects_empty_content(tmp_path):
    try:
        save_translation(str(tmp_path), "EntityX", "Spanish", "")
    except ValueError as exc:
        assert "content" in str(exc)
    else:
        raise AssertionError("empty translation was accepted")

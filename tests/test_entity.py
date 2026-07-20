from __future__ import annotations

import json

from fixtures import LocalCompletionServer

from src.perplexity.entity import extract_entity_description, research_target_audience


def test_extract_entity_description() -> None:
    assert extract_entity_description("Name: reader\nDescription: A researcher") == "A researcher"
    assert extract_entity_description("reader") == "reader"


def test_research_target_audience_uses_local_http_and_safe_output(tmp_path) -> None:
    entity = tmp_path / "audience.md"
    fep = tmp_path / "fep.md"
    entity.write_text("Entity content", encoding="utf-8")
    fep.write_text("Reference", encoding="utf-8")
    with LocalCompletionServer("audience research response") as server:
        result = research_target_audience(
            server.client(), str(entity), str(fep), str(tmp_path / "out"), model="local"
        )
    output = next((tmp_path / "out").glob("*.json"))
    data = json.loads(output.read_text(encoding="utf-8"))
    assert result.research_data == data["research_data"] == "audience research response"


def test_research_target_audience_uses_stable_id_for_artifact_identity(tmp_path) -> None:
    fep = tmp_path / "fep.md"
    fep.write_text("Reference", encoding="utf-8")
    with LocalCompletionServer("audience research response") as server:
        result = research_target_audience(
            server.client(),
            "Display entity content",
            str(fep),
            str(tmp_path / "out"),
            entity_name="Display Entity",
            entity_id="display-entity-id",
            model="local",
        )
    assert result.metadata["entity_id"] == "display-entity-id"
    assert "display-entity-id_research_" in result.output_paths[0]

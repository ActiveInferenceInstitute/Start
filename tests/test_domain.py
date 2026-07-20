from __future__ import annotations

import json

import pytest
from fixtures import LocalCompletionServer

from src.perplexity.domain import analyze_domain, chat_result


def test_domain_chat_uses_production_http_protocol() -> None:
    with LocalCompletionServer("local domain response") as server:
        result = chat_result(server.client(), "research prompt", "research system", model="local")
    assert result.content == "local domain response"


def test_analyze_domain_writes_collision_safe_real_outputs(tmp_path) -> None:
    domain = tmp_path / "domain.md"
    fep = tmp_path / "fep.md"
    domain.write_text("A domain description", encoding="utf-8")
    fep.write_text("Reference material", encoding="utf-8")

    def response(payload: dict) -> str:
        return "curriculum result" if "curriculum" in str(payload).lower() else "analysis result"

    with LocalCompletionServer(response) as server:
        result = analyze_domain(
            server.client(), str(domain), str(fep), str(tmp_path / "out"), model="local"
        )

    assert result.domain_name == "domain"
    outputs = list((tmp_path / "out").iterdir())
    assert {path.suffix for path in outputs} == {".json", ".md"}
    assert (
        json.loads(next(path for path in outputs if path.suffix == ".json").read_text())[
            "domain_name"
        ]
        == "domain"
    )


def test_analyze_domain_uses_stable_id_for_artifact_identity(tmp_path) -> None:
    fep = tmp_path / "fep.md"
    fep.write_text("Reference material", encoding="utf-8")

    def response(payload: dict) -> str:
        return "curriculum result" if "curriculum" in str(payload).lower() else "analysis result"

    with LocalCompletionServer(response) as server:
        result = analyze_domain(
            server.client(),
            "Display domain content",
            str(fep),
            str(tmp_path / "out"),
            domain_name="Display Domain",
            domain_id="display-domain-id",
            model="local",
        )

    assert result.metadata["domain_id"] == "display-domain-id"
    assert all("display-domain-id_research_" in path for path in result.output_paths)


def test_domain_chat_rejects_empty_prompt(tmp_path) -> None:
    with LocalCompletionServer("response") as server:
        with pytest.raises(ValueError, match="Prompt"):
            chat_result(server.client(), "", "system")

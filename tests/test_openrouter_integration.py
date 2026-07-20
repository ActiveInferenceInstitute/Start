from __future__ import annotations

import pytest
from fixtures import LocalCompletionServer

from src.perplexity.clients import ChatPolicy, complete_chat_result
from src.perplexity.curriculum import chat_result as curriculum_chat_result
from src.perplexity.translation import translate_curriculum_result


def test_openai_compatible_completion_is_a_real_local_request() -> None:
    seen: list[dict] = []

    def respond(payload: dict) -> str:
        seen.append(payload)
        return "This is a sufficiently detailed local completion response."

    with LocalCompletionServer(respond) as server:
        result = complete_chat_result(
            server.client(),
            [{"role": "user", "content": "hello"}],
            ChatPolicy(model="local", min_content_length=10),
        )
    assert result.content.startswith("This is")
    assert seen[0]["model"] == "local"


def test_curriculum_and_translation_use_local_provider(tmp_path) -> None:
    response = "This is a sufficiently detailed local completion response."
    with LocalCompletionServer(response) as server:
        client = server.client()
        assert (
            curriculum_chat_result(client, "outline", "educator", model="local").content == response
        )
        translated = translate_curriculum_result(
            client, "# Title\n\nA paragraph with enough source text.", "Spanish", model="local"
        )
    assert translated.content == response


def test_empty_provider_content_is_rejected() -> None:
    with LocalCompletionServer("") as server:
        with pytest.raises(RuntimeError, match="completion failed"):
            curriculum_chat_result(
                server.client(), "outline", "educator", model="local", max_retries=1
            )

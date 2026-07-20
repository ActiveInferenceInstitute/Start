"""Local protocol fixtures used by provider integration tests."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from openai import OpenAI


class _CompletionHandler(BaseHTTPRequestHandler):
    server_version = "STARTLocalCompletion/1.0"

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        response_text = self.server.responder(payload)  # type: ignore[attr-defined]
        response = {
            "id": "local-response",
            "object": "chat.completion",
            "created": 1,
            "model": payload.get("model", "local-model"),
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": response_text},
                }
            ],
        }
        encoded = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, _format: str, *_args: Any) -> None:
        return


class LocalCompletionServer:
    """A real local HTTP completion endpoint for the production OpenAI client."""

    def __init__(self, responder: Callable[[dict[str, Any]], str] | str):
        self.responder = (lambda _payload: responder) if isinstance(responder, str) else responder
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _CompletionHandler)
        self.server.responder = self.responder  # type: ignore[attr-defined]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.server.server_port}/v1"

    def __enter__(self) -> "LocalCompletionServer":
        self.thread.start()
        return self

    def __exit__(self, *_args: Any) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def client(self) -> OpenAI:
        return OpenAI(api_key="local-test-key", base_url=self.base_url, max_retries=0, timeout=5)

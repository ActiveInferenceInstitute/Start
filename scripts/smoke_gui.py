"""Exercise the loopback curriculum GUI endpoints without a browser."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def main() -> int:
    port = free_port()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "learning.curriculum_creation.generate_curriculum_gui",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--no-browser",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(base + "/status", timeout=1) as response:
                    status = json.loads(response.read().decode("utf-8"))
                break
            except Exception as exc:
                if process.poll() is not None:
                    stdout, stderr = process.communicate(timeout=1)
                    raise RuntimeError(
                        f"GUI exited early: stdout={stdout!r} stderr={stderr!r}"
                    ) from exc
                time.sleep(0.25)
        else:
            raise TimeoutError("GUI did not become ready")

        assert status["running"] is False
        for path in ("/", "/options"):
            with urllib.request.urlopen(base + path, timeout=3) as response:
                assert response.status == 200
                assert response.read()

        request = urllib.request.Request(
            base + "/start",
            data=json.dumps({"domain": "", "entity": "", "language": ""}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(request, timeout=3)
        except urllib.error.HTTPError as exc:
            assert exc.code == 400
        else:
            raise AssertionError("invalid /start payload unexpectedly succeeded")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    print("GUI endpoint smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

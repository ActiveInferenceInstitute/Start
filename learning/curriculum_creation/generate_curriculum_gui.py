"""Browser-based GUI for custom Active Inference curriculum generation.

This script launches a lightweight local HTTP server and opens a browser UI to
collect inputs (domain, entity, language, optional entity description), then
runs the existing curriculum generation pipeline while displaying a live status
indicator with a progress estimate. When finished, a concise result summary is
shown in the UI.

Design notes:
- The GUI server introduces no new third-party dependencies beyond the project's
  existing pipeline dependencies (the script itself uses only the standard library).
- The script imports the canonical orchestrator and typed configuration helpers
  directly so the browser and CLI share one execution path.
- Progress is estimated at stage granularity with simple weights; ETA is
  extrapolated from elapsed time and fraction complete.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import secrets
import sys
import threading
import time
import uuid
import webbrowser
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from learning.curriculum_creation.generate_custom_curriculum import (  # noqa: E402
    CurriculumConfig,
    CurriculumOrchestrator,
)
from src.common.logging_utils import redact_log_value  # noqa: E402
from src.config.catalog import load_domains_config, load_entities_config  # noqa: E402
from src.config.schemas import stable_identifier  # noqa: E402


def _get_available_options() -> Tuple[List[str], List[str], List[str]]:
    """Return available domains, entities, and languages.

    Returns:
        Tuple of lists: (domains, entities, languages)
    """
    domains_config = load_domains_config()
    domains = [d["name"] for d in domains_config.get("domains", [])]
    entities_config = load_entities_config()
    entities = [e["name"] for e in entities_config.get("entities", [])]
    from src.config.languages import get_target_languages

    languages = get_target_languages()
    if not domains or not entities or not languages:
        raise ValueError("Domain, entity, and language configuration must not be empty")

    return domains, entities, languages


def _parse_start_payload(data: object) -> tuple[str, str, str, Optional[str]]:
    """Validate and normalize a JSON start request before launching work."""
    if not isinstance(data, dict):
        raise ValueError("JSON body must be an object")

    def required_text(name: str, maximum: int) -> str:
        value = data.get(name)
        if not isinstance(value, str):
            raise ValueError(f"{name} must be a string")
        value = value.strip()
        if not value or len(value) > maximum:
            raise ValueError(f"{name} must be between 1 and {maximum} characters")
        return value

    domain = required_text("domain", 200)
    entity = required_text("entity", 200)
    language = required_text("language", 100)
    description = data.get("entity_description")
    if description is None:
        entity_description = None
    elif isinstance(description, str):
        entity_description = description.strip() or None
        if entity_description is not None and len(entity_description) > 2000:
            raise ValueError("entity_description must be at most 2000 characters")
    else:
        raise ValueError("entity_description must be a string or null")

    return domain, entity, language, entity_description


@dataclass
class GuiStatus:
    """Thread-safe shared status for the GUI."""

    stage_index: int
    stage_name: str
    progress: float  # 0.0-1.0
    message: str
    eta_seconds: Optional[int]
    started_at: float
    done: bool
    error: Optional[str]
    results: Optional[Dict[str, Any]]


_STATUS_LOCK = threading.Lock()
_STATUS: GuiStatus = GuiStatus(
    stage_index=-1,
    stage_name="Idle",
    progress=0.0,
    message="Ready",
    eta_seconds=None,
    started_at=0.0,
    done=False,
    error=None,
    results=None,
)
_RUN_ACTIVE = False
_RUN_ID: Optional[str] = None
_CANCEL_EVENT = threading.Event()


_STAGE_ORDER: List[Tuple[str, str]] = [
    ("Domain Research", "run_domain_research_stage"),
    ("Entity Research", "run_entity_research_stage"),
    ("Curriculum Generation", "run_curriculum_generation_stage"),
    ("Visualization", "run_visualization_stage"),
    ("Translation", "run_translation_stage"),
]

# Coarse weights per stage, summing to 1.0
_STAGE_WEIGHTS: List[float] = [0.25, 0.25, 0.30, 0.10, 0.10]


def _safe_public_error(value: object) -> str:
    """Keep provider credentials, prompt bodies, and large traces out of GUI output."""

    text = redact_log_value(value)
    # Local paths and provider request details are operational diagnostics,
    # not browser data.  Keep only a short, non-sensitive summary.
    text = re.sub(
        r"(?<![A-Za-z0-9])/(?:Users|private|tmp|var|home|etc|usr|opt|System|Library|bin|sbin|srv|dev|proc|Volumes|Applications)/[^\s,;]+",
        "[path]",
        text,
    )
    text = re.sub(r"(?i)\b[A-Za-z]:\\[^\s,;]*", "[path]", text)
    return text[:500]


def estimate_progress(stage_index: int, in_stage: bool) -> float:
    """Estimate overall progress based on the current stage.

    Args:
        stage_index: Zero-based index of the current stage; -1 when idle.
        in_stage: True if the stage has started but not finished yet.

    Returns:
        Progress value in [0.0, 1.0].
    """
    if stage_index < 0:
        return 0.0
    completed = sum(_STAGE_WEIGHTS[: max(0, stage_index)])
    if in_stage:
        # Assume halfway through the current stage for a simple live estimate
        return min(1.0, completed + _STAGE_WEIGHTS[stage_index] * 0.5)
    return min(1.0, completed)


def estimate_eta_seconds(started_at: float, progress: float) -> Optional[int]:
    """Estimate remaining seconds based on elapsed time and progress.

    Args:
        started_at: Epoch seconds when the run started.
        progress: Current overall progress fraction (0..1).

    Returns:
        Estimated seconds remaining, or None if indeterminate.
    """
    if progress <= 0.01:
        return None
    elapsed = max(0.0, time.time() - started_at)
    total_estimate = elapsed / progress
    remaining = max(0.0, total_estimate - elapsed)
    return int(remaining)


def build_config_from_form(
    domain: str,
    entity: str,
    language: str,
    entity_description: Optional[str] = None,
) -> Any:
    """Build a CurriculumConfig from GUI form inputs.

    The returned object is an instance of the orchestrator's `CurriculumConfig`.
    """
    cfg = CurriculumConfig(
        target_domains=[domain],
        target_entities=[entity],
        target_languages=[language],
        skip_existing_research=False,
        skip_existing_curricula=False,
        skip_existing_translations=False,
        verbose_logging=True,
    )
    if entity_description:
        cfg.custom_entity_description = entity_description
    return cfg


def _wrap_stages_for_progress(orchestrator: Any) -> None:
    """Monkey-patch stage methods to update GUI status before/after each stage."""

    for idx, (stage_name, method_name) in enumerate(_STAGE_ORDER):
        original: Callable[[], bool] = getattr(orchestrator, method_name)

        def make_wrapped(i: int, name: str, fn: Callable[[], bool]) -> Callable[[], bool]:
            def wrapped() -> bool:
                if _CANCEL_EVENT.is_set():
                    return False
                with _STATUS_LOCK:
                    _STATUS.stage_index = i
                    _STATUS.stage_name = name
                    _STATUS.message = f"Starting {name}"
                    _STATUS.progress = estimate_progress(i, in_stage=True)
                    _STATUS.eta_seconds = estimate_eta_seconds(_STATUS.started_at, _STATUS.progress)
                ok = fn()
                with _STATUS_LOCK:
                    _STATUS.progress = estimate_progress(i + 1, in_stage=False)
                    _STATUS.message = f"Completed {name}" if ok else f"Failed {name}"
                    _STATUS.eta_seconds = estimate_eta_seconds(_STATUS.started_at, _STATUS.progress)
                return ok

            return wrapped

        setattr(orchestrator, method_name, make_wrapped(idx, stage_name, original))


def _results_to_summary_html(results: Dict[str, Any]) -> str:
    """Convert orchestrator results dict to a small HTML summary block."""
    parts: List[str] = [
        '<div style="font-family:system-ui,Segoe UI,Roboto,Arial">',
        "<h2>Run Summary</h2>",
        "<ul>",
    ]
    for key, data in results.items():
        if isinstance(data, dict) and "success" in data:
            if key == "visualizations":
                status = (
                    "Success" if data.get("success") else f"Failed: {data.get('error', 'Unknown')}"
                )
                parts.append(
                    f"<li><b>{html.escape(key.replace('_', ' ').title())}</b>: {html.escape(status)}</li>"
                )
            else:
                succ = data.get("success", 0)
                fail = data.get("failed", 0)
                skip = data.get("skipped", 0)
                parts.append(
                    f"<li><b>{html.escape(key.replace('_', ' ').title())}</b>: "
                    f"{succ} successful, {fail} failed, {skip} skipped</li>"
                )
                for error in data.get("errors", []):
                    parts.append(f'<li class="error">{html.escape(_safe_public_error(error))}</li>')
    parts.append("</ul></div>")
    return "".join(parts)


def _run_pipeline_in_thread(cfg: Any) -> None:
    global _RUN_ACTIVE, _RUN_ID
    try:
        orchestrator = CurriculumOrchestrator(cfg)
    except Exception as exc:  # pragma: no cover - defensive thread boundary
        with _STATUS_LOCK:
            _STATUS.done = True
            _STATUS.error = _safe_public_error(exc)
            _STATUS.message = "Failed"
            _RUN_ACTIVE = False
        return
    with _STATUS_LOCK:
        _RUN_ID = cfg.run_id
        _STATUS.started_at = time.time()
        _STATUS.done = False
        _STATUS.error = None
        _STATUS.results = None
        _STATUS.stage_index = 0
        _STATUS.stage_name = _STAGE_ORDER[0][0]
        _STATUS.progress = 0.0
        _STATUS.message = "Initializing"
        _STATUS.eta_seconds = None

    # Wrap stages for GUI progress updates
    _wrap_stages_for_progress(orchestrator)

    try:
        ok = orchestrator.run_complete_pipeline()
        with _STATUS_LOCK:
            _STATUS.done = True
            _STATUS.progress = 1.0 if ok else _STATUS.progress
            _STATUS.message = "Completed" if ok else "Completed with errors"
            _STATUS.eta_seconds = 0
            _STATUS.results = orchestrator.results
            _STATUS.message = "Cancelled" if _CANCEL_EVENT.is_set() else _STATUS.message
            if not ok:
                _STATUS.error = "One or more stages failed. See summary."
    except Exception as exc:  # pragma: no cover - defensive
        with _STATUS_LOCK:
            _STATUS.done = True
            _STATUS.error = _safe_public_error(exc)
            _STATUS.message = "Failed"
            _STATUS.eta_seconds = None
    finally:
        with _STATUS_LOCK:
            _RUN_ACTIVE = False


class _GuiHandler(BaseHTTPRequestHandler):
    """HTTP handler serving the GUI, options, start, and status endpoints."""

    server_version = "CurriculumGUI/1.0"

    def _set_headers(
        self, status: int = 200, content_type: str = "text/html; charset=utf-8"
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'",
        )
        self.send_header("Connection", "close")
        self.end_headers()

    def _authorized(self) -> bool:
        expected = getattr(self.server, "auth_token", None)
        if not expected:
            return True
        supplied = self.headers.get("X-START-Token", "")
        return secrets.compare_digest(supplied, expected)

    def _cross_site_request(self) -> bool:
        """Reject state-changing POSTs that came from a non-loopback origin.

        A browser-driven cross-site form POST carries an Origin/Referer header
        of the attacker's host; rejecting non-loopback origins blocks that
        CSRF vector while still allowing same-origin and local tool requests.
        """
        for header in ("Origin", "Referer"):
            value = self.headers.get(header)
            if not value:
                continue
            parsed = urlparse(value)
            hostname = (parsed.hostname or "").lower().rstrip(".")
            if hostname not in {
                "localhost",
                "127.0.0.1",
                "::1",
                "0.0.0.0",
            } and not hostname.startswith("127."):
                return True
        return False

    def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler API)
        if not self._authorized():
            self._set_headers(HTTPStatus.UNAUTHORIZED, "text/plain; charset=utf-8")
            self.wfile.write(b"Authentication required")
            return
        if self.path == "/" or self.path.startswith("/index.html"):
            self._serve_index()
            return
        if self.path == "/options":
            self._serve_options()
            return
        if self.path == "/status":
            self._serve_status()
            return
        if self.path == "/results":
            self._serve_results()
            return
        self._set_headers(HTTPStatus.NOT_FOUND)
        self.wfile.write(b"Not found")

    def do_POST(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler API)
        if not self._authorized():
            self._set_headers(HTTPStatus.UNAUTHORIZED, "text/plain; charset=utf-8")
            self.wfile.write(b"Authentication required")
            return
        if self._cross_site_request():
            self._set_headers(HTTPStatus.FORBIDDEN, "text/plain; charset=utf-8")
            self.wfile.write(b"Cross-site request rejected")
            return
        if self.path == "/start":
            self._handle_start()
            return
        if self.path == "/cancel":
            self._handle_cancel()
            return
        self._set_headers(HTTPStatus.NOT_FOUND)
        self.wfile.write(b"Not found")

    def _serve_index(self) -> None:
        self._set_headers()
        html = _INDEX_HTML
        self.wfile.write(html.encode("utf-8"))

    def _serve_options(self) -> None:
        try:
            domains, entities, languages = _get_available_options()
        except (OSError, ValueError, KeyError) as exc:
            self._set_headers(HTTPStatus.INTERNAL_SERVER_ERROR, "application/json; charset=utf-8")
            self.wfile.write(json.dumps({"error": _safe_public_error(exc)}).encode("utf-8"))
            return
        payload = {
            "domains": domains,
            "entities": entities,
            "languages": languages,
            "identifiers": {
                "domains": {
                    str(item["name"]): str(item.get("id") or stable_identifier(item["name"]))
                    for item in load_domains_config().get("domains", [])
                },
                "entities": {
                    str(item["name"]): str(item.get("id") or stable_identifier(item["name"]))
                    for item in load_entities_config().get("entities", [])
                },
                "languages": {language: stable_identifier(language) for language in languages},
            },
            "defaults": {
                "domain": domains[0],
                "entity": entities[0],
                "language": languages[0],
            },
        }
        self._set_headers(HTTPStatus.OK, "application/json; charset=utf-8")
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def _serve_status(self) -> None:
        with _STATUS_LOCK:
            s = {
                "stage_index": _STATUS.stage_index,
                "stage_name": _STATUS.stage_name,
                "progress": _STATUS.progress,
                "message": _STATUS.message,
                "eta_seconds": _STATUS.eta_seconds,
                "done": _STATUS.done,
                "error": _STATUS.error,
                "running": _RUN_ACTIVE,
                "run_id": _RUN_ID,
                "cancel_requested": _CANCEL_EVENT.is_set(),
            }
        self._set_headers(HTTPStatus.OK, "application/json; charset=utf-8")
        self.wfile.write(json.dumps(s).encode("utf-8"))

    def _serve_results(self) -> None:
        with _STATUS_LOCK:
            res = _STATUS.results
        if not isinstance(res, dict):
            self._set_headers(HTTPStatus.NO_CONTENT)
            self.wfile.write(b"")
            return
        html = _results_to_summary_html(res)
        self._set_headers(HTTPStatus.OK, "text/html; charset=utf-8")
        self.wfile.write(html.encode("utf-8"))

    def _handle_start(self) -> None:
        try:
            content_len = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_len = -1
        if content_len < 1 or content_len > 64 * 1024:
            status = (
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE
                if content_len > 64 * 1024
                else HTTPStatus.BAD_REQUEST
            )
            self._set_headers(status)
            self.wfile.write(b"Request body must be between 1 and 65536 bytes")
            return
        body = self.rfile.read(content_len)
        try:
            data = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._set_headers(HTTPStatus.BAD_REQUEST)
            self.wfile.write(b"Invalid JSON")
            return
        try:
            domain, entity, language, entity_desc = _parse_start_payload(data)
        except ValueError as exc:
            self._set_headers(HTTPStatus.BAD_REQUEST)
            self.wfile.write(_safe_public_error(exc).encode("utf-8"))
            return

        try:
            _get_available_options()
        except (OSError, ValueError, KeyError) as exc:
            self._set_headers(HTTPStatus.INTERNAL_SERVER_ERROR)
            self.wfile.write(_safe_public_error(exc).encode("utf-8"))
            return

        # Reserve the run slot before starting the worker so simultaneous
        # requests cannot both pass the guard.
        global _RUN_ACTIVE
        with _STATUS_LOCK:
            if _RUN_ACTIVE:
                self._set_headers(HTTPStatus.CONFLICT)
                self.wfile.write(b"A run is already in progress")
                return
            _RUN_ACTIVE = True
            _CANCEL_EVENT.clear()

        try:
            cfg = build_config_from_form(domain, entity, language, entity_desc)
            cfg.run_id = f"gui-{int(time.time())}-{uuid.uuid4().hex[:8]}"
            cfg.cancellation_event = _CANCEL_EVENT
            cfg.validate()
        except Exception as exc:  # any config failure must free the run slot
            with _STATUS_LOCK:
                _RUN_ACTIVE = False
            self._set_headers(HTTPStatus.BAD_REQUEST)
            self.wfile.write(_safe_public_error(exc).encode("utf-8"))
            return
        t = threading.Thread(target=_run_pipeline_in_thread, args=(cfg,), daemon=True)
        t.start()
        self._set_headers(HTTPStatus.ACCEPTED)
        self.wfile.write(b"Started")

    def _handle_cancel(self) -> None:
        with _STATUS_LOCK:
            if not _RUN_ACTIVE:
                self._set_headers(HTTPStatus.CONFLICT)
                self.wfile.write(b"No run is in progress")
                return
            _CANCEL_EVENT.set()
        self._set_headers(HTTPStatus.ACCEPTED)
        self.wfile.write(b"Cancellation requested")


_INDEX_HTML = """  # noqa: E501
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Active Inference Curriculum Generator (GUI)</title>
  <style>
    body { font-family: system-ui, Segoe UI, Roboto, Arial; margin: 24px; }
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 16px; max-width: 880px; }
    .row { display: flex; gap: 16px; flex-wrap: wrap; }
    .col { flex: 1 1 240px; min-width: 240px; }
    label { display: block; font-weight: 600; margin: 8px 0 4px; }
    input, select, textarea { width: 100%; padding: 8px; font-size: 14px; }
    button { padding: 10px 16px; font-size: 14px; cursor: pointer; }
    .muted { color: #666; font-size: 13px; }
    .progress { height: 12px; background: #eee; border-radius: 6px; overflow: hidden; }
    .bar { height: 100%; width: 0%; background: #0b82ff; transition: width 0.3s ease; }
    .status { margin-top: 8px; }
    .error { color: #b00020; }
    .success { color: #0a7a33; }
    .footer { margin-top: 16px; font-size: 12px; color: #555; }
    .results { margin-top: 16px; }
  </style>
  <script>
  let polling = null;

  async function loadOptions() {
    const res = await fetch('/options');
    const data = await res.json();
    populateSelect('domain', data.domains, data.defaults.domain);
    populateSelect('entity', data.entities, data.defaults.entity);
    populateSelect('language', data.languages, data.defaults.language);
  }

  function populateSelect(id, values, defaultVal) {
    const sel = document.getElementById(id);
    sel.innerHTML = '';
    for (const v of values) {
      const opt = document.createElement('option');
      opt.value = v; opt.textContent = v; sel.appendChild(opt);
    }
    if (defaultVal) sel.value = defaultVal;
  }

  function selectedOrCustom(selectId, customId) {
    const custom = document.getElementById(customId).value.trim();
    return custom || document.getElementById(selectId).value;
  }

  async function startRun() {
    const domain = selectedOrCustom('domain', 'domain_custom');
    const entity = selectedOrCustom('entity', 'entity_custom');
    const language = selectedOrCustom('language', 'language_custom');
    const entity_description = document.getElementById('entity_description').value.trim();

    if (!domain || !entity || !language) {
      alert('Please provide domain, entity, and language (select or custom).');
      return;
    }

    const btn = document.getElementById('startBtn');
    btn.disabled = true;
    document.getElementById('results').innerHTML = '';
    updateStatus({stage_name: 'Working', progress: 0, message: 'Starting...', eta_seconds: null, done: false});

    const res = await fetch('/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ domain, entity, language, entity_description })
    });
    if (res.status === 202) {
      if (polling) clearInterval(polling);
      polling = setInterval(pollStatus, 1000);
    } else {
      const text = await res.text();
      alert('Unable to start: ' + text);
      btn.disabled = false;
    }
  }

  function updateStatus(s) {
    const pct = Math.round((s.progress || 0) * 100);
    document.getElementById('bar').style.width = pct + '%';
    document.getElementById('stage').textContent = s.stage_name || 'Idle';
    document.getElementById('msg').textContent = s.message || '';
    const eta = (s.eta_seconds==null) ? '' : (' ~' + s.eta_seconds + 's remaining');
    document.getElementById('eta').textContent = eta;
    const err = document.getElementById('err');
    err.textContent = s.error ? s.error : '';
    err.style.display = s.error ? 'block' : 'none';
  }

  async function pollStatus() {
    const res = await fetch('/status');
    const s = await res.json();
    updateStatus(s);
    if (s.done) {
      clearInterval(polling);
      document.getElementById('startBtn').disabled = false;
      const r = await fetch('/results');
      const html = await r.text();
      document.getElementById('results').innerHTML = html;
    }
  }

  window.addEventListener('DOMContentLoaded', loadOptions);
  </script>
  </head>
  <body>
    <h1>Active Inference Curriculum Generator</h1>
    <p class="muted">Fill in the fields below (use dropdowns or provide custom values), then click Generate.</p>
    <div class="card">
      <div class="row">
        <div class="col">
          <label for="domain">Domain (select)</label>
          <select id="domain"></select>
          <label for="domain_custom">or custom domain</label>
          <input id="domain_custom" placeholder="e.g., Coffee Roasting" />
        </div>
        <div class="col">
          <label for="entity">Entity (select)</label>
          <select id="entity"></select>
          <label for="entity_custom">or custom entity</label>
          <input id="entity_custom" placeholder="e.g., William Blake" />
        </div>
        <div class="col">
          <label for="language">Language (select)</label>
          <select id="language"></select>
          <label for="language_custom">or custom language</label>
          <input id="language_custom" placeholder="e.g., Spanish" />
        </div>
      </div>
      <div class="row">
        <div class="col">
          <label for="entity_description">Custom entity description (optional)</label>
          <textarea id="entity_description" rows="3" placeholder="A brief description for your custom target audience"></textarea>
        </div>
      </div>
      <div class="row" style="align-items: flex-end;">
        <div class="col">
          <button id="startBtn" onclick="startRun()">Generate</button>
        </div>
      </div>
      <div class="row">
        <div class="col">
          <div class="progress"><div id="bar" class="bar"></div></div>
          <div class="status">
            <div><b id="stage">Idle</b> <span id="eta" class="muted"></span></div>
            <div id="msg" class="muted">Ready</div>
            <div id="err" class="error" style="display:none"></div>
          </div>
        </div>
      </div>
      <div id="results" class="results"></div>
      <div class="footer">While working, the UI will show "Working" with a live estimate. Results appear here when done.</div>
    </div>
  </body>
</html>
"""


def _open_browser(url: str) -> None:
    try:
        webbrowser.open(url, new=2)
    except OSError as exc:
        print(f"Unable to open browser: {exc}")


def run_gui_server(
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser_delay: float = 0.6,
    open_browser: bool = True,
    allow_remote: bool = False,
    auth_token: Optional[str] = None,
) -> None:
    """Start the GUI HTTP server and open the default browser."""
    loopback_hosts = {"127.0.0.1", "::1", "localhost"}
    if host not in loopback_hosts and not allow_remote:
        raise ValueError("non-loopback binding requires --allow-remote")
    if host not in loopback_hosts and not auth_token:
        raise ValueError("non-loopback binding requires an authentication token")

    class SecureGuiServer(ThreadingHTTPServer):
        pass

    httpd = SecureGuiServer((host, port), _GuiHandler)
    httpd.auth_token = auth_token
    url = f"http://{host}:{port}/"
    if open_browser:
        threading.Timer(open_browser_delay, _open_browser, args=(url,)).start()
    print(f"GUI available at {url}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover - manual stop
        _CANCEL_EVENT.set()
    finally:
        _CANCEL_EVENT.set()
        httpd.server_close()


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point: run the GUI server."""
    parser = argparse.ArgumentParser(description="Run the local curriculum generator GUI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--allow-remote", action="store_true")
    parser.add_argument(
        "--auth-token", help="Required with --allow-remote; never sent in responses"
    )
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    if (
        args.host not in {"127.0.0.1", "::1", "localhost"}
        and args.allow_remote
        and not args.auth_token
    ):
        parser.error("--auth-token is required with --allow-remote")
    try:
        run_gui_server(
            args.host,
            args.port,
            open_browser=not args.no_browser,
            allow_remote=args.allow_remote,
            auth_token=args.auth_token,
        )
    except (OSError, ValueError) as exc:
        print(f"Error: {_safe_public_error(exc)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

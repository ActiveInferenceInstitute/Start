"""Browser-based GUI for custom Active Inference curriculum generation.

This script launches a lightweight local HTTP server and opens a browser UI to
collect inputs (domain, entity, language, optional entity description), then
runs the existing curriculum generation pipeline while displaying a live status
indicator with a progress estimate. When finished, a concise result summary is
shown in the UI.

Design notes:
- No extra dependencies are introduced; only the Python standard library is used.
- The script dynamically imports the existing orchestrator and config from
  `generate_custom_curriculum.py` and the domain/entity/language utilities
  from sibling scripts to ensure a single source of truth.
- Progress is estimated at stage granularity with simple weights; ETA is
  extrapolated from elapsed time and fraction complete.
"""

from __future__ import annotations

import json
import threading
import time
import webbrowser
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import importlib.util
import sys


# Ensure project root is on path for `src` imports used by orchestrator
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Dynamic import of the CLI orchestrator module to reuse its classes/functions
_ORCH_SPEC = importlib.util.spec_from_file_location(
    "generate_custom_curriculum", SCRIPT_DIR / "generate_custom_curriculum.py"
)
_ORCH_MOD = importlib.util.module_from_spec(_ORCH_SPEC)
assert _ORCH_SPEC and _ORCH_SPEC.loader is not None
# Ensure the module is visible to dataclasses and other reflection logic
sys.modules[_ORCH_SPEC.name] = _ORCH_MOD  # type: ignore[index]
_ORCH_SPEC.loader.exec_module(_ORCH_MOD)

# Types from orchestrator
CurriculumConfig = _ORCH_MOD.CurriculumConfig  # type: ignore[attr-defined]
CurriculumOrchestrator = _ORCH_MOD.CurriculumOrchestrator  # type: ignore[attr-defined]
_import_script_functions = _ORCH_MOD._import_script_functions  # type: ignore[attr-defined]


# Load supporting script modules (domain/entity/language helpers)
_domain_mod, _entity_mod, _curriculum_mod, _viz_mod, _trans_mod = _import_script_functions()


def _get_available_options() -> Tuple[List[str], List[str], List[str]]:
    """Return available domains, entities, and languages.

    Returns:
        Tuple of lists: (domains, entities, languages)
    """
    try:
        domains_config = _domain_mod.load_domains_config()
        domains = [d["name"] for d in domains_config.get("domains", [])]
    except Exception:
        domains = [
            "biochemistry",
            "neuroscience",
            "artificial_intelligence",
            "psychology",
        ]

    try:
        entities_config = _entity_mod.load_entities_config()
        entities = [e["name"] for e in entities_config.get("entities", [])]
    except Exception:
        entities = ["karl_friston", "tulsi_gabbard", "elon_musk"]

    try:
        from src.config.languages import get_target_languages

        languages = get_target_languages()
    except Exception:
        languages = ["Spanish", "French", "Chinese", "Arabic", "Hindi"]

    return domains, entities, languages


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


_STAGE_ORDER: List[Tuple[str, str]] = [
    ("Domain Research", "run_domain_research_stage"),
    ("Entity Research", "run_entity_research_stage"),
    ("Curriculum Generation", "run_curriculum_generation_stage"),
    ("Visualization", "run_visualization_stage"),
    ("Translation", "run_translation_stage"),
]

# Coarse weights per stage, summing to 1.0
_STAGE_WEIGHTS: List[float] = [0.25, 0.25, 0.30, 0.10, 0.10]


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
        # Attach as a private attribute consumed by orchestrator when creating custom entity
        setattr(cfg, "_custom_entity_description", entity_description)
    return cfg


def _wrap_stages_for_progress(orchestrator: Any) -> None:
    """Monkey-patch stage methods to update GUI status before/after each stage."""

    for idx, (stage_name, method_name) in enumerate(_STAGE_ORDER):
        original: Callable[[], bool] = getattr(orchestrator, method_name)

        def make_wrapped(i: int, name: str, fn: Callable[[], bool]) -> Callable[[], bool]:
            def wrapped() -> bool:
                with _STATUS_LOCK:
                    _STATUS.stage_index = i
                    _STATUS.stage_name = name
                    _STATUS.message = f"Starting {name}"
                    _STATUS.progress = estimate_progress(i, in_stage=True)
                    _STATUS.eta_seconds = estimate_eta_seconds(_STATUS.started_at, _STATUS.progress)
                ok = fn()
                with _STATUS_LOCK:
                    _STATUS.progress = estimate_progress(i + 1, in_stage=False)
                    _STATUS.message = (f"Completed {name}" if ok else f"Failed {name}")
                    _STATUS.eta_seconds = estimate_eta_seconds(_STATUS.started_at, _STATUS.progress)
                return ok

            return wrapped

        setattr(orchestrator, method_name, make_wrapped(idx, stage_name, original))


def _results_to_summary_html(results: Dict[str, Any]) -> str:
    """Convert orchestrator results dict to a small HTML summary block."""
    parts: List[str] = [
        "<div style=\"font-family:system-ui,Segoe UI,Roboto,Arial\">",
        "<h2>Run Summary</h2>",
        "<ul>",
    ]
    for key, data in results.items():
        if isinstance(data, dict) and "success" in data:
            if key == "visualizations":
                status = "Success" if data.get("success") else f"Failed: {data.get('error', 'Unknown')}"
                parts.append(f"<li><b>{key.replace('_', ' ').title()}</b>: {status}</li>")
            else:
                succ = data.get("success", 0)
                fail = data.get("failed", 0)
                skip = data.get("skipped", 0)
                parts.append(
                    f"<li><b>{key.replace('_', ' ').title()}</b>: "
                    f"{succ} successful, {fail} failed, {skip} skipped</li>"
                )
    parts.append("</ul></div>")
    return "".join(parts)


def _run_pipeline_in_thread(cfg: Any) -> None:
    orchestrator = CurriculumOrchestrator(cfg)
    with _STATUS_LOCK:
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
            if not ok:
                _STATUS.error = "One or more stages failed. See summary."
    except Exception as exc:  # pragma: no cover - defensive
        with _STATUS_LOCK:
            _STATUS.done = True
            _STATUS.error = str(exc)
            _STATUS.message = "Failed"
            _STATUS.eta_seconds = None


class _GuiHandler(BaseHTTPRequestHandler):
    """HTTP handler serving the GUI, options, start, and status endpoints."""

    server_version = "CurriculumGUI/1.0"

    def _set_headers(self, status: int = 200, content_type: str = "text/html; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler API)
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
        if self.path == "/start":
            self._handle_start()
            return
        self._set_headers(HTTPStatus.NOT_FOUND)
        self.wfile.write(b"Not found")

    def _serve_index(self) -> None:
        self._set_headers()
        html = _INDEX_HTML
        self.wfile.write(html.encode("utf-8"))

    def _serve_options(self) -> None:
        domains, entities, languages = _get_available_options()
        payload = {
            "domains": domains,
            "entities": entities,
            "languages": languages,
            "defaults": {
                "domain": (domains[0] if domains else "biochemistry"),
                "entity": (entities[0] if entities else "karl_friston"),
                "language": (languages[0] if languages else "Spanish"),
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
        content_len = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            data = json.loads(body.decode("utf-8"))
        except Exception:
            self._set_headers(HTTPStatus.BAD_REQUEST)
            self.wfile.write(b"Invalid JSON")
            return

        domain = str(data.get("domain", "")).strip()
        entity = str(data.get("entity", "")).strip()
        language = str(data.get("language", "")).strip()
        entity_desc = str(data.get("entity_description") or "").strip() or None

        if not domain or not entity or not language:
            self._set_headers(HTTPStatus.BAD_REQUEST)
            self.wfile.write(b"Missing required fields")
            return

        # Prevent concurrent runs
        with _STATUS_LOCK:
            if not _STATUS.done and _STATUS.started_at and (_STATUS.progress > 0.0):
                self._set_headers(HTTPStatus.CONFLICT)
                self.wfile.write(b"A run is already in progress")
                return

        cfg = build_config_from_form(domain, entity, language, entity_desc)
        t = threading.Thread(target=_run_pipeline_in_thread, args=(cfg,), daemon=True)
        t.start()
        self._set_headers(HTTPStatus.ACCEPTED)
        self.wfile.write(b"Started")


_INDEX_HTML = """
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

  async function startRun() {
    const domain = document.getElementById('domain').value || document.getElementById('domain_custom').value.trim();
    const entity = document.getElementById('entity').value || document.getElementById('entity_custom').value.trim();
    const language = document.getElementById('language').value || document.getElementById('language_custom').value.trim();
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
    except Exception:
        pass


def run_gui_server(host: str = "127.0.0.1", port: int = 8765, open_browser_delay: float = 0.6) -> None:
    """Start the GUI HTTP server and open the default browser."""
    httpd = ThreadingHTTPServer((host, port), _GuiHandler)
    url = f"http://{host}:{port}/"
    threading.Timer(open_browser_delay, _open_browser, args=(url,)).start()
    print(f"GUI available at {url}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover - manual stop
        pass
    finally:
        httpd.server_close()


def main() -> None:
    """Entry point: run the GUI server."""
    run_gui_server()


if __name__ == "__main__":
    main()



"""Assert the recorded GNN pin agrees with the registration and pipeline command.

The canonical pin file is ``.github/gnn-pin.json`` (schema
``gnn-importer-pin/v1``). ``src/repos/cloning.py`` carries the same revision for
the clone registration, and ``src/gnn/main.py`` builds the pipeline command the
pin describes. This check fails when the three disagree.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from src.gnn.main import build_pipeline_command, registered_revision

ROOT = Path(__file__).resolve().parents[1]
PIN_PATH = ROOT / ".github" / "gnn-pin.json"
PIN_SCHEMA = "gnn-importer-pin/v1"
PIN_REPOSITORY = "ActiveInferenceInstitute/Generalized_Notation_Notation"
PIPELINE_SCRIPT = "src/gnn/main.py"
FULL_REVISION = re.compile(r"^[0-9a-f]{40}$")


def check_pin(pin_path: Path = PIN_PATH) -> list[str]:
    """Return every disagreement between the pin, registration, and command."""

    failures: list[str] = []
    try:
        pin = json.loads(pin_path.read_text(encoding="utf-8"))
    except OSError as exc:
        return [f"{pin_path.relative_to(ROOT)}: unreadable: {exc}"]
    except json.JSONDecodeError as exc:
        return [f"{pin_path.relative_to(ROOT)}: invalid JSON: {exc}"]

    if pin.get("schema") != PIN_SCHEMA:
        failures.append(f"schema is {pin.get('schema')!r}, expected {PIN_SCHEMA!r}")
    if pin.get("repository") != PIN_REPOSITORY:
        failures.append(f"repository is {pin.get('repository')!r}, expected {PIN_REPOSITORY!r}")
    revision = pin.get("revision")
    if not isinstance(revision, str) or not FULL_REVISION.match(revision):
        failures.append(f"revision is not a full 40-character commit id: {revision!r}")
        revision = None
    if not str(pin.get("tag") or "").strip():
        failures.append("tag is empty")

    registered = registered_revision()
    if revision is not None and registered != revision:
        failures.append(
            f"registered revision {registered!r} does not match pin {revision!r} "
            "(src/repos/cloning.py)"
        )

    command = build_pipeline_command(
        ["python"], (3, 5), Path("/tmp/gnn-models"), Path("/tmp/gnn-output")
    )
    if command[1] != PIPELINE_SCRIPT:
        failures.append(f"pipeline script is {command[1]!r}, expected {PIPELINE_SCRIPT!r}")
    if command[command.index("--only-steps") + 1] != "3,5":
        failures.append("step selection is not the default '3,5'")
    return failures


def main() -> int:
    failures = check_pin()
    if failures:
        print("GNN pin check failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(f"registered GNN revision: {registered_revision()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

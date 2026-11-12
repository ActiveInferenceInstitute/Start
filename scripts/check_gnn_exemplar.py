"""Parse and type-check the pinned upstream GNN exemplar.

This is the networked half of the GNN conformance job. It installs the pinned
upstream package from ``.github/gnn-pin.json`` into the active environment,
fetches the pinned ``input/gnn_files/basics/static_perception.md`` exemplar, and
runs the upstream parser, syntax validator, and type checker over it.

Requires network access. ``start-gate gnn`` is the offline half and does not
install or fetch anything.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN_PATH = ROOT / ".github" / "gnn-pin.json"
EXEMPLAR = "input/gnn_files/basics/static_perception.md"
RAW_URL = "https://raw.githubusercontent.com/{repository}/{revision}/{path}"
REQUIREMENTS = (
    "defusedxml",
    "psutil",
)


def load_pin() -> dict[str, str]:
    payload = json.loads(PIN_PATH.read_text(encoding="utf-8"))
    for field in ("repository", "revision"):
        if not str(payload.get(field) or "").strip():
            raise SystemExit(f"{PIN_PATH.relative_to(ROOT)}: missing {field!r}")
    return payload


def install_pinned_package(pin: dict[str, str]) -> None:
    spec = (
        "generalized-notation-notation @ "
        f"git+https://github.com/{pin['repository']}.git@{pin['revision']}"
    )
    subprocess.run(
        ["uv", "pip", "install", "--no-deps", *REQUIREMENTS, spec],
        cwd=ROOT,
        check=True,
    )


def main() -> int:
    pin = load_pin()
    install_pinned_package(pin)

    from gnn.parsers.basic import parse_gnn_formal, validate_gnn_syntax
    from gnn.type_checker import GNNTypeChecker

    from gnn import __version__

    url = RAW_URL.format(repository=pin["repository"], revision=pin["revision"], path=EXEMPLAR)
    with tempfile.TemporaryDirectory(prefix="start-gnn-") as output_dir:
        model = Path(output_dir) / Path(EXEMPLAR).name
        with urllib.request.urlopen(url, timeout=60) as response:
            model.write_bytes(response.read())

        parsed = parse_gnn_formal(model)
        if parsed is None or getattr(parsed, "parse_errors", None):
            raise SystemExit("pinned exemplar did not parse cleanly")
        valid, errors = validate_gnn_syntax(model.read_text(encoding="utf-8"))
        if not valid:
            raise SystemExit(f"pinned exemplar syntax errors: {errors!r}")

        model_dir = Path(output_dir) / "models"
        model_dir.mkdir()
        shutil.copy(model, model_dir / model.name)
        if not GNNTypeChecker().validate_gnn_files(model_dir, Path(output_dir)):
            raise SystemExit("GNN type checker rejected the pinned exemplar")

    print(json.dumps({"gnn-version": __version__, "result": "verified"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

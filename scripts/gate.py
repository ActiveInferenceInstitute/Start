"""Repository gate: one entry point, one command per arm.

Every arm here is the command the GitHub Actions workflows run: the workflows
call ``uv run start-gate <arm>`` instead of repeating command bodies, so a local
run and a hosted run cannot drift apart.

Arms are independently runnable. ``start-gate`` with no argument runs the
``fast`` arm; ``start-gate --list`` prints every arm with its exact argv.

The measured arm runtimes, test selection counts, and coverage total live in
``docs/_generated/gate-timings.json`` and its rendered companion
``docs/_generated/gate-timings.md``. ``start-gate measure`` writes both and the
``numbers`` arm fails when either is edited by hand.
"""

from __future__ import annotations

import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = ROOT / "docs" / "_generated"
TIMINGS_JSON = GENERATED_DIR / "gate-timings.json"
TIMINGS_MD = GENERATED_DIR / "gate-timings.md"
SCHEMA = "start-gate-timings/v1"
FIXTURE = "{fixture_dir}"
NETWORK_ARMS = frozenset({"gnn-exemplar"})

# `uv run start-gate` puts the locked interpreter on the path; keep every arm on
# that interpreter so a bare `python scripts/gate.py` cannot pick another.
PY = sys.executable

COLLECT_SELECTIONS: dict[str, tuple[str, ...]] = {
    "all": (),
    "fast": ("-m", "not slow and not network and not integration"),
    "slow": ("-m", "slow"),
    "integration": ("-m", "integration"),
    "network": ("-m", "network"),
}
COLLECTED = re.compile(r"(\d+)(?:/\d+)? tests? collected")
COVERAGE_TOTAL = re.compile(r"^TOTAL\b.*?(\d+(?:\.\d+)?)%")


@dataclass(frozen=True)
class Arm:
    """One independently runnable unit of the gate."""

    summary: str
    commands: tuple[tuple[str, ...], ...]


ARMS: dict[str, Arm] = {
    "lint": Arm(
        "Ruff, Black, and shell syntax",
        (
            (PY, "-m", "ruff", "check", "."),
            (PY, "-m", "black", "--check", "."),
            ("bash", "-n", "run.sh", "run_docs.sh", "src/setup.sh"),
        ),
    ),
    "types": Arm(
        "mypy over src, scripts, and learning",
        ((PY, "-m", "mypy", "src", "scripts", "learning", "--ignore-missing-imports"),),
    ),
    "fast": Arm(
        "Selected tests: not marked slow, network, or integration",
        ((PY, "-m", "pytest", *COLLECT_SELECTIONS["fast"], "-q"),),
    ),
    "full": Arm(
        "Full suite with the 80% branch-aware coverage floor",
        (
            (
                PY,
                "-m",
                "pytest",
                "--cov=src",
                "--cov-branch",
                "--cov-report=term-missing",
                "--cov-fail-under=80",
                "-q",
            ),
        ),
    ),
    "docs": Arm(
        "Strict MkDocs build plus configuration and local-link validation",
        (
            (PY, "-m", "mkdocs", "build", "--strict"),
            (PY, "-m", "scripts.validate_repository"),
        ),
    ),
    "numbers": Arm(
        "Generated gate-timings document matches its generator and this registry",
        ((PY, "-m", "scripts.gate", "check-docs"),),
    ),
    "gnn": Arm(
        "Pinned GNN registration and orchestrator tests",
        (
            (PY, "-m", "scripts.check_gnn_pin"),
            (PY, "-m", "pytest", "tests/test_gnn_runner.py", "-q"),
        ),
    ),
    "gnn-exemplar": Arm(
        "Parse and type-check the pinned upstream GNN exemplar (requires network)",
        ((PY, "-m", "scripts.check_gnn_exemplar"),),
    ),
    "artifacts": Arm(
        "Artifact provenance, output contracts, and offline fixture replay",
        (
            (
                PY,
                "-m",
                "scripts.audit_artifacts",
                "--check",
                "--baseline",
                "data/artifact-manifests/current.json",
            ),
            (PY, "-m", "scripts.validate_outputs", "--check"),
            (
                PY,
                "-m",
                "scripts.regenerate_offline_fixtures",
                "--output-dir",
                FIXTURE,
                "--run-id",
                "gate-fixture",
                "--json",
            ),
        ),
    ),
    "smoke": Arm(
        "CLI help and loopback GUI endpoint smoke",
        (
            (PY, "-m", "learning.curriculum_creation.generate_custom_curriculum", "--help"),
            (PY, "-m", "learning.curriculum_creation.generate_curriculum_gui", "--help"),
            (PY, "-m", "src.repos.clone_repo", "--help"),
            (PY, "-m", "scripts.smoke_gui"),
        ),
    ),
    "audit": Arm(
        "Dependency vulnerability audit",
        ((PY, "-m", "pip_audit", "--strict"),),
    ),
    "lock": Arm(
        "Lockfile freshness",
        (("uv", "lock", "--check"),),
    ),
    "smoke-macos": Arm(
        "macOS hardening and visualization smoke tests",
        (
            (
                PY,
                "-m",
                "pytest",
                "tests/test_core_hardening.py",
                "tests/test_visualization_runner.py",
                "-q",
            ),
        ),
    ),
}

HELP = """usage: start-gate [ARM | measure | check-docs]

Run one gate arm. The same arms are what .github/workflows calls, so a local
run and a hosted run execute one command.

  start-gate                 run the default arm (fast)
  start-gate lint            ruff, black, shell syntax
  start-gate types           mypy
  start-gate fast            tests not marked slow/network/integration
  start-gate full            full suite, 80% branch-aware coverage floor
  start-gate docs            mkdocs build --strict + config/link validation
  start-gate numbers         verify the generated timing document
  start-gate gnn             pinned GNN registration + orchestrator tests
  start-gate gnn-exemplar    pinned exemplar parse (requires network)
  start-gate artifacts       artifact provenance, output contracts, fixture
  start-gate smoke           CLI help and GUI endpoint smoke
  start-gate audit           dependency vulnerability audit
  start-gate lock            uv lock --check
  start-gate smoke-macos     macOS hardening and visualization smoke tests

  start-gate --list          list arms with their exact commands
  start-gate measure         re-measure arms and rewrite docs/_generated/
  start-gate check-docs      verify docs/_generated/ matches this file
"""


def render_command(command: Sequence[str]) -> str:
    """Render an argv for display without losing its exact quoting.

    The running interpreter is rendered as ``python`` so receipts and the
    generated timing document do not record one machine's virtualenv path.
    """

    return " ".join(shlex.quote("python" if part == PY else part) for part in command)


def render_actual(command: Sequence[str]) -> str:
    """Render the argv exactly as it will be executed."""

    return " ".join(shlex.quote(part) for part in command)


def _receipts() -> dict[str, list[str]]:
    return {name: [render_command(cmd) for cmd in arm.commands] for name, arm in ARMS.items()}


def _environment() -> dict[str, str]:
    env = dict(os.environ)
    env.setdefault("MPLBACKEND", "Agg")
    return env


def _expand(command: Iterable[str], fixture_dir: str) -> list[str]:
    return [fixture_dir if part == FIXTURE else part for part in command]


def _stream(argv: Sequence[str]) -> tuple[int, str]:
    """Run one command, echo its output, and return ``(code, output)``."""

    lines: list[str] = []
    process = subprocess.Popen(
        argv,
        cwd=ROOT,
        env=_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="", flush=True)
        lines.append(line)
    return process.wait(), "".join(lines)


def run_arm(name: str, *, quiet: bool = False) -> tuple[bool, float, list[int], str]:
    """Run one arm and return ``(passed, wall_seconds, exit_codes, output)``."""

    arm = ARMS[name]
    fixture_dir = tempfile.mkdtemp(prefix=f"start-gate-{name}-")
    started = time.perf_counter()
    codes: list[int] = []
    output = ""
    print(f"== {name}: {arm.summary}", flush=True)
    try:
        for command in arm.commands:
            argv = _expand(command, fixture_dir)
            print(f"   $ {render_actual(argv)}", flush=True)
            code, chunk = _stream(argv)
            codes.append(code)
            output += chunk
            if code != 0:
                break
    finally:
        shutil.rmtree(fixture_dir, ignore_errors=True)
    elapsed = time.perf_counter() - started
    passed = bool(codes) and codes[-1] == 0
    if not quiet:
        print(f"== {name}: {'PASS' if passed else 'FAIL'} ({elapsed:.1f}s)", flush=True)
    return passed, elapsed, codes, output


def collect_counts() -> dict[str, int]:
    """Count collected tests for the recorded marker selections."""

    counts: dict[str, int] = {}
    for label, selection in COLLECT_SELECTIONS.items():
        code, output = _stream(
            [PY, "-m", "pytest", "--collect-only", "-o", "addopts=", "-q", *selection]
        )
        match = COLLECTED.search(output)
        if match is None:
            counts[label] = 0 if code == 5 else -1
        else:
            counts[label] = int(match.group(1))
    return counts


def coverage_percent(output: str) -> float | None:
    """Read the coverage total out of a pytest coverage table."""

    for line in output.splitlines():
        match = COVERAGE_TOTAL.match(line.strip())
        if match is not None:
            return float(match.group(1))
    return None


def _host() -> dict[str, str]:
    try:
        uv = subprocess.run(
            ["uv", "--version"], cwd=ROOT, capture_output=True, text=True, check=False
        )
        uv_version = uv.stdout.strip() or "unavailable"
    except OSError:
        uv_version = "unavailable"
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "uv": uv_version,
    }


def _payload(
    arms: list[dict[str, Any]],
    measured: str | None,
    tests: dict[str, int] | None,
    coverage: float | None,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "measured": measured,
        "host": _host(),
        "tests": tests,
        "coverage_percent": coverage,
        "arms": arms,
    }


def _empty_payload() -> dict[str, Any]:
    receipts = _receipts()
    return _payload(
        [
            {
                "name": name,
                "summary": ARMS[name].summary,
                "commands": receipts[name],
                "wall_seconds": None,
                "exit_codes": [],
            }
            for name in ARMS
        ],
        None,
        None,
        None,
    )


def render_markdown(payload: dict[str, Any]) -> str:
    """Render the timing document from its machine-written payload."""

    host = payload.get("host", {})
    measured = payload.get("measured") or "not measured"
    lines = [
        "# Gate arm timings",
        "",
        "Generated by `uv run start-gate measure`. Do not edit this file; edit "
        "`scripts/gate.py` and re-run the measurement.",
        "",
        f"Measured at {measured} on {host.get('platform', 'unknown')} "
        f"({host.get('machine', 'unknown')}), Python {host.get('python', 'unknown')}, "
        f"{host.get('uv', 'unknown')}.",
        "",
        "One warm-environment run per arm on a single local machine. These are "
        "local observations, not scheduled-runner durations: the estate's GitHub "
        "Actions runs are billing-locked, so local runs are the only gate.",
        "",
    ]
    tests = payload.get("tests")
    if isinstance(tests, dict):
        lines.extend(
            [
                "## Test selection",
                "",
                "| Selection | Collected tests |",
                "| --- | --- |",
            ]
        )
        for label in COLLECT_SELECTIONS:
            if label in tests:
                lines.append(f"| `{label}` | {tests[label]} |")
        lines.append("")
    coverage = payload.get("coverage_percent")
    if coverage is not None:
        lines.extend(
            [
                "## Coverage",
                "",
                f"`full` arm total: **{coverage:.1f}%** (branch-aware, `--cov=src`).",
                "",
            ]
        )
    lines.extend(
        [
            "## Arms",
            "",
            "| Arm | Wall time (s) | Exit codes | Commands |",
            "| --- | --- | --- | --- |",
        ]
    )
    for arm in payload.get("arms", []):
        wall = arm.get("wall_seconds")
        wall_text = "not measured" if wall is None else f"{wall:.1f}"
        codes = ", ".join(str(code) for code in arm.get("exit_codes", [])) or "-"
        commands = "<br>".join(f"`{command}`" for command in arm.get("commands", []))
        lines.append(f"| `{arm.get('name')}` | {wall_text} | {codes} | {commands} |")
    lines.extend(
        [
            "",
            "`measure` writes this file and its `.json` source; the `numbers` arm "
            "fails when either is edited by hand or when the arm registry changes "
            "without a re-measurement.",
            "",
        ]
    )
    return "\n".join(lines)


def _write(payload: dict[str, Any]) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    TIMINGS_JSON.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    TIMINGS_MD.write_text(render_markdown(payload), encoding="utf-8")


def check_docs() -> int:
    """Verify the generated timing document against this file."""

    missing = [path for path in (TIMINGS_JSON, TIMINGS_MD) if not path.exists()]
    if missing:
        print(
            "missing generated timing files: "
            + ", ".join(str(path.relative_to(ROOT)) for path in missing)
            + "\nrun: uv run start-gate measure",
            file=sys.stderr,
        )
        return 1
    try:
        payload = json.loads(TIMINGS_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"{TIMINGS_JSON.relative_to(ROOT)}: invalid JSON: {exc}", file=sys.stderr)
        return 1
    problems: list[str] = []
    if payload.get("schema") != SCHEMA:
        problems.append(f"schema is {payload.get('schema')!r}, expected {SCHEMA!r}")
    recorded = {
        arm.get("name"): arm.get("commands", []) for arm in payload.get("arms", []) if "name" in arm
    }
    expected = _receipts()
    for name in ARMS:
        if name not in recorded:
            problems.append(f"arm {name!r} missing from the timing document")
        elif recorded[name] != expected[name]:
            problems.append(
                f"arm {name!r} commands drifted:\n"
                f"  recorded: {recorded[name]}\n  current:  {expected[name]}"
            )
    for name in recorded:
        if name not in ARMS:
            problems.append(f"timing document names an unknown arm: {name!r}")
    if render_markdown(payload) != TIMINGS_MD.read_text(encoding="utf-8"):
        problems.append(
            f"{TIMINGS_MD.relative_to(ROOT)} is not a faithful render of "
            f"{TIMINGS_JSON.relative_to(ROOT)}"
        )
    if problems:
        print("gate timing document check failed:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        print("run: uv run start-gate measure", file=sys.stderr)
        return 1
    print(f"gate timing document matches {len(ARMS)} arms")
    return 0


def measure(include_network: bool) -> int:
    """Run every arm once and rewrite the generated timing document."""

    if not TIMINGS_JSON.exists() or not TIMINGS_MD.exists():
        _write(_empty_payload())
    names = [name for name in ARMS if include_network or name not in NETWORK_ARMS]
    results: dict[str, tuple[bool, float, list[int], str]] = {}
    for name in names:
        results[name] = run_arm(name)
    receipts = _receipts()
    arms = [
        {
            "name": name,
            "summary": ARMS[name].summary,
            "commands": receipts[name],
            "wall_seconds": round(results[name][1], 1),
            "exit_codes": results[name][2],
        }
        for name in names
    ]
    coverage = coverage_percent(results["full"][3]) if "full" in results else None
    tests = collect_counts()
    _write(
        _payload(
            arms,
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            tests,
            coverage,
        )
    )
    failed = [name for name in names if not results[name][0]]
    if failed:
        print(f"measurement completed; failing arms: {', '.join(failed)}", file=sys.stderr)
        return 1
    print(f"measured {len(names)} arms -> {TIMINGS_MD.relative_to(ROOT)}")
    return 0


def print_arms() -> int:
    width = max(len(name) for name in ARMS)
    for name, arm in ARMS.items():
        print(f"{name.ljust(width)}  {arm.summary}")
        for command in arm.commands:
            print(f"{' ' * width}    {render_command(command)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        return 0 if run_arm("fast")[0] else 1
    head = args[0]
    if head in {"-h", "--help", "help"}:
        print(HELP, end="")
        return 0
    if head in {"-l", "--list", "ls"}:
        return print_arms()
    if head == "measure":
        return measure(include_network="--include-network" in args[1:])
    if head == "check-docs":
        return check_docs()
    if head in ARMS:
        return 0 if run_arm(head)[0] else 1
    print(f"unknown arm: {head}", file=sys.stderr)
    print(HELP, end="", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

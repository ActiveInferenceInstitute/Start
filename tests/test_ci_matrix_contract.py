"""Keep CI's advertised interpreter and required-job contracts explicit."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_matrix_sync_and_gate_select_the_same_python():
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    matrix = workflow["jobs"]["test"]
    assert matrix["strategy"]["matrix"]["include"] == [
        {"python-version": "3.11", "gate-arm": "fast"},
        {"python-version": "3.12", "gate-arm": "full"},
    ]
    steps = {step["name"]: step for step in matrix["steps"] if "name" in step}
    assert steps["Install locked project environment"]["run"] == (
        "uv sync --python ${{ matrix.python-version }} --all-extras --dev --locked"
    )
    assert steps["Test"]["run"] == (
        "uv run --no-sync --python ${{ matrix.python-version }} "
        "start-gate ${{ matrix.gate-arm }}"
    )
    assert (ROOT / ".python-version").read_text().strip() == "3.12"


def test_matrix_checks_the_actual_interpreter_before_the_gate():
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    steps = workflow["jobs"]["test"]["steps"]
    names = [step.get("name") for step in steps]
    assert names.index("Verify selected interpreter") < names.index("Test")
    check = steps[names.index("Verify selected interpreter")]["run"]
    assert check.startswith("uv run --no-sync --python ${{ matrix.python-version }} python -")
    assert 'expected = tuple(map(int, "${{ matrix.python-version }}".split(".")))' in check
    assert "assert sys.version_info[:2] == expected" in check
    assert 'assert Path(sys.prefix).resolve() == (Path.cwd() / ".venv").resolve()' in check
    assert "assert Path(sys.executable).parent.resolve()" in check


def test_rollup_keeps_all_existing_jobs_required():
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    jobs = workflow["jobs"]
    rollup = jobs["required-gate"]
    assert rollup["name"] == "test"
    assert set(rollup["needs"]) == set(jobs) - {"required-gate"}
    assert rollup["if"] == "${{ always() }}"
    assert all(not jobs[name].get("continue-on-error", False) for name in rollup["needs"])
    assert rollup["steps"][0]["run"] == (
        'jq -e \'length > 0 and all(.[]; .result == "success")\' <<<"$RESULTS"'
    )

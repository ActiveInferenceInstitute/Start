# Review Log — 2026-08-02

Docs-deep review pass of the START repository (public
ActiveInferenceInstitute/Start, default branch `main`).

## Phase 0 — Preflight

- Fetched origin; working tree clean at `73471f2` before the pass.
- Inventoried: root README/AGENTS/here.md/TODO.md, `docs/` (25 files +
  `other/`), `learning/` guides, `src/` per-module README/AGENTS pairs,
  `tests/`, `examples/` (efe, vfe), `.aii/`, `.github/workflows/`
  (ci, release-gate, security, codeql, deploy_docs), `mkdocs.yml`,
  `pyproject.toml`, `.env.example`.

## Phase 1 — Mega-deep docs review

Validation evidence:

- `uv run python -m scripts.validate_repository` — PASS (178 tracked
  JSON/YAML/TOML + 197 authored text files).
- `uv run mkdocs build --strict` — PASS (CI docs gate green).
- Whole-repo relative-link + GFM anchor scan over 68 authored Markdown
  files — 0 missing file targets, 0 missing anchors.
- CLI flag cross-check against `--help` output for every documented
  entrypoint — found one broken flag family (see below).

Findings by severity (full detail in the scoped TODO.md section):

- Major: `learning/` docs document `--input`/`--output` flags that the
  canonical `start-curriculum` CLI rejects (exit 2) — commands as written
  fail; correct dir-override flags are `--visualizations-dir`,
  `--translation-dir`, `--curriculum-dir`.
- Major: `src/` technical references omit the `pipeline/` module (the
  canonical orchestrator) entirely; `src/config/` description stale.
- Major (privacy): `.aii/SKILL.md` — tracked file in a public repo —
  contained a local developer path; sanitized to a generic clone
  instruction.
- Medium: `docs/clones.md` ecosystem list missing `gnn` + `cerebrum` and
  wrong clone destinations for RxInferExamples.jl/ActiveInference.jl
  (code keys `rxinfer`/`activeinference`); `docs/data_outputs.md` naming
  claims contradict real artifact filenames (display names, not stable
  IDs); `docs/docs_and_deployment.md` describes an Actions workflow as
  "alternative" that already exists (`deploy_docs.yml`); `docs/environment.md`
  mypy command stale vs CI (now full scope); `docs/curriculum_gui.md`
  stdlib overclaim; README Zenodo DOI inconsistency; FAQ duplicate
  question; relative-path drift (`docs/`-prefixed paths inside `docs/`).
- Minor: duplicate H1 in docs/README.md, bold-marker typo in
  docs/index.md, tests/AGENTS.md duplicate entries, examples/AGENTS.md
  off-by-one line counts, learning README dependency list (pydantic not
  a project dep), `.env.example` placeholder model names, here.md LaTeX
  delimiters (`\[...\]`/`\(...\)` do not render on GitHub).

## Phase 3 — Implementation

Commits (chronological; each gate-validated):

1. `docs: sanitize local path in .aii/SKILL.md (public repo)`
2. `docs: fix CLI flags in learning guides to canonical start-curriculum`
3. `docs: correct environment mypy scope, GUI claim, DOI, and docs hub`
4. `docs: align clone map, data-output naming, and deployment docs`
5. `docs: document src/pipeline in source references`
6. `docs: fix test/example inventories and learning dependency list`
7. `docs: align env example, stable commands, and GitHub math delimiters`
8. `docs: scope and close out docs deep review in TODO.md`

## Phase 4 — Final verification

- `uv run python -m scripts.validate_repository` — PASS
- `uv run mkdocs build --strict` — PASS
- Re-ran link/anchor scan after edits — 0 broken targets
- `uv run pytest -q` — not re-run in full (code untouched; only docs and
  one tracked docs/config-adjacent file changed). State explicitly: no
  code paths modified, so the heavy suite was not re-executed.
- Pushed to `origin/main`; working tree clean.

Skipped: full pytest suite and provider tests (no code changes in this
pass; docs-only). No Julia/LaTeX build surfaces in this repo.

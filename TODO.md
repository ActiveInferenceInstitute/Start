# START Forward Execution Backlog

This is the sole canonical backlog for future work. It contains unchecked
work that remains after the deepest red-team review and hardening pass
(2026-08-01).

- Status: active; release `v1` was cut on 2025-09-03 (tag `v1` on commit
  `7c5452b`, still an ancestor of `main`); `pyproject.toml` version is `0.2.0`
- Last reviewed: 2026-11-12 (backlog truth pass; every item re-verified against
  the tracked tree and the recorded gate measurement at this head, completed
  items moved to the dated section below); prior review 2026-11-11
  (documentation pass 3; repository defects below recorded, not fixed); prior
  review 2026-08-02 (docs-deep review pass; Minor/Medium findings implemented)

## Known repository defects (recorded 2026-11-11; two added 2026-11-12; not fixed)

Verified against the tracked tree at this head. Each needs an owner decision
before it is changed; none was modified by either review pass.

- [ ] `examples/vfe/node_modules/` is committed (631 tracked files) even though
  the root `.gitignore` lists `examples/vfe/node_modules/`. Git ignore rules do
  not affect already-tracked files, so the vendored tree stays in the index.
  Owner decision: untrack the directory (keep it ignored) and rely on
  `npm install` per `examples/vfe/README.md`, or retain it intentionally.
- [ ] `examples/package-lock.json` records no dependencies
  (`{"name": "examples", "lockfileVersion": 3, "requires": true, "packages": {}}`)
  with no sibling `examples/package.json`. Owner decision: remove it, or add the
  missing `examples/package.json` that it would describe.
- [ ] `examples/vfe.jsx` is duplicated verbatim at the `examples/` root and in
  `examples/vfe/vfe.jsx` (both 56,986 bytes). `examples/README.md` and
  `examples/AGENTS.md` document only the `examples/vfe/` copy. Owner decision:
  remove the unused root duplicate or document why it exists.
- [ ] `coverage.json` is tracked at the repository root (387,508 bytes) and its
  `meta` block records `"timestamp": "2026-07-18T13:33:29"`, while the measured
  total at this head is 89.1% (`docs/_generated/gate-timings.json`). No gate
  arm, workflow, script, or document reads it, and `.gitignore` ignores
  `.coverage`/`coverage.xml` but not `coverage.json`, so a `--cov-report=json`
  run silently rewrites a stale committed file. Owner decision: delete it and
  add the pattern to `.gitignore`, or make the gate consume it.
- [ ] `pyproject.toml` sets `[tool.ruff] target-version = "py310"` while
  `requires-python = ">=3.11"` and the documented matrix is 3.11/3.12
  (`docs/environment.md`); `[tool.black] target-version` already lists
  `py311`/`py312`. The linter therefore grades against a floor two minor
  versions below the package's declared floor. Owner decision: set
  `target-version = "py311"` and re-run `start-gate lint`.

## Dependency pins (verified 2026-11-12)

- **GNN is pinned at `v5.0.3`, not the estate's `v5.1.0`.** `.github/gnn-pin.json`
  records `ActiveInferenceInstitute/Generalized_Notation_Notation` at
  `8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1` (`v5.0.3`), and
  `src/repos/cloning.py` hard-codes the same revision for the `gnn` clone target
  with the comment "GNN v5.0.3; the shared canonical revision for the education
  workstream". Start does not import the upstream GNN package:
  `src/gnn/main.py` locates a GNN checkout and runs its pipeline with that
  checkout's own interpreter, so the estate's `v5.1.0` importer migration does
  not apply here and the older pin is a deliberate choice rather than an
  unfinished migration. If that decision changes, the
  repository maintainer updates `.github/gnn-pin.json` and
  `src/repos/cloning.py` together, then re-runs `start-gate gnn` and
  `start-gate gnn-exemplar` (the exemplar arm needs network).
- **`pymdp` carries no version pin, and is not on 1.0.5.** `pymdp` is only a
  clone target (`src/repos/cloning.py`: `docxology/pymdp`, branch `textbook`);
  it is absent from `pyproject.toml` dependencies and from `uv.lock`, and no
  module under `src/`, `scripts/`, or `learning/` imports it (only generated
  curriculum text under `data/` mentions it). Owner: repository maintainer, if
  a versioned dependency is ever wanted.

## Education contract (blocked outside this repository)

- [ ] **Authored curriculum content does not exist in this repository.** Start
  generates curricula from provider responses; every committed curriculum under
  `data/written_curriculums/`, `data/translated_curriculums/`, and
  `data/visualizations/` is generated output carrying a run timestamp. The
  authored tree (`data/prompts/`, `data/config/`, `docs/`, `learning/`, `src/`)
  contains no learning-objectives artefact, no glossary term list, and no
  learner plan: `git grep -i glossary` matches only the prompt template
  `data/prompts/translation.md` and generated output under `data/`. Until that
  authored content exists, no Education-contract bundle can be emitted from
  this repository and the migration cannot start here.
  Owner: the Institute's curriculum/education lead supplies the objectives,
  glossary terms, and learner plan; the repository maintainer then wires them
  into the generator. Blocked outside this repository; no code change here can
  unblock it.

## Docs deep review (2026-08-02)

Scoped and implemented during the mega-deep documentation pass. Severity
definitions: **Minor** = typo, broken link, formatting; **Medium** = stale
section rewrite, doc restructure, added missing guide; **Major** = large doc
system overhaul or cross-cutting refactor.

### Major

- [x] ✓ Remove a local developer path from `.aii/SKILL.md` (tracked file in
  a public repo); replaced with a generic clone instruction.
  (commit `docs: sanitize local path in .aii/SKILL.md (public repo)`)
- [x] ✓ Fix `learning/` guides documenting `--input`/`--output` flags that
  `start-curriculum` rejects (exit 2); the canonical CLI uses
  `--visualizations-dir`, `--translation-dir`, `--curriculum-dir`.
  (commit `docs: fix CLI flags in learning guides to canonical start-curriculum`)
- [x] ✓ Document the `src/pipeline/` module (canonical orchestrator) in
  `src/AGENTS.md` and `src/README.md`; refresh the stale `src/config/`
  description (now `catalog.py` + `schemas.py` + `languages.py`).
  (commit `docs: document src/pipeline in source references`)

### Medium

- [x] ✓ `docs/environment.md`: mypy command now full-scope
  (`mypy src scripts learning --ignore-missing-imports`), matching CI;
  fix `docs/TESTING.md` relative path; align model env defaults with
  `src/perplexity/clients.py`.
- [x] ✓ `docs/curriculum_gui.md`: remove the "only the Python standard
  library" overclaim (GUI imports project pipeline modules).
- [x] ✓ `README.md`: unify Zenodo DOI (badge/citation use
  `10.5281/zenodo.17047617`; inline text said `...19`).
- [x] ✓ `docs/clones.md`: add missing `gnn` and `cerebrum` repositories;
  correct clone destinations to the code keys (`rxinfer`,
  `activeinference`) and the after-cloning structure tree.
- [x] ✓ `docs/data_outputs.md`: research filenames use display names
  (e.g. `Barry Bonds_research_20250903.json`), not stable IDs; stable IDs
  appear in diagrams/manifests.
- [x] ✓ `docs/docs_and_deployment.md`: point at the existing
  `.github/workflows/deploy_docs.yml` instead of describing an Actions
  workflow as a to-be-added alternative.
- [x] ✓ `docs/FAQ.md`: merge the duplicated "Where do outputs go?" entry.
- [x] ✓ `learning/curriculum_creation/README.md`: correct Input lines
  (config-driven), dependency list (drop `pydantic`, `pathlib`), and
  `--input`/`--output` CLI examples.
- [x] ✓ `learning/curriculum_creation/USAGE_GUIDE.md`: fix `--input`/
  `--output` examples and the broken `an#` H1.
- [x] ✓ `docs/AGENTS.md` (docs hub list): add `methods.md`, `manuscript.md`,
  `operations.md`, `curriculum_gui.md` to the file index.

### Minor

- [x] ✓ `docs/README.md`: remove duplicate H1 (`# START Documentation —
  README` vs `# START documentation`).
- [x] ✓ `docs/index.md`: fix `** Professional Domains**` bold-marker typo;
  align the inferant-stream link label with its relative path.
- [x] ✓ `docs/getting_started.md`, `docs/pipeline.md`,
  `docs/environment.md`: `docs/`-prefixed intra-doc paths are wrong from
  inside `docs/`; use relative names.
- [x] ✓ `docs/TESTING.md`: annotate the `--cov-fail-under=80` example as
  the matrix baseline (release floor is 90).
- [x] ✓ `docs/conventions.md`: use `./run_docs.sh --serve` consistently.
- [x] ✓ `tests/AGENTS.md`: remove duplicate `test_repos_cloning.py` /
  `test_run_script_integration.py` entries.
- [x] ✓ `examples/AGENTS.md`: fix off-by-one line counts for `vfe.jsx`
  (1180) and `vfe-compiled.html` (9403).
- [x] ✓ `AGENTS.md` root: complete the stable-commands list
  (`start-clone`, `start-curate-artifacts`, `start-run-history`).
- [x] ✓ `.env.example`: replace `default_model_name` placeholders with the
  real defaults used by `src/perplexity/clients.py`.
- [x] ✓ `here.md`: use `$$`/`$` math delimiters so equations render on
  GitHub (backslash delimiters are not rendered).

### Open / deferred

- None from this pass. The remaining TODO sections below (P0–P3 and the
  Major deferrals) are unchanged and remain the forward backlog.


## P0 — Release blockers

None open. The artifact boundary and the provider matrix moved to the
2026-11-12 completed section below. What still blocks a release is one
publication gate each, tracked where it is worked: the provenance floor in P1
and the coverage floor in P2.

## P1 — Data and product readiness

- [ ] Human-review the generated-artifact audit. The recorded baseline at this
  head is unchanged: 687 files, 1 duplicate-content group, and 642 without
  provenance after excluding repository guidance and run-state files
  (`data/artifact-manifests/current.json`). Retain a small canonical example
  set, archive or remove unexplained timestamped duplicates, and make the
  curated manifest reproducible without deleting user-owned evidence. Owner:
  repository maintainer — this is a human retention decision, and
  `uv run python -m scripts.audit_artifacts --check --fail-on-unprovenanced`
  (the release floor in `.github/workflows/release-gate.yml`) is the gate that
  must pass once the debt is cleared.
- [ ] Add CLI-argv tests for `--dry-run` and `--estimate-cost`
  (`learning/curriculum_creation/generate_custom_curriculum.py:1551-1556`); the
  only current dry-run coverage is at orchestrator/runner level
  (`tests/test_production_hardening.py:1111`,
  `tests/test_gnn_runner.py:383`). The rest of the earlier list is covered:
  JSON output and exit codes by
  `test_cli_json_failure_is_bounded_and_machine_readable` and
  `test_gui_entrypoint_has_stable_argument_failure_code`, resume by
  `test_pipeline_dependencies_resume_and_optional_failures`, budget refusal by
  `test_pipeline_budget_stops_before_downstream_stage_and_does_not_publish_failures`,
  authenticated remote binding by
  `test_gui_remote_binding_requires_explicit_authentication`, and redaction by
  `test_structured_logging_redacts_sensitive_values`. Owner: whoever adds the
  tests; nothing external blocks this.

## P2 — Public release gates

- [ ] Raise branch-aware coverage from the recorded 89.1%
  (`docs/_generated/gate-timings.json`, measured `2026-11-12T13:22:55Z`) to the
  90% release floor, and add per-module floors for every destructive
  repository/path operation. The two floors differ today: the CI `full` arm
  enforces `--cov-fail-under=80` (`scripts/gate.py`) while
  `.github/workflows/release-gate.yml` enforces `--cov-fail-under=90`, so the
  release floor is currently unmet. Owner: repository maintainer. Neither floor
  has hosted evidence, because the estate's Actions runs are billing-locked.
- [ ] Get a recorded green run of the Python 3.11/3.12 matrix and the
  `macos-smoke` job. The configuration exists — `.github/workflows/ci.yml` runs
  `fast` on 3.11, `full` on 3.12, and `macos-smoke` (`lock` plus
  `smoke-macos`); `docs/environment.md` documents 3.11/3.12; all ten console
  entry points are listed in `AGENTS.md`. What is missing is evidence: the
  estate's Actions runs are billing-locked, so neither job has a recorded green
  hosted run. Owner: whoever holds the organization billing/runner decision;
  local arm output is the interim evidence.
- [ ] Complete formal security review, secret-scan review, dependency audit
  triage, static analysis triage, and release threat-model sign-off. In place
  today: the `audit` arm (`pip-audit --strict`) and
  `.github/workflows/codeql.yml`. Missing: no `SECURITY.md`, no secret-scan
  configuration or scan record, and no triage or threat-model artefact in the
  repository. Owner: repository maintainer with a reviewer; CodeQL results are
  also unobservable while Actions runs are billing-locked.
- [ ] Run one explicitly budgeted live pilot for one domain, one entity, and
  one language; require human review of its manifest and artifacts before
  publication. Owner: release owner; needs provider credentials and the human
  review the item names.

## P3 — Post-release product exploration

None of these is blocked; each needs an owner decision from the repository
maintainer before it becomes work.

- [ ] Evaluate provider plugins and model-independent runtime extensions.
- [ ] Evaluate richer interactive visualizations, LMS exports, and
  progress-based personalization with consent and human review.
- [ ] Evaluate community configuration contributions and knowledge-graph
  integration.
- [ ] Evaluate automated assessment only with evidence, review, and refusal
  paths defined.
- [ ] Evaluate mobile and AR/VR delivery after the core release contract is
  stable.

## Major — Scoped (deferred) — validated but intentionally NOT implemented

None currently. The one quality Major (mypy debt) was resolved in the
2026-08-01 comprehensive pass and is now enforced in CI.

### Documented deferrals (validated but deliberately NOT modified this pass)

These were validated and intentionally left unchanged after a review decision;
they are documented here so the reasoning is not lost.

- **Curriculum generation is deliberately transactional (all-or-nothing).**
  `src/perplexity/curriculum.py` raises without writing any output when any
  section fails, so an incomplete curriculum is never mistaken for a complete
  one. This is pinned by `test_core_hardening.py::test_curriculum_generation_`
  `_is_transactional`. The earlier "preserve partial sections" suggestion was
  evaluated and REJECTED because it contradicts this intentional, tested
  guarantee.
- **Read-side symlink hardening is target-only.** `src/common/io.py`
  `read_text`/`read_json` reject a symlinked *target* file but intentionally
  allow symlinked *parents*, because the repository is documented to run under
  symlinked install/clone paths (monorepo workspaces); rejecting parent
  symlinks would break those legitimate installs. Writes still reject both.
- `src/perplexity/entity.py` `extract_entity_description` falls back to the
  full input when no `Description:` line exists; existing tests pin this.

## Completed / Closed (2026-11-12 backlog truth pass)

Verified against tracked files at this head. Nothing here rests on a hosted
run, because the estate's Actions runs are billing-locked.

- **Source/test/generated-artifact boundary recorded and enforced.** The
  boundary is the roots list in `data/artifact-manifests/current.json`
  (`data/audience_research`, `data/domain_research`, `data/entity_research`,
  `data/translated_curriculums`, `data/visualizations`,
  `data/written_curriculums`) and the `artifacts` arm runs
  `scripts.audit_artifacts --check --baseline data/artifact-manifests/current.json`,
  `scripts.validate_outputs --check`, and the offline fixture replay. The
  retired "before the first release commit" framing was wrong: release `v1` was
  cut on 2025-09-03.
- **Provider concurrency, cancellation, usage/cost, structured logging, and the
  failure matrix are covered by tests.** `tests/test_production_hardening.py`
  covers the `RequestLimiter` concurrency cap, cancellation interrupting
  backoff, provider-reported cost and usage accounting, structured-log and
  credential redaction, retry exhaustion, `Retry-After` parsing (including the
  HTTP-date form), and payload validation.
  `tests/test_release_edge_matrix.py::test_provider_failure_matrix_redacts_secrets_and_honors_cancellation`
  covers 429 retry plus redaction plus cancellation, and
  `tests/test_release_edge_matrix.py::test_pipeline_contracts_usage_and_run_artifacts_are_serializable`
  covers usage normalization and aggregation at the pipeline-contract layer.
  Budget refusal is covered by
  `test_pipeline_budget_stops_before_downstream_stage_and_does_not_publish_failures`.
  Both adapters run through `ProviderAdapter`/`complete_chat_result`;
  `tests/test_clients.py` asserts the Perplexity and OpenRouter base URLs and
  the credential requirement.

## Completed / Closed (2026-08-01 comprehensive + wiring pass)

Additional improvements landed after the first comprehensive pass (all four
gates green: pytest exit 0, ruff clean, black clean, mypy 0):

- **mypy now enforced in CI.** The `ci.yml` type-check step was expanded from a
  small subset (`src/pipeline src/config/schemas.py --follow-imports=skip`) to
  the full clean scope (`mypy src scripts learning`). This prevents regression
  of the now-zero typing debt.
- **Model fallback + cost rates wired live through the pipeline.** The features
  are no longer dormant in the API:
  - `PerplexityConfig`/`OpenRouterConfig` gained `fallback_models` and
    `input/output_cost_per_million` fields (validated) plus a `to_chat_policy()`
    helper.
  - `CurriculumConfig` gained `perplexity_fallback_models`,
    `openrouter_fallback_models`, and the four cost-rate overrides (validated).
  - `domain`, `entity`, `curriculum`, and `translation` provider paths thread
    `fallback_models` and cost rates into `ChatPolicy`, so a model-level failure
    now falls back to the next configured model and cost overrides reach usage
    accounting.
  - New tests cover `to_chat_policy` mirroring and `CurriculumConfig`
    validation; the existing negative-cost error contract is preserved.

The earlier comprehensive + red-team passes (StageResult partial-failure,
skip_existing freshness, post-clone git hardening, prompt-injection data
framing, legacy `3_Intro` cleanup, schema/io/repos/GUI/system hardening)
remain complete as recorded below.

Implemented and verified (pytest, ruff, black, mypy all green) during the
comprehensive pass. This adds to the earlier red-team hardening:

- **mypy fully clean**: 0 errors across `src`, `scripts`, and `learning`
  (was ~150). Fixed the untyped orchestrator `self.results`, `Optional`-style
  issues, API/typing inference across repos/system/learning/scripts.
- **Model fallback** (`src/perplexity/clients.py`): `ChatPolicy.fallback_models`
  — on a model-level failure the client tries the next model before giving up;
  attempts are reported across the pool. Covered by a test.
- **Cost estimation wired** (`src/perplexity/clients.py`): documented
  default-cost lookup so the default OpenRouter path reports a non-zero
  estimated cost; explicit rates still win; unknown models stay honestly 0.
- **Prompt-injection data framing** (`src/common/prompts.py` + domain/entity/
  curriculum): untrusted research/entity/foundation content is wrapped in an
  explicit "treat strictly as data" boundary before reaching the model.
- **Legacy `3_Introduction_Visualizations.py`** reduced from ~725 lines of dead
  chart logic to a thin delegator to the canonical `src/visualization` runner.
- All earlier red-team fixes (StageResult partial-failure, skip_existing
  freshness, post-clone git hardening, schema/io/repos/GUI/system hardening).

Implemented and verified (pytest, ruff, black all green; no new mypy errors)
during the deep red-team pass. These are removed from the active backlog:

- **MAJOR (fixed): silent partial failure.** `StageResult.__post_init__`
  (`src/pipeline/contracts.py`) now re-assesses status after deriving item
  failures, so a stage containing a failed item reports `ok=False`; the
  pipeline no longer reports a run green on partial failure. Regression tests
  added; the existing test that encoded the buggy behavior was corrected.

- **MAJOR (fixed): stale `skip_existing` cache.** `process_research_directory_detailed`
  (`src/pipeline/stages.py`) now verifies the existing output's declared
  research/fep_actinf input hashes (sibling JSON) before skipping; a stale
  cache hit is regenerated instead of silently published as authoritative.

- **MAJOR (fixed): post-clone git hardening.** `update_repository` and
  `get_repository_status` (`src/repos/cloning.py`) now run git with committed
  hooks disabled (`-c core.hooksPath=/dev/null`, `--no-optional-locks`,
  `GIT_CONFIG_NOSYSTEM`), refuse repos whose `.git/config` enables
  hooks/filters/fsmonitor/url-rewrites, and use fetch + fast-forward merge
  instead of `pull`. Real-git behavior preserved and covered by tests.

- `perplexity/translation.py`: `skip_existing` now verifies the recorded
  `source_sha256` (regenerate when provably stale, legacy behavior preserved);
  failure messages no longer assume a colon prefix.

- `StageSpec`/runner early-stop records skipped required stages; resumed runs
  report real duration; usage/parsers/config schema hardening (see prior pass).

- Documentation drift fixed: `src/terminal/AGENTS.md` (typewriter_effect,
  glitch_effect, input_dialog signatures), `src/system/AGENTS.md` (dependency
  attributes), `docs/curriculum_gui.md` (no longer overclaims "only stdlib"),
  `learning/curriculum_creation/AGENTS.md` (deduplicated thin-delegator entry).
- `config/schemas.py`: reject CR/LF in source URLs.
- `config/catalog.py`: `output_exists` no longer raises on odd display names.
- `pipeline/schemas.py`: accept numeric `schema_version=1.0`; reject newline
  section names.
- `common/prompts.py`: log unresolved non-strict placeholders; return JSON-safe
  sorted variables list.
- `common/io.py`: symlink-target guard on reads; `list_files` glob confinement;
  `load_key_from_file` first-wins + empty-vs-absent.
- `common/paths.py`: `ensure_dir` delegates to hardened `ensure_directory`.
- `common/config.py`: CRLF-tolerant frontmatter.
- `common/env.py`: prefer repo-root `.env` with cwd fallback.
- `pipeline/history.py`: defensive sort + malformed timestamps handled.
- `pipeline/usage.py`: `total_tokens` recomputed when inconsistent.
- `pipeline/parsers.py`: fence-aware heading parse + duplicate-heading warning.
- `perplexity/clients.py`: empty-content retries; `http://` only for loopback
  hosts; JWT redaction; jitter-before-cap; dead-code removal; redacted
  client-construction errors.
- `repos/manager.py`: repo-name traversal refused on update/status/delete.
- `repos/cloning.py`: branch safety check; credential redaction; safe
  `cleanup_failed_clones` (staging/empty dirs only).
- `visualization/runner.py`: unreadable curriculum skipped, not run-aborting.
- `generate_curriculum_gui.py`: cross-site POST rejection (CSRF), broader path
  redaction, run-slot freed on any config exception.
- `system/reporting.py`: macOS memory fallback + explicit encodings.
- `system/dependencies.py`: generated synthetic artifact is now a warn-only
  content check, not a required dependency.
- `terminal/menu.py`: all-disabled menu leaves no phantom selection.
- `common/logging_utils.py`: JWT redaction pattern added.
- New tests: `tests/test_redteam_sweep.py` (schema/io/history/usage/parsers/
  runner/run_history coverage); `4_Translate_Introductions.py` cleaned to a
  thin delegator (dead block + `validate_languages` removed).

## Definition of done

An item is complete only when implementation, tests, documentation, generated
artifacts, and release validation are aligned. Remove completed items instead
of adding a history section; add newly discovered future work here.

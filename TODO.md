# START Forward Execution Backlog

This is the sole canonical backlog for future work. It contains unchecked
work that remains after the deepest red-team review and hardening pass
(2026-08-01).

- Status: active (no release cut yet)
- Last reviewed: 2026-08-02 (docs-deep review pass; Minor/Medium findings
  implemented; see the dated section below)

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

- [ ] Complete the dirty-worktree baseline review and record the final
  source/test/generated-artifact boundary before the first release commit.
- [ ] Add full-run provider concurrency and cancellation stress tests,
  structured-log integration assertions, and provider-reported usage/cost
  aggregation across the orchestrator and all staged entrypoints.
- [ ] Complete the provider failure matrix for every adapter path, including
  malformed payloads, 4xx/429/5xx, timeout, retry exhaustion, cancellation,
  usage accounting, and no-secret error/log output.

## P1 — Data and product readiness

- [ ] Human-review the generated-artifact audit (current snapshot: 687 files,
  1 duplicate-content group, and 642 without provenance after excluding
  repository guidance and run-state files), retain a small
  canonical example set, archive or remove unexplained timestamped duplicates,
  and make the curated manifest reproducible without deleting user-owned
  evidence.
- [ ] Expand CLI and GUI tests for JSON output, exit codes, dry-run,
  cost-estimate, resume, budget refusal, authenticated remote binding,
  cancellation, and sensitive-response redaction.

## P2 — Public release gates

- [ ] Raise branch-aware coverage above the now-passed 90.03% total gate and
  enforce higher floors for every destructive repository/path operation; the
  current repository orchestration module remains below that stricter floor.
- [ ] Validate the Python 3.10–3.12 matrix and macOS smoke path in CI, and
  document supported versions and package/console entrypoints.
- [ ] Complete formal security review, secret-scan review, dependency audit,
  static analysis triage, and release threat-model sign-off.
- [ ] Run one explicitly budgeted live pilot for one domain, one entity, and
  one language; require human review of its manifest and artifacts before
  publication.

## P3 — Post-release product exploration

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

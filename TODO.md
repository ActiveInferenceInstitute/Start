# START Forward Execution Backlog

This is the sole canonical backlog for future work. It contains unchecked
work that remains after the deepest red-team review and hardening pass
(2026-08-01).

- Status: active (no release cut yet)
- Last reviewed: 2026-08-01 (deep hostile red-team pass; Minor/Medium findings
  implemented; Major findings scoped below)

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

- [ ] **MAJOR (quality): mypy is now clean as of 2026-08-01** — `uv run mypy src
  scripts learning` reports 0 errors after the comprehensive typing pass
  (annotated orchestrator `self.results`, repos/system/learning annotations,
  API typing fixes). Keep mypy in CI to prevent regressions; add it to the
  workflow gate.

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
- Provider cost rates: `_DEFAULT_COST_PER_MILLION` provides documented
  list-price estimates for known default models (currently
  `anthropic/claude-3.5-sonnet` $3/$15); unknown models honestly report 0.0.
  Exact spend should come from provider-reported actual cost or explicit
  `ChatPolicy` rates.

## Completed / Closed (2026-08-01 comprehensive pass)

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

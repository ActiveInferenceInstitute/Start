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

These are the MAJOR findings from the deep hostile review. Implementation is a
deliberate, reviewed decision; items here remain open and are not auto-applied.

- [ ] **MAJOR (quality): mypy is not fully clean.**
  `uv run mypy src scripts learning` still reports a large number of errors
  across ~17 files (e.g. `no_implicit_optional` in learning scripts, `Any | None`
  assignments in `src/system/environment.py`, `base_dir: Path | str` union errors
  in `src/repos/manager.py`, unannotated locals). Conflicts with the
  `require_types_for_public_functions` rule in `.cursorrules`. Not the CI gate,
  but must be resolved before release. Fix: correct the easy
  `no_implicit_optional` cases first, then the remaining annotations, and add
  mypy to CI. (A full clean was deliberately not rushed in the 2026-08-01 pass to
  avoid introducing regressions ahead of a release-label push.)

### Documented deferrals (validated but deliberately not modified this pass)

The following non-Major items were validated but intentionally left for an
explicit human decision (they trade risk against correctness and should be
decided on before release, not auto-applied):

- `src/perplexity/clients.py` `estimated_cost_usd` is computed correctly but is
  always `0.0` because no caller sets `input/output_cost_per_million`. Wiring a
  default per-model pricing table risks shipping stale/fabricated prices; the
  computation is now pinned by a test.
- No model-fallback list exists in `src/perplexity/clients.py`; a model-level
  error hard-fails the pipeline. Adding a fallback list is a feature change.
- Research prompts embed untrusted domain/entity/FEP file content unsanitized
  (`src/perplexity/domain.py:182`, `entity.py:166`, `curriculum.py:441`); a
  hostile source file could steer the model. Requires delimiters + a
  data-not-instruction directive.
- `src/perplexity/curriculum.py:439-504` discards the whole curriculum when one
  section fails; saving partial sections + a failure manifest needs an
  orchestration change.
- `learning/curriculum_creation/3_Introduction_Visualizations.py` retains
  ~600 lines of legacy chart logic bypassed by the canonical `src/visualization`
  path; deleting is large and needs a dedicated pass.
- `src/common/io.py` `read_text`/`read_json` reject only a symlinked *target*
  (not symlinked parents) to stay compatible with symlinked installs.
- `src/perplexity/entity.py` `extract_entity_description` falls back to the
  full input when no `Description:` line exists; existing tests pin this
  behavior, so it is retained deliberately.

## Completed / Closed (2026-08-01 hardening pass)

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

# START Forward Execution Backlog

This is the sole canonical backlog for future work. It contains only
unchecked work that remains after the current hardening pass; completed or
historical checklists are intentionally removed.

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

## Definition of done

An item is complete only when implementation, tests, documentation, generated
artifacts, and release validation are aligned. Remove completed items instead
of adding a history section; add newly discovered future work here.

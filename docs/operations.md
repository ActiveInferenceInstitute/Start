# Operations and Release Evidence

START uses the filesystem as its operational record. This keeps the current
single-user scope inspectable without introducing a database.

## Run records

Each canonical run lives below the configured curriculum `.runs` directory and
contains a manifest plus stage checkpoints. The manifest records:

- run and configuration identity;
- required and optional stage outcomes;
- stable item identifiers and dependency skips;
- published artifact paths, hashes, sizes, and provenance;
- declared output roots and refusal of artifacts outside those roots;
- provider/model metadata, prompt versions, usage, and cost;
- quality results and failure summaries.

Inspect history with:

```bash
uv run start-run-history --root data/written_curriculums/.runs --json
```

Retention is plan-first. The command never removes anything unless both
`--prune` and `--apply` are supplied, and it only considers manifest-bearing
run directories:

```bash
uv run start-run-history \
  --root data/written_curriculums/.runs \
  --keep 10 --older-than-days 30 --prune --json
uv run start-run-history \
  --root data/written_curriculums/.runs \
  --keep 10 --older-than-days 30 --prune --apply --json
```

Review the first command’s JSON before applying the second. Never prune a run
that is the only copy of evidence required for a publication or incident
review.

## Cost and failure review

Usage is normalized to prompt tokens, completion tokens, total tokens,
estimated cost, observed provider cost, and request count. Estimates are not
spend. A budget refusal is persisted as a failed preflight manifest, and an
observed over-budget run cancels downstream work and refuses publication.

For machine-readable operational output:

```bash
START_LOG_FORMAT=json uv run start-curriculum \
  --non-interactive --offline --dry-run --run-id ops-check --json
```

Logs redact common API-key and bearer-token forms. Prompts and provider error
body text are not used as exception messages.

## Release evidence sequence

Run the following in order and preserve the outputs for review:

```bash
uv run python -m scripts.validate_repository
uv run start-audit-artifacts --check --json
uv run start-validate-outputs --check
uv run start-regenerate-offline --output-dir /tmp/start-release-fixture --json
uv run pytest --cov=src --cov-branch --cov-report=term-missing -q
uv run mkdocs build --strict
uv run pip-audit --strict
```

The public-release gate additionally requires publication-mode content
validation, a complete provenance review, security sign-off, and human review
of any authorized live pilot. No local green check substitutes for those
human or external decisions.

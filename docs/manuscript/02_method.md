# Method

The methods protocol is recorded in [Methods and Evidence Protocol](https://github.com/ActiveInferenceInstitute/Start/blob/a825e8c13cc45196a048be76e4cc428719b8228b/docs/methods.md).
The first-principles function is to make reviewable artifacts, not to maximize
the number of generated files. The scientific method is applied as a sequence
of falsifiable engineering hypotheses, controlled offline fixtures, measured
quality outputs, and iterative repairs.

The primary unit of analysis is an artifact record. It contains a stable item
identity, producing stage, regular-file path, content hash, status, and
provenance. The primary unit of execution is a run manifest. It records the
configuration digest, stage results, provider and prompt metadata, usage,
quality status, errors, and artifact records.

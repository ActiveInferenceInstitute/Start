# Contribution and scope

The contribution is a compact operating contract for a single-user research
and curriculum workflow:

1. stable configuration and item identifiers;
2. dependency-aware stages (`acquire → prepare → process → parse → render`);
3. provider boundaries with bounded retries, cancellation, redaction, and
   usage telemetry;
4. quality and provenance gates before publication;
5. deterministic offline fixtures and hashed visualization bundles;
6. staged entrypoints that delegate to one canonical orchestration layer.

The system is not a multi-user platform, a fact-checking service, an automated
ethics decision-maker, or a substitute for domain-expert review.

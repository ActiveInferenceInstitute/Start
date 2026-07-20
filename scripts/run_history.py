"""Inspect and conservatively prune filesystem-backed START run history."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.pipeline.history import list_runs, prune_runs, retention_candidates, summarize_runs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, required=True, help="Directory containing run directories"
    )
    parser.add_argument("--keep", type=int, default=10)
    parser.add_argument("--older-than-days", type=int)
    parser.add_argument("--prune", action="store_true", help="Plan removal of retention candidates")
    parser.add_argument("--apply", action="store_true", help="Actually remove planned candidates")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)
    if args.apply and not args.prune:
        parser.error("--apply requires --prune")
    summaries = list_runs(args.root)
    candidates = retention_candidates(
        summaries,
        keep=args.keep,
        older_than_days=args.older_than_days,
    )
    removed = prune_runs(candidates, apply=args.apply) if args.prune else []
    payload = {
        "summary": summarize_runs(summaries),
        "runs": [summary.as_dict() for summary in summaries],
        "retention_candidates": [summary.as_dict() for summary in candidates],
        "removed": removed,
        "applied": args.apply,
    }
    if args.json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"{payload['summary']['run_count']} runs, "
            f"{payload['summary']['artifact_count']} artifacts, "
            f"{len(candidates)} retention candidates"
        )
        if args.prune:
            print("removed" if args.apply else "planned", len(candidates), "runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

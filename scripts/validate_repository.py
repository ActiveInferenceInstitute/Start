"""Validate tracked repository configuration and output manifests."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import tomllib
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_SUFFIXES = {".json", ".yaml", ".yml", ".toml"}
TEXT_SUFFIXES = {
    ".cfg",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
GENERATED_OR_THIRD_PARTY_PREFIXES = (
    "data/audience_research/",
    "data/domain_research/",
    "data/entity_research/",
    "data/translated_curriculums/",
    "data/visualizations/",
    "data/written_curriculums/",
    "examples/vfe/node_modules/",
)
GENERATED_OR_THIRD_PARTY_FILES = {"uv.lock"}
PROHIBITED_AUTHORED_TERMS = re.compile(
    r"\b(mock\w*|stub\w*)\b|\bsimulated?\s+(api|fixture|provider|request|test)",
    re.IGNORECASE,
)
LOCAL_MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
URL_SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:", re.IGNORECASE)


class UniqueKeyLoader(yaml.SafeLoader):
    """YAML loader that rejects duplicate mapping keys."""


def _construct_mapping(loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"duplicate YAML key: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return sorted(
        path
        for path in (Path(item) for item in result.stdout.decode().split("\0") if item)
        if (ROOT / path).exists()
    )


def is_generated_or_third_party(path: Path) -> bool:
    normalized = path.as_posix()
    return path.name in GENERATED_OR_THIRD_PARTY_FILES or normalized.startswith(
        GENERATED_OR_THIRD_PARTY_PREFIXES
    )


def tracked_config_files(paths: list[Path]) -> list[Path]:
    return sorted(path for path in paths if path.suffix.lower() in CONFIG_SUFFIXES)


def authored_text_files(paths: list[Path]) -> list[Path]:
    return sorted(
        path
        for path in paths
        if path.suffix.lower() in TEXT_SUFFIXES and not is_generated_or_third_party(path)
    )


def validate_file(path: Path) -> None:
    absolute = ROOT / path
    content = absolute.read_bytes()
    if not content.strip():
        raise ValueError("file is empty")
    suffix = path.suffix.lower()
    if suffix == ".json":
        json.loads(content)
    elif suffix in {".yaml", ".yml"}:
        yaml.load(content, Loader=UniqueKeyLoader)
    elif suffix == ".toml":
        tomllib.loads(content.decode("utf-8"))


def validate_authored_terms(path: Path) -> list[str]:
    failures: list[str] = []
    text = (ROOT / path).read_text(encoding="utf-8")
    for line_number, line in enumerate(text.splitlines(), start=1):
        if "OpenAI-compatible" in line:
            continue
        if "test_openai_compatible_completion_is_a_real_local_request" in line:
            continue
        if "PROHIBITED_AUTHORED_TERMS" in line:
            continue
        if path == Path("scripts/validate_repository.py") and "simulated?" in line:
            continue
        if PROHIBITED_AUTHORED_TERMS.search(line):
            failures.append(f"{path}:{line_number}: prohibited authored terminology")
        if "Languages/" in line and "stale Languages/ path" not in line:
            failures.append(f"{path}:{line_number}: stale Languages/ path")
    return failures


def _normalize_markdown_target(raw_target: str) -> str:
    target = raw_target.strip().strip("<>")
    if " " in target and not raw_target.strip().startswith("<"):
        target = target.split()[0]
    return target.split("#", 1)[0]


def validate_markdown_links(path: Path) -> list[str]:
    if path.suffix.lower() != ".md":
        return []
    failures: list[str] = []
    text = (ROOT / path).read_text(encoding="utf-8")
    for match in LOCAL_MARKDOWN_LINK.finditer(text):
        target = _normalize_markdown_target(match.group(1))
        if not target or target.startswith("#") or URL_SCHEME.match(target):
            continue
        candidate = ((ROOT / path).parent / target).resolve()
        try:
            candidate.relative_to(ROOT)
        except ValueError:
            failures.append(f"{path}: link escapes repository: {match.group(1)}")
            continue
        if not candidate.exists():
            failures.append(f"{path}: broken local link: {match.group(1)}")
    return failures


def main() -> int:
    failures: list[str] = []
    try:
        files = tracked_files()
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Unable to enumerate tracked files: {exc}", file=sys.stderr)
        return 1

    config_files = tracked_config_files(files)
    text_files = authored_text_files(files)

    for path in config_files:
        try:
            validate_file(path)
        except Exception as exc:
            failures.append(f"{path}: {exc}")

    for path in text_files:
        try:
            failures.extend(validate_authored_terms(path))
            failures.extend(validate_markdown_links(path))
        except UnicodeDecodeError as exc:
            failures.append(f"{path}: not valid UTF-8 text: {exc}")

    if failures:
        print("Repository validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(
        f"Validated {len(config_files)} tracked JSON/YAML/TOML files "
        f"and {len(text_files)} authored text files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

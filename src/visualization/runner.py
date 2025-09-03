from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import pandas as pd


def collect_curriculum_files(base_dir: str) -> List[Tuple[str, str]]:
    curriculum_dir = Path(base_dir)
    curriculum_dir.mkdir(parents=True, exist_ok=True)
    files: List[Tuple[str, str]] = []
    for curr_file in curriculum_dir.rglob("complete_curriculum_*.md"):
        files.append((curr_file.parent.name, str(curr_file)))
    return files


def generate_curriculum_metrics(
    curriculum_docs: List[str], entity_labels: List[str], output_dir: str
) -> None:
    metrics = []
    import re

    for i, curriculum in enumerate(curriculum_docs):
        words = len(curriculum.split())
        sections = len(re.findall(r"^#+\s+(.+)$", curriculum, re.MULTILINE))
        paragraphs = len(re.split(r"\n\s*\n", curriculum))
        metrics.append(
            {
                "Entity": entity_labels[i],
                "Total Words": words,
                "Sections": sections,
                "Paragraphs": paragraphs,
                "Words per Section": words / max(sections, 1),
                "Words per Paragraph": words / max(paragraphs, 1),
            }
        )
    df = pd.DataFrame(metrics)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    df.to_csv(Path(output_dir) / "curriculum_metrics.csv", index=False)


def run(input_root: str, output_root: str) -> None:
    from src.common.paths import inputs_and_outputs_root

    base_dir = Path(inputs_and_outputs_root()) / "Written_Curriculums"
    collected = collect_curriculum_files(str(base_dir))
    if not collected:
        return
    curriculums: list[str] = []
    labels: list[str] = []
    for entity, path in collected:
        try:
            curriculums.append(Path(path).read_text(encoding="utf-8"))
            labels.append(entity)
        except Exception:
            continue
    generate_curriculum_metrics(curriculums, labels, str(Path(output_root) / "metrics"))

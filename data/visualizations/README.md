# Visualizations

Visualization outputs including charts, diagrams, and metrics.

## Overview

This directory contains visualization outputs generated from curriculum
analysis, including PNG charts, Mermaid diagrams, JSON metrics, and the
provenance-bearing `visualization_manifest.json` bundle record.

## File Types

### PNG Charts
- Complexity analysis charts
- Learning objectives charts
- Section breakdown charts
- Technical content charts
- Metrics dashboard

### Mermaid Diagrams
- Learning flow diagrams
- Curriculum structure diagrams

### JSON Metrics
- `metrics/curriculum_metrics.json`: Detailed metrics data for all curricula
  (schema version, evidence status, and records)

## File Naming

**Entity-Specific Files** (stable IDs, no timestamps):
- `diagrams/{stable-item-id}_flow.mmd` - Entity-specific flow diagrams

**Global Aggregate Files** (no timestamps):
- `metrics/curriculum_metrics.json` - Aggregated metrics data
- `metrics/curriculum_metrics.csv` - Tabular metrics export
- `charts/curriculum_metrics.png` - Aggregate volume chart
- `diagrams/curriculum_structure.mmd` - Overall curriculum structure
- `visualization_manifest.json` - Input/output hashes and evidence boundary

**Chart Types**:
- `complexity_analysis`: Complexity analysis charts
- `learning_objectives`: Learning objectives visualization
- `section_breakdown`: Section breakdown charts
- `technical_content`: Technical content analysis

## Navigation

- [AGENTS.md](AGENTS.md) - File format and naming reference
- [../README.md](../README.md) - Data directory overview
- [../../docs/visualizations.md](../../docs/visualizations.md) - Visualization documentation

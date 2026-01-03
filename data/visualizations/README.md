# Visualizations

Visualization outputs including charts, diagrams, and metrics.

## Overview

This directory contains visualization outputs generated from curriculum analysis, including PNG charts, Mermaid diagrams, and JSON metrics files.

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
- `curriculum_metrics.json`: Detailed metrics data for all curricula (array of metadata objects)

## File Naming

**Entity-Specific Files** (no timestamps):
- `{entity}_{type}.png` - Entity-specific charts (e.g., `Barry Bonds_complexity_analysis.png`)
- `{entity}_flow.mmd` - Entity-specific flow diagrams (e.g., `Coffee Roasting_flow.mmd`)

**Global Aggregate Files** (no timestamps):
- `curriculum_metrics.json` - Aggregated metrics data for all curricula
- `curriculum_metrics.png` - Aggregated metrics dashboard chart
- `curriculum_structure.mmd` - Overall curriculum structure diagram

**Chart Types**:
- `complexity_analysis`: Complexity analysis charts
- `learning_objectives`: Learning objectives visualization
- `section_breakdown`: Section breakdown charts
- `technical_content`: Technical content analysis

## Navigation

- [AGENTS.md](AGENTS.md) - File format and naming reference
- [../README.md](../README.md) - Data directory overview
- [../../docs/visualizations.md](../../docs/visualizations.md) - Visualization documentation

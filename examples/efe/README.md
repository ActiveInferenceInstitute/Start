# Expected Free Energy: Gridworld Action Selection

Interactive visualization of the Expected Free Energy (EFE) mathematical framework for action selection in a gridworld environment.

## Overview

This directory contains a complete React-based interactive simulation demonstrating:
- Gridworld environment with Temperature and pH attributes per tile
- Agent with probabilistic beliefs about tile values
- Action evaluation using Expected Free Energy
- Pragmatic Value: alignment with preference distributions
- Epistemic Value: expected information gain
- Interactive parameter adjustment with real-time visualization updates
- Multiple visualization types (gridworld, distributions, heatmaps, action evaluations)

## Files

### `efe.jsx`
React/JSX component file with the complete EFE simulation. Uses React hooks, Tailwind CSS, and Lucide React icons.

### `efe-compiled.html`
Standalone HTML file compiled from `efe.jsx`. Includes all dependencies bundled and can be opened directly in a browser without a build step.

### `efe-entry.jsx`
Entry point for the build process. Imports the main component and makes React/ReactDOM globally available.

### `build-efe.js`
Build script that uses esbuild to compile the JSX component into a standalone HTML file.

## Building

See [BUILD.md](BUILD.md) for detailed build instructions.

Quick start:
```bash
cd examples/efe
npm install
npm run build
```

## Usage

### Compiled Version
Simply open `efe-compiled.html` in any modern web browser.

### Development Version
The component can be used in a React project by importing `efe.jsx`.

## GIF Generation

Automated GIF generation captures interactive demonstrations of the visualization.

### Prerequisites

1. Install dependencies:
```bash
npm install
```

2. Install Playwright browsers:
```bash
npx playwright install
```

3. Build the HTML file (if not already built):
```bash
npm run build
```

### Generating GIFs

Run the capture script:
```bash
npm run capture-gifs
```

This will generate animated GIFs in the `gifs/` directory:
- `preference-sliders.gif` - Demonstrates preference distribution adjustments
- `action-execution.gif` - Shows action sampling and agent movement
- `tile-selection.gif` - Demonstrates tile clicking and belief inspection
- `action-prior.gif` - Shows action prior adjustments
- `posterior-demo.gif` - Demonstrates beta parameter and posterior visualization
- `sections-demo.gif` - Shows expanding/collapsing sections
- `full-demo.gif` - Complete interactive demonstration

The script uses Playwright to automate browser interactions, capture screenshots, and convert them to animated GIFs.

## Mathematical Framework

**Expected Free Energy (EFE)** for action `a`:
```
EFE(a) = Pragmatic Value + Epistemic Value
```

**Pragmatic Value**: Measures alignment with preference distributions
- KL divergence between predicted outcome and preference distribution
- Lower divergence = better alignment with preferences

**Epistemic Value**: Measures expected information gain
- Expected reduction in entropy (uncertainty) about tile values
- Higher information gain = better exploration

**Action Selection**: The agent selects actions that minimize EFE, balancing preference satisfaction with information gathering.

## Navigation

- [AGENTS.md](AGENTS.md) - Technical reference for EFE files
- [BUILD.md](BUILD.md) - Build instructions
- [../README.md](../README.md) - Examples overview
- [../../README.md](../../README.md) - Main project README

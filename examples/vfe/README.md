# Variational Free Energy: Perception Simulation

Interactive visualization of the Variational Free Energy (VFE) mathematical framework for perception.

## Overview

This directory contains a complete React-based interactive simulation demonstrating:
- Gaussian generative model (prior and likelihood)
- Recognition model (approximate posterior)
- Free Energy vs Surprise relationship
- Interactive parameter adjustment with real-time visualization updates
- Multiple visualization types (distributions, landscapes, trade-off plots)

## Files

### `vfe.jsx`
React/JSX component file with the complete VFE simulation. Uses React hooks, Tailwind CSS, and Lucide React icons.

### `vfe-compiled.html`
Standalone HTML file compiled from `vfe.jsx`. Includes all dependencies bundled and can be opened directly in a browser without a build step.

### `vfe-entry.jsx`
Entry point for the build process. Imports the main component and makes React/ReactDOM globally available.

### `build-vfe.js`
Build script that uses esbuild to compile the JSX component into a standalone HTML file.

## Building

See [BUILD.md](BUILD.md) for detailed build instructions.

Quick start:
```bash
cd examples/vfe
npm install
npm run build
```

## Usage

### Compiled Version
Simply open `vfe-compiled.html` in any modern web browser.

### Development Version
The component can be used in a React project by importing `vfe.jsx`.

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
- `slider-demo.gif` - Demonstrates slider movements and parameter changes
- `sections-demo.gif` - Shows expanding/collapsing sections
- `manual-mode-demo.gif` - Manual mode interaction and suboptimal belief exploration
- `parameter-combinations.gif` - Different parameter combinations
- `full-demo.gif` - Complete interactive demonstration

The script uses Playwright to automate browser interactions, capture screenshots, and convert them to animated GIFs.

## Navigation

- [AGENTS.md](AGENTS.md) - Technical reference for VFE files
- [BUILD.md](BUILD.md) - Build instructions
- [../README.md](../../README.md) - Project overview
- [../../README.md](../../README.md) - Main project README

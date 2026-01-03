# Examples Technical Reference

## Overview

Technical documentation for example files and demonstrations in the START project.

## Directory Structure

Examples are organized in subfolders, each containing:
- `README.md` - Overview and usage instructions
- `AGENTS.md` - Technical reference for that example
- Source files and build configuration
- Documentation

## Available Examples

### Variational Free Energy (VFE)

**Location**: [`vfe/`](vfe/)

**Type**: React/JSX interactive visualization

**Purpose**: Interactive demonstration of Variational Free Energy mathematical framework for perception simulation.

**Key Files**:
- `vfe.jsx` - Main React component (1181 lines)
- `vfe-compiled.html` - Standalone compiled version (9404 lines)
- `build-vfe.js` - Build script using esbuild
- `vfe-entry.jsx` - Build entry point

**Dependencies**:
- React 18.2.0
- ReactDOM 18.2.0
- lucide-react 0.294.0
- esbuild (build tool)
- Tailwind CSS (via CDN in compiled version)

**Build Process**:
1. `vfe-entry.jsx` imports component and exposes React/ReactDOM globally
2. `build-vfe.js` uses esbuild to bundle everything
3. Bundled code is injected into HTML template with Tailwind CSS
4. Output: `vfe-compiled.html` (standalone, no dependencies)

**Mathematical Components**:
- Gaussian PDF calculations
- KL divergence computations
- Bayesian posterior inference
- Free Energy and Surprise calculations
- Validation checks

**Visualizations**:
- Probability distribution plots (SVG)
- Free Energy landscape
- Complexity vs Accuracy trade-off
- Energy component bars
- Dynamic equation displays

**See**: [`vfe/AGENTS.md`](vfe/AGENTS.md) for detailed technical reference.

## Cross-References

- [README.md](README.md) - Examples overview
- [vfe/README.md](vfe/README.md) - VFE example overview
- [vfe/AGENTS.md](vfe/AGENTS.md) - VFE technical reference
- [../README.md](../README.md) - Main project README

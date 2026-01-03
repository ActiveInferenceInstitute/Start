# Examples

Example files and demonstrations for the START project.

## Overview

This directory contains example implementations demonstrating various concepts, visualizations, and usage patterns. Each example is organized in its own subfolder for clarity and maintainability.

## Structure

```
examples/
  ├── README.md          # This file - general examples overview
  ├── AGENTS.md          # Technical reference for examples
  └── vfe/               # Variational Free Energy perception simulation
      ├── README.md      # VFE-specific documentation
      ├── AGENTS.md      # VFE technical reference
      ├── BUILD.md       # Build instructions
      ├── vfe.jsx        # React component source
      ├── vfe-entry.jsx  # Build entry point
      ├── vfe-compiled.html  # Compiled standalone HTML
      ├── build-vfe.js   # Build script
      ├── package.json   # Node.js dependencies
      └── node_modules/  # Dependencies
```

## Available Examples

### Variational Free Energy (VFE)

Interactive visualization of the Variational Free Energy mathematical framework for perception.

**Location**: [`vfe/`](vfe/)

**Description**: A complete React-based interactive simulation demonstrating:
- Gaussian generative model (prior and likelihood)
- Recognition model (approximate posterior)
- Free Energy vs Surprise relationship
- Interactive parameter adjustment
- Real-time visualization updates

**Quick Start**:
```bash
cd vfe
npm install
npm run build
# Open vfe-compiled.html in browser
```

See [`vfe/README.md`](vfe/README.md) for detailed documentation.

## Adding New Examples

When adding new examples:

1. Create a new subfolder: `examples/your-example/`
2. Include a `README.md` with overview and usage instructions
3. Include an `AGENTS.md` with technical documentation
4. Update this README to reference the new example
5. Update `AGENTS.md` to include the new example

## Navigation

- [AGENTS.md](AGENTS.md) - Technical reference for all examples
- [vfe/](vfe/) - Variational Free Energy example
- [../README.md](../README.md) - Main project overview

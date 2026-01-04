# Building EFE Component

This directory contains a build script to compile the React JSX component (`efe.jsx`) into a standalone HTML file.

## Prerequisites

- Node.js (v16 or higher)
- npm or yarn

## Building

1. Install dependencies:
```bash
cd examples/efe
npm install
```

2. Run the build script:
```bash
npm run build
```

Or directly:
```bash
node build-efe.js
```

## Output

The build process creates `efe-compiled.html` - a standalone HTML file that includes:
- React and ReactDOM (bundled)
- All component code (JSX transformed to JavaScript)
- Lucide React icons (bundled)
- Everything needed to run the app in a browser

## Usage

Simply open `efe-compiled.html` in any modern web browser. No server or build process needed - it's completely self-contained.

## How It Works

1. `efe-entry.jsx` - Entry point that imports the component and makes React/ReactDOM globally available
2. `build-efe.js` - Uses esbuild to bundle everything into a single JavaScript file
3. The bundled code is injected into an HTML template
4. The HTML file includes everything needed to run the React app

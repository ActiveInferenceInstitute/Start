import * as esbuild from 'esbuild';
import { readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// HTML template
const htmlTemplate = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Expected Free Energy: Gridworld Action Selection</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            'gray-900': '#111827',
            'gray-800': '#1F2937',
            'gray-700': '#374151',
            'gray-200': '#E5E7EB',
            'gray-400': '#9CA3AF',
            'gray-500': '#6B7280',
            'blue-500': '#3B82F6',
            'red-500': '#EF4444',
            'emerald-500': '#10B981',
            'amber-500': '#F59E0B',
            'violet-500': '#8B5CF6',
            'pink-500': '#EC4899',
          }
        }
      }
    }
  </script>
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      background-color: #111827;
      color: #E5E7EB;
    }
    
    #root {
      min-height: 100vh;
    }
  </style>
</head>
<body>
  <div id="root"></div>
  <script>
    {BUNDLE_CODE}
    
    // Mount the React app
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(React.createElement(EFEDashboard));
  </script>
</body>
</html>`;

async function build() {
  try {
    console.log('Building EFE component...');
    
    // Bundle everything including React and ReactDOM using entry point
    const result = await esbuild.build({
      entryPoints: [join(__dirname, 'efe-entry.jsx')],
      bundle: true,
      format: 'iife',
      jsx: 'automatic',
      write: false,
      minify: false,
      sourcemap: false,
      platform: 'browser',
      define: {
        'process.env.NODE_ENV': '"production"',
      },
    });

    const bundleCode = result.outputFiles[0].text;
    
    // Replace placeholder in HTML template
    const finalHTML = htmlTemplate.replace('{BUNDLE_CODE}', bundleCode);
    
    // Write output
    const outputPath = join(__dirname, 'efe-compiled.html');
    writeFileSync(outputPath, finalHTML);
    
    console.log(`✓ Built successfully: ${outputPath}`);
    console.log(`  Bundle size: ${(bundleCode.length / 1024).toFixed(2)} KB`);
  } catch (error) {
    console.error('Build failed:', error);
    console.error(error.stack);
    process.exit(1);
  }
}

build();

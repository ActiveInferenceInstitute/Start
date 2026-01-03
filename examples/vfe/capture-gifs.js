import { chromium } from 'playwright';
import { readFileSync, writeFileSync, existsSync, createWriteStream } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import GIFEncoder from 'gifencoder';
import { createCanvas, loadImage } from 'canvas';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const GIFS_DIR = join(__dirname, 'gifs');
const HTML_FILE = join(__dirname, 'vfe-compiled.html');

// Ensure HTML file exists
if (!existsSync(HTML_FILE)) {
  console.error(`Error: ${HTML_FILE} not found. Please run 'npm run build' first.`);
  process.exit(1);
}

// Helper: Generate unique screenshot path
let frameCounter = 0;
function getNextScreenshotPath() {
  return join(__dirname, `temp_screenshot_${frameCounter++}.png`);
}

// Helper: Wait for React to render
async function waitForReact(page) {
  await page.waitForSelector('#root', { state: 'attached' });
  await page.waitForTimeout(500); // Allow React to fully render
}

// Helper: Capture screenshot
async function captureScreenshot(page, path) {
  await page.screenshot({ path, fullPage: true });
  return readFileSync(path);
}

// Helper: Update slider and wait for React
async function updateSlider(page, sliderLocator, value) {
  await sliderLocator.evaluate((el, val) => {
    el.value = val;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }, value);
  await page.waitForTimeout(200); // Wait for React to process
}

// Helper: Create GIF from screenshots
async function createGIF(screenshotPaths, outputPath, fps = 8) {
  if (screenshotPaths.length === 0) {
    console.error('No screenshots to create GIF');
    return;
  }

  // Load first image to get dimensions
  const firstImage = await loadImage(screenshotPaths[0]);
  const width = firstImage.width;
  const height = firstImage.height;

  // Create encoder with file stream
  const encoder = new GIFEncoder(width, height);
  const file = createWriteStream(outputPath);
  encoder.createReadStream().pipe(file);

  encoder.start();
  encoder.setRepeat(0); // 0 for repeat, -1 for no-repeat
  encoder.setDelay(1000 / fps); // Delay between frames in ms
  encoder.setQuality(10); // Image quality. 10 is default.

  // Create canvas
  const canvas = createCanvas(width, height);
  const ctx = canvas.getContext('2d');

  // Add frames
  for (const screenshotPath of screenshotPaths) {
    const image = await loadImage(screenshotPath);
    ctx.drawImage(image, 0, 0);
    encoder.addFrame(ctx);
  }

  encoder.finish();
  
  // Wait for file stream to finish
  await new Promise((resolve, reject) => {
    file.on('finish', resolve);
    file.on('error', reject);
  });
  
  console.log(`✓ Created GIF: ${outputPath}`);
}

// Helper: Gradually change slider value
async function animateSlider(page, sliderLocator, startValue, endValue, steps = 20, delay = 50) {
  const stepSize = (endValue - startValue) / steps;
  for (let i = 0; i <= steps; i++) {
    const value = startValue + stepSize * i;
    await sliderLocator.evaluate((el, val) => {
      el.value = val;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    }, value);
    await page.waitForTimeout(delay);
  }
}

// Scenario 1: Slider movements
async function captureSliderDemo(page, screenshots) {
  console.log('Capturing slider demo...');
  
  await waitForReact(page);
  await page.waitForTimeout(500);

  // Find sliders by their labels (they're in sections)
  const observationSlider = page.locator('input[type="range"]').nth(0);
  const sensoryPrecisionSlider = page.locator('input[type="range"]').nth(1);
  const priorMeanSlider = page.locator('input[type="range"]').nth(2);

  // Capture initial state
  const tempPath = getNextScreenshotPath();
  await captureScreenshot(page, tempPath);
  screenshots.push(tempPath);

  // Animate observation slider (10 steps)
  for (let i = 0; i <= 10; i++) {
    const value = (i / 10) * 4 - 2; // -2 to 2
    await updateSlider(page, observationSlider, value);
    const path = getNextScreenshotPath();
    await captureScreenshot(page, path);
    screenshots.push(path);
  }

  // Animate prior mean (8 steps)
  for (let i = 0; i <= 8; i++) {
    const value = (i / 8) * 3 - 1.5; // -1.5 to 1.5
    await updateSlider(page, priorMeanSlider, value);
    const path = getNextScreenshotPath();
    await captureScreenshot(page, path);
    screenshots.push(path);
  }

  // Animate sensory precision (8 steps)
  for (let i = 0; i <= 8; i++) {
    const value = 0.5 + (i / 8) * 4; // 0.5 to 4.5
    await updateSlider(page, sensoryPrecisionSlider, value);
    const path = getNextScreenshotPath();
    await captureScreenshot(page, path);
    screenshots.push(path);
  }
}

// Scenario 2: Section toggles
async function captureSectionsDemo(page, screenshots) {
  console.log('Capturing sections demo...');
  
  await waitForReact(page);
  await page.waitForTimeout(500);

  // Find section headers (they have chevron icons)
  const sectionHeaders = page.locator('button').filter({ hasText: /Free Energy|Probability|Components|Equations|Errors|Landscape|Trade-off|Validation|Parameters/ });

  // Capture initial state
  const initialPath = getNextScreenshotPath();
  await captureScreenshot(page, initialPath);
  screenshots.push(initialPath);

  // Toggle a few key sections (limit to 5 for brevity)
  const count = Math.min(await sectionHeaders.count(), 5);
  for (let i = 0; i < count; i++) {
    await sectionHeaders.nth(i).click();
    await page.waitForTimeout(200); // Wait for animation
    const path = getNextScreenshotPath();
    await captureScreenshot(page, path);
    screenshots.push(path);
  }

  // Toggle back open
  for (let i = 0; i < count; i++) {
    await sectionHeaders.nth(i).click();
    await page.waitForTimeout(200);
    const path = getNextScreenshotPath();
    await captureScreenshot(page, path);
    screenshots.push(path);
  }
}

// Scenario 3: Manual mode
async function captureManualModeDemo(page, screenshots) {
  console.log('Capturing manual mode demo...');
  
  await waitForReact(page);
  await page.waitForTimeout(500);

  // Find manual mode checkbox
  const manualCheckbox = page.locator('input[type="checkbox"]#manual');
  
  // Capture initial state (manual mode off)
  const initialPath = getNextScreenshotPath();
  await captureScreenshot(page, initialPath);
  screenshots.push(initialPath);

  // Enable manual mode using JavaScript click to bypass interception
  await manualCheckbox.evaluate(el => el.click());
  await page.waitForTimeout(500);
  const afterCheckboxPath = getNextScreenshotPath();
  await captureScreenshot(page, afterCheckboxPath);
  screenshots.push(afterCheckboxPath);

  // Find manual slider (appears after checkbox is checked)
  const manualSlider = page.locator('input[type="range"]').last();
  
  // Animate manual slider away from optimal (10 steps)
  for (let i = 0; i <= 10; i++) {
    const value = 1.0 + (i / 10) * 2; // 1.0 to 3.0 (away from optimal)
    await updateSlider(page, manualSlider, value);
    const path = getNextScreenshotPath();
    await captureScreenshot(page, path);
    screenshots.push(path);
  }

  // Move back toward optimal (10 steps)
  for (let i = 10; i >= 0; i--) {
    const value = 1.0 + (i / 10) * 2;
    await updateSlider(page, manualSlider, value);
    const path = getNextScreenshotPath();
    await captureScreenshot(page, path);
    screenshots.push(path);
  }
}

// Scenario 4: Parameter combinations
async function captureParameterCombinations(page, screenshots) {
  console.log('Capturing parameter combinations...');
  
  await waitForReact(page);
  await page.waitForTimeout(500);

  const observationSlider = page.locator('input[type="range"]').nth(0);
  const sensoryPrecisionSlider = page.locator('input[type="range"]').nth(1);
  const priorMeanSlider = page.locator('input[type="range"]').nth(2);
  const priorPrecisionSlider = page.locator('input[type="range"]').nth(3);

  // Different parameter combinations
  const combinations = [
    { o: 0, pi_o: 1, mu_p: 0, pi_p: 1, label: 'Balanced' },
    { o: 3, pi_o: 5, mu_p: 0, pi_p: 1, label: 'High sensory trust' },
    { o: 0, pi_o: 1, mu_p: 2, pi_p: 5, label: 'Strong prior' },
    { o: -2, pi_o: 2, mu_p: 1, pi_p: 2, label: 'Conflicting signals' },
  ];

  for (const combo of combinations) {
    await updateSlider(page, observationSlider, combo.o);
    await updateSlider(page, sensoryPrecisionSlider, combo.pi_o);
    await updateSlider(page, priorMeanSlider, combo.mu_p);
    await updateSlider(page, priorPrecisionSlider, combo.pi_p);
    await page.waitForTimeout(300); // Wait for all updates
    
    // Capture and hold for 2-3 frames
    for (let i = 0; i < 3; i++) {
      const path = getNextScreenshotPath();
      await captureScreenshot(page, path);
      screenshots.push(path);
      if (i < 2) await page.waitForTimeout(100);
    }
  }
}

// Scenario 5: Full demo (combination)
async function captureFullDemo(page, screenshots) {
  console.log('Capturing full demo...');
  
  await waitForReact(page);
  await page.waitForTimeout(500);

  // Start with initial state
  const initialPath = getNextScreenshotPath();
  await captureScreenshot(page, initialPath);
  screenshots.push(initialPath);

  // Expand a section
  const firstSection = page.locator('button').first();
  await firstSection.click();
  await page.waitForTimeout(200);
  const afterSectionPath = getNextScreenshotPath();
  await captureScreenshot(page, afterSectionPath);
  screenshots.push(afterSectionPath);

  // Move observation slider (8 steps)
  const observationSlider = page.locator('input[type="range"]').nth(0);
  for (let i = 0; i <= 8; i++) {
    const value = (i / 8) * 3 - 1.5;
    await updateSlider(page, observationSlider, value);
    const path = getNextScreenshotPath();
    await captureScreenshot(page, path);
    screenshots.push(path);
  }

  // Enable manual mode and adjust
  const manualCheckbox = page.locator('input[type="checkbox"]#manual');
  await manualCheckbox.evaluate(el => el.click());
  await page.waitForTimeout(500);
  const afterManualPath = getNextScreenshotPath();
  await captureScreenshot(page, afterManualPath);
  screenshots.push(afterManualPath);

  const manualSlider = page.locator('input[type="range"]').last();
  for (let i = 0; i <= 8; i++) {
    const value = 1.5 + (i / 8) * 1;
    await updateSlider(page, manualSlider, value);
    const path = getNextScreenshotPath();
    await captureScreenshot(page, path);
    screenshots.push(path);
  }
}

async function main() {
  console.log('Starting GIF capture...');
  console.log(`HTML file: ${HTML_FILE}`);
  console.log(`Output directory: ${GIFS_DIR}`);

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
  });
  const page = await context.newPage();

  try {
    // Navigate to HTML file
    const fileUrl = `file://${HTML_FILE}`;
    await page.goto(fileUrl, { waitUntil: 'networkidle' });
    await waitForReact(page);

    const scenarios = [
      { name: 'slider-demo', func: captureSliderDemo },
      { name: 'sections-demo', func: captureSectionsDemo },
      { name: 'manual-mode-demo', func: captureManualModeDemo },
      { name: 'parameter-combinations', func: captureParameterCombinations },
      { name: 'full-demo', func: captureFullDemo },
    ];

    for (const scenario of scenarios) {
      console.log(`\n=== ${scenario.name} ===`);
      frameCounter = 0; // Reset counter for each scenario
      const screenshots = [];
      
      // Reload page for each scenario
      await page.reload({ waitUntil: 'networkidle' });
      await waitForReact(page);
      
      // Capture screenshots
      await scenario.func(page, screenshots);
      
      // Create GIF
      if (screenshots.length > 0) {
        const outputPath = join(GIFS_DIR, `${scenario.name}.gif`);
        await createGIF(screenshots, outputPath, 8);
        
        // Clean up all temporary screenshots
        const { unlinkSync } = await import('fs');
        for (const screenshot of screenshots) {
          try {
            unlinkSync(screenshot);
          } catch (e) {
            // Ignore cleanup errors
          }
        }
      }
    }

    console.log('\n✓ All GIFs generated successfully!');
    console.log(`Output directory: ${GIFS_DIR}`);

  } catch (error) {
    console.error('Error during capture:', error);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

main().catch(console.error);

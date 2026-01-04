import { chromium } from 'playwright';
import { readFileSync, writeFileSync, existsSync, createWriteStream, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import GIFEncoder from 'gifencoder';
import { createCanvas, loadImage } from 'canvas';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const GIFS_DIR = join(__dirname, 'gifs');
const HTML_FILE = join(__dirname, 'efe-compiled.html');

// Ensure gifs directory exists
if (!existsSync(GIFS_DIR)) {
  mkdirSync(GIFS_DIR, { recursive: true });
}

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
  await page.waitForTimeout(1000); // Allow React to fully render
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
  await page.waitForTimeout(300); // Wait for React to process
}

// Helper: Click element
async function clickElement(page, locator) {
  await locator.click();
  await page.waitForTimeout(300);
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

// Scenario 1: Preference slider adjustments
async function capturePreferenceSliders(page, screenshots) {
  console.log('Capturing preference slider demo...');
  
  await waitForReact(page);
  await page.waitForTimeout(500);

  // Find preference sliders (Temperature and pH)
  const tempMuSlider = page.locator('input[type="range"]').filter({ has: page.locator('text=Temperature') }).first();
  const tempSigmaSlider = page.locator('input[type="range"]').filter({ has: page.locator('text=Temperature') }).nth(1);
  const pHMuSlider = page.locator('input[type="range"]').filter({ has: page.locator('text=pH') }).first();
  const pHSigmaSlider = page.locator('input[type="range"]').filter({ has: page.locator('text=pH') }).nth(1);

  // Get all sliders by index (more reliable)
  const allSliders = page.locator('input[type="range"]');
  const sliderCount = await allSliders.count();
  
  // Temperature sliders are typically first two in preference section
  // pH sliders are next two
  let tempMuIdx = 0, tempSigmaIdx = 1, pHMuIdx = 2, pHSigmaIdx = 3;
  
  // Capture initial state
  const tempPath = getNextScreenshotPath();
  await captureScreenshot(page, tempPath);
  screenshots.push(tempPath);

  // Animate Temperature mean (8 steps)
  for (let i = 0; i <= 8; i++) {
    const value = (i / 8) * 1.0; // 0 to 1
    const slider = allSliders.nth(tempMuIdx);
    if (await slider.count() > 0) {
      await updateSlider(page, slider, value);
      const path = getNextScreenshotPath();
      await captureScreenshot(page, path);
      screenshots.push(path);
    }
  }

  // Animate Temperature sigma (6 steps)
  for (let i = 0; i <= 6; i++) {
    const value = 0.05 + (i / 6) * 0.35; // 0.05 to 0.4
    const slider = allSliders.nth(tempSigmaIdx);
    if (await slider.count() > 0) {
      await updateSlider(page, slider, value);
      const path = getNextScreenshotPath();
      await captureScreenshot(page, path);
      screenshots.push(path);
    }
  }

  // Animate pH mean (8 steps)
  for (let i = 0; i <= 8; i++) {
    const value = (i / 8) * 1.0; // 0 to 1
    const slider = allSliders.nth(pHMuIdx);
    if (await slider.count() > 0) {
      await updateSlider(page, slider, value);
      const path = getNextScreenshotPath();
      await captureScreenshot(page, path);
      screenshots.push(path);
    }
  }
}

// Scenario 2: Action execution and agent movement
async function captureActionExecution(page, screenshots) {
  console.log('Capturing action execution demo...');
  
  await waitForReact(page);
  await page.waitForTimeout(500);

  // Capture initial state
  const initialPath = getNextScreenshotPath();
  await captureScreenshot(page, initialPath);
  screenshots.push(initialPath);

  // Find action buttons (they have icons and text)
  const actionButtons = page.locator('button, div').filter({ 
    hasText: /Up|Down|Left|Right|Stay/
  });

  // Try clicking actions by finding the "Sample Action from Posterior" button first
  // Then find action evaluation panel items
  const sampleButton = page.locator('button').filter({ hasText: /Sample Action/ });
  
  // If sample button exists, click it a few times
  if (await sampleButton.count() > 0) {
    for (let i = 0; i < 5; i++) {
      await sampleButton.click();
      await page.waitForTimeout(500);
      const path = getNextScreenshotPath();
      await captureScreenshot(page, path);
      screenshots.push(path);
    }
  }

  // Also try clicking action items directly
  // Actions are in clickable divs with action names
  const actionItems = page.locator('div').filter({ 
    hasText: /^Up$|^Down$|^Left$|^Right$|^Stay$/
  });

  const actionCount = Math.min(await actionItems.count(), 3);
  for (let i = 0; i < actionCount; i++) {
    await actionItems.nth(i).click();
    await page.waitForTimeout(500);
    const path = getNextScreenshotPath();
    await captureScreenshot(page, path);
    screenshots.push(path);
  }
}

// Scenario 3: Tile selection and belief exploration
async function captureTileSelection(page, screenshots) {
  console.log('Capturing tile selection demo...');
  
  await waitForReact(page);
  await page.waitForTimeout(500);

  // Capture initial state
  const initialPath = getNextScreenshotPath();
  await captureScreenshot(page, initialPath);
  screenshots.push(initialPath);

  // Find gridworld SVG
  const gridworldSVG = page.locator('svg').first();
  
  // Click on different tiles in the gridworld
  // Tiles are rect elements within the SVG
  const tiles = gridworldSVG.locator('rect');
  const tileCount = Math.min(await tiles.count(), 8);
  
  for (let i = 0; i < tileCount; i += 2) { // Skip every other to show variety
    try {
      await tiles.nth(i).click();
      await page.waitForTimeout(400);
      const path = getNextScreenshotPath();
      await captureScreenshot(page, path);
      screenshots.push(path);
    } catch (e) {
      // Continue if click fails
    }
  }

  // Also try clicking on uncertainty heatmap
  const heatmapSVG = page.locator('svg').nth(1);
  if (await heatmapSVG.count() > 0) {
    const heatmapTiles = heatmapSVG.locator('rect');
    const heatmapTileCount = Math.min(await heatmapTiles.count(), 3);
    for (let i = 0; i < heatmapTileCount; i++) {
      try {
        await heatmapTiles.nth(i).click();
        await page.waitForTimeout(400);
        const path = getNextScreenshotPath();
        await captureScreenshot(page, path);
        screenshots.push(path);
      } catch (e) {
        // Continue if click fails
      }
    }
  }
}

// Scenario 4: Action prior adjustments
async function captureActionPrior(page, screenshots) {
  console.log('Capturing action prior demo...');
  
  await waitForReact(page);
  await page.waitForTimeout(500);

  // Capture initial state
  const initialPath = getNextScreenshotPath();
  await captureScreenshot(page, initialPath);
  screenshots.push(initialPath);

  // Find action prior sliders (they're in the Action Prior section)
  // They come after preference sliders
  const allSliders = page.locator('input[type="range"]');
  const sliderCount = await allSliders.count();
  
  // Action prior sliders are typically after preference sliders (indices 4-8)
  const startIdx = Math.min(4, sliderCount - 5);
  const endIdx = Math.min(startIdx + 5, sliderCount);
  
  for (let idx = startIdx; idx < endIdx; idx++) {
    const slider = allSliders.nth(idx);
    if (await slider.count() > 0) {
      // Animate slider from 0 to 1
      for (let step = 0; step <= 5; step++) {
        const value = (step / 5) * 1.0;
        await updateSlider(page, slider, value);
        if (step === 0 || step === 5) {
          const path = getNextScreenshotPath();
          await captureScreenshot(page, path);
          screenshots.push(path);
        }
      }
    }
  }

  // Try clicking "Reset to Uniform" button
  const resetButton = page.locator('button').filter({ hasText: /Reset to Uniform|Uniform/ });
  if (await resetButton.count() > 0) {
    await resetButton.first().click();
    await page.waitForTimeout(500);
    const path = getNextScreenshotPath();
    await captureScreenshot(page, path);
    screenshots.push(path);
  }
}

// Scenario 5: Beta parameter and posterior visualization
async function capturePosteriorDemo(page, screenshots) {
  console.log('Capturing posterior demo...');
  
  await waitForReact(page);
  await page.waitForTimeout(500);

  // Capture initial state
  const initialPath = getNextScreenshotPath();
  await captureScreenshot(page, initialPath);
  screenshots.push(initialPath);

  // Find beta slider (inverse temperature)
  // It's in the Action Posterior section
  const allSliders = page.locator('input[type="range"]');
  const sliderCount = await allSliders.count();
  
  // Beta slider is typically one of the later sliders
  // Try to find it by looking for sliders with value around 1.0
  // Or just use a later index
  const betaSliderIdx = Math.min(9, sliderCount - 1);
  const betaSlider = allSliders.nth(betaSliderIdx);
  
  if (await betaSlider.count() > 0) {
    // Animate beta from low to high (exploratory to deterministic)
    for (let i = 0; i <= 10; i++) {
      const value = 0.1 + (i / 10) * 4.9; // 0.1 to 5.0
      await updateSlider(page, betaSlider, value);
      const path = getNextScreenshotPath();
      await captureScreenshot(page, path);
      screenshots.push(path);
    }
  }
}

// Scenario 6: Section toggles
async function captureSectionsDemo(page, screenshots) {
  console.log('Capturing sections demo...');
  
  await waitForReact(page);
  await page.waitForTimeout(500);

  // Capture initial state
  const initialPath = getNextScreenshotPath();
  await captureScreenshot(page, initialPath);
  screenshots.push(initialPath);

  // Find section headers (they have chevron icons and are buttons)
  const sectionHeaders = page.locator('button').filter({ 
    has: page.locator('svg') // Has chevron icon
  });

  // Toggle a few key sections
  const count = Math.min(await sectionHeaders.count(), 6);
  for (let i = 0; i < count; i++) {
    try {
      await sectionHeaders.nth(i).click();
      await page.waitForTimeout(300);
      const path = getNextScreenshotPath();
      await captureScreenshot(page, path);
      screenshots.push(path);
    } catch (e) {
      // Continue if click fails
    }
  }

  // Toggle back open
  for (let i = 0; i < count; i++) {
    try {
      await sectionHeaders.nth(i).click();
      await page.waitForTimeout(300);
      const path = getNextScreenshotPath();
      await captureScreenshot(page, path);
      screenshots.push(path);
    } catch (e) {
      // Continue if click fails
    }
  }
}

// Scenario 7: Full workflow demo
async function captureFullDemo(page, screenshots) {
  console.log('Capturing full demo...');
  
  await waitForReact(page);
  await page.waitForTimeout(500);

  // Initial state
  const initialPath = getNextScreenshotPath();
  await captureScreenshot(page, initialPath);
  screenshots.push(initialPath);

  // Adjust preferences
  const allSliders = page.locator('input[type="range"]');
  if (await allSliders.count() > 0) {
    await updateSlider(page, allSliders.nth(0), 0.7);
    await page.waitForTimeout(300);
    const path1 = getNextScreenshotPath();
    await captureScreenshot(page, path1);
    screenshots.push(path1);
  }

  // Click a tile
  const gridworldSVG = page.locator('svg').first();
  const tiles = gridworldSVG.locator('rect');
  if (await tiles.count() > 0) {
    await tiles.nth(5).click();
    await page.waitForTimeout(400);
    const path2 = getNextScreenshotPath();
    await captureScreenshot(page, path2);
    screenshots.push(path2);
  }

  // Sample an action
  const sampleButton = page.locator('button').filter({ hasText: /Sample Action/ });
  if (await sampleButton.count() > 0) {
    await sampleButton.click();
    await page.waitForTimeout(500);
    const path3 = getNextScreenshotPath();
    await captureScreenshot(page, path3);
    screenshots.push(path3);
  }

  // Adjust beta
  const betaSlider = allSliders.nth(Math.min(9, await allSliders.count() - 1));
  if (await betaSlider.count() > 0) {
    await updateSlider(page, betaSlider, 3.0);
    await page.waitForTimeout(300);
    const path4 = getNextScreenshotPath();
    await captureScreenshot(page, path4);
    screenshots.push(path4);
  }

  // Sample another action
  if (await sampleButton.count() > 0) {
    await sampleButton.click();
    await page.waitForTimeout(500);
    const path5 = getNextScreenshotPath();
    await captureScreenshot(page, path5);
    screenshots.push(path5);
  }
}

async function main() {
  console.log('Starting EFE GIF capture...');
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
      { name: 'preference-sliders', func: capturePreferenceSliders },
      { name: 'action-execution', func: captureActionExecution },
      { name: 'tile-selection', func: captureTileSelection },
      { name: 'action-prior', func: captureActionPrior },
      { name: 'posterior-demo', func: capturePosteriorDemo },
      { name: 'sections-demo', func: captureSectionsDemo },
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

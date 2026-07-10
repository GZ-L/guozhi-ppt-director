#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";

const DEFAULT_CHROME =
  process.platform === "darwin"
    ? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    : undefined;

function argValue(name, fallback = undefined) {
  const index = process.argv.indexOf(name);
  if (index === -1 || index + 1 >= process.argv.length) return fallback;
  return process.argv[index + 1];
}

function hasFlag(name) {
  return process.argv.includes(name);
}

async function loadPlaywright() {
  try {
    return await import("playwright");
  } catch {
    const moduleDir = process.env.PLAYWRIGHT_NODE_MODULES;
    if (!moduleDir) {
      throw new Error(
        "Cannot import playwright. Install it or set PLAYWRIGHT_NODE_MODULES to a node_modules directory containing playwright.",
      );
    }
    const requireFromDir = createRequire(path.join(moduleDir, "_entry.js"));
    return requireFromDir("playwright");
  }
}

async function readJson(file) {
  return JSON.parse(await fs.readFile(file, "utf-8"));
}

async function writeJson(file, data) {
  await fs.writeFile(file, `${JSON.stringify(data, null, 2)}\n`, "utf-8");
}

function shouldCapture(result, onlyMissing, requestedIndex) {
  if (requestedIndex && result.index !== requestedIndex) return false;
  if (!onlyMissing) return true;
  return result.status !== "ok" || !result.asset_path;
}

async function main() {
  const skillRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
  const indexFile = path.resolve(
    skillRoot,
    argValue("--index", "references/style-library/zcool-style-index.json"),
  );
  const outputDir = path.resolve(
    skillRoot,
    argValue("--output-dir", "assets/style-library/zcool-first-screen"),
  );
  const onlyMissing = hasFlag("--only-missing");
  const requestedIndex = argValue("--ref");
  const chromePath = argValue("--chrome-path", process.env.CHROME_PATH || DEFAULT_CHROME);
  const waitMs = Number(argValue("--wait-ms", "5000"));
  const width = Number(argValue("--width", "1440"));
  const height = Number(argValue("--height", "1000"));

  const index = await readJson(indexFile);
  const targets = index.results.filter((result) => shouldCapture(result, onlyMissing, requestedIndex));
  if (!targets.length) {
    console.log("No screenshot targets.");
    return;
  }

  const { chromium } = await loadPlaywright();
  const browser = await chromium.launch({
    headless: true,
    ...(chromePath ? { executablePath: chromePath } : {}),
  });

  await fs.mkdir(outputDir, { recursive: true });
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });

  for (const result of targets) {
    const fileName = `zcool-ref-${result.index}-screenshot.png`;
    const outputFile = path.join(outputDir, fileName);
    try {
      await page.goto(result.source_url, { waitUntil: "domcontentloaded", timeout: 45000 });
      await page.waitForTimeout(waitMs);
      await page.screenshot({ path: outputFile, fullPage: false });
      const stat = await fs.stat(outputFile);
      result.status = "ok";
      result.image_url = "browser-first-screen-screenshot";
      result.asset_path = `assets/style-library/zcool-first-screen/${fileName}`;
      result.content_type = "image/png";
      result.bytes = stat.size;
      result.error = null;
      console.log(`captured ref-${result.index}: ${outputFile}`);
    } catch (error) {
      result.status = "screenshot_failed";
      result.error = error instanceof Error ? error.message : String(error);
      console.error(`failed ref-${result.index}: ${result.error}`);
    }
  }

  await browser.close();
  index.method = "metadata_image_extract_with_browser_screenshot_fallback";
  index.updated_at = new Date().toISOString();
  await writeJson(indexFile, index);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

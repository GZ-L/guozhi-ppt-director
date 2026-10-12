#!/usr/bin/env node
/** Verify the web_motion_v1 QA bridge and browser video playback. */

import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
let chromium;
try {
  ({ chromium } = require("playwright"));
} catch (error) {
  process.stderr.write(
    `${JSON.stringify({ ok: false, errors: [{ code: "MOTION_TARGET_UNAVAILABLE", message: "Playwright is unavailable", evidence: String(error) }] }, null, 2)}\n`,
  );
  process.exit(2);
}

function parseArgs(argv) {
  const args = { expectBuilds: 0, expectVideo: false, json: false };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--url") args.url = argv[++index];
    else if (token === "--expect-builds") args.expectBuilds = Number(argv[++index]);
    else if (token === "--expect-video") args.expectVideo = true;
    else if (token === "--json") args.json = true;
    else if (token === "--browser-executable") args.browserExecutable = argv[++index];
    else throw new Error(`unknown argument: ${token}`);
  }
  if (!args.url) throw new Error("--url is required");
  if (!Number.isInteger(args.expectBuilds) || args.expectBuilds < 0) {
    throw new Error("--expect-builds must be a non-negative integer");
  }
  return args;
}

async function inspect(url, expectBuilds, expectVideo, browserExecutable) {
  const report = {
    url,
    ok: false,
    verification_level: null,
    bridge_version: null,
    states: [],
    reduced_motion: false,
    videos: [],
    errors: [],
  };
  let browser;
  try {
    browser = await chromium.launch({
      headless: true,
      executablePath: browserExecutable || undefined,
      args: ["--autoplay-policy=no-user-gesture-required"],
    });
    const page = await browser.newPage();
    await page.goto(url, { waitUntil: "load", timeout: 15000 });
    const bridge = await page.evaluate(() => {
      const api = window.__GUOZHI_DECK_QA__;
      if (!api || typeof api.getState !== "function" || typeof api.advance !== "function") {
        return null;
      }
      return { version: String(api.version || ""), state: api.getState() };
    });
    if (!bridge) {
      report.errors.push({
        code: "MOTION_STRUCTURE_INVALID",
        message: "window.__GUOZHI_DECK_QA__ bridge is missing or incomplete",
        evidence: null,
      });
      return report;
    }
    report.bridge_version = bridge.version;
    report.states.push(bridge.state);
    for (let index = 0; index < expectBuilds; index += 1) {
      const state = await page.evaluate(async () => {
        const result = await window.__GUOZHI_DECK_QA__.advance();
        return result || window.__GUOZHI_DECK_QA__.getState();
      });
      report.states.push(state);
      await page.waitForTimeout(50);
    }
    const finalState = report.states.at(-1) || {};
    if (expectBuilds > 0 && Number(finalState.revealIndex) < expectBuilds) {
      report.errors.push({
        code: "PLAYBACK_QA_FAILED",
        message: "web deck did not reach the expected reveal index",
        evidence: JSON.stringify(finalState),
      });
    }

    await page.emulateMedia({ reducedMotion: "reduce" });
    report.reduced_motion = await page.evaluate(
      () => window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    );
    if (!report.reduced_motion) {
      report.errors.push({
        code: "PLAYBACK_QA_FAILED",
        message: "browser reduced-motion mode could not be enabled",
        evidence: null,
      });
    }

    if (expectVideo) {
      const count = await page.locator("video[data-video-id]").count();
      if (count === 0) {
        report.errors.push({
          code: "VIDEO_SOURCE_UNAVAILABLE",
          message: "expected video[data-video-id] element is missing",
          evidence: null,
        });
      } else {
        await page.waitForFunction(
          () => [...document.querySelectorAll("video[data-video-id]")].every((video) => video.readyState >= 1),
          null,
          { timeout: 10000 },
        );
        report.videos = await page.evaluate(async () => {
          const records = [];
          for (const video of document.querySelectorAll("video[data-video-id]")) {
            let playError = null;
            try {
              await video.play();
              await new Promise((resolve) => setTimeout(resolve, 250));
            } catch (error) {
              playError = String(error);
            }
            records.push({
              id: video.dataset.videoId,
              readyState: video.readyState,
              duration: video.duration,
              currentTime: video.currentTime,
              muted: video.muted,
              playable: !playError && video.readyState >= 2 && video.currentTime > 0,
              error: playError,
            });
          }
          return records;
        });
        for (const video of report.videos) {
          if (!video.playable) {
            report.errors.push({
              code: "PLAYBACK_QA_FAILED",
              message: `video ${video.id || "unknown"} did not advance during playback`,
              evidence: JSON.stringify(video),
            });
          }
        }
      }
    }
  } catch (error) {
    report.errors.push({
      code: "PLAYBACK_QA_FAILED",
      message: "browser motion verification failed",
      evidence: String(error),
    });
  } finally {
    if (browser) await browser.close();
  }
  report.ok = report.errors.length === 0;
  report.verification_level = report.ok ? "playback" : null;
  return report;
}

let args;
try {
  args = parseArgs(process.argv.slice(2));
} catch (error) {
  process.stderr.write(`${String(error)}\n`);
  process.exit(2);
}

const report = await inspect(
  args.url,
  args.expectBuilds,
  args.expectVideo,
  args.browserExecutable,
);
if (args.json) process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
else {
  process.stdout.write(
    `web motion verification: ok=${report.ok} states=${report.states.length} videos=${report.videos.length}\n`,
  );
}
process.exit(report.ok ? 0 : 1);

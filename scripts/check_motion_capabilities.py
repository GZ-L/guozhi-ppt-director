#!/usr/bin/env python3
"""Inspect motion and video verification capabilities without changing artifacts."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


PROTOCOL_VERSION = "1.1"
PROFILE_IDS = {"none", "web_motion_v1", "pptx_basic_v1", "dual_motion_v1"}
VERIFICATION_LEVELS = {"structural", "playback"}


def _default_app_probe(name: str) -> str | bool:
    candidates = [Path("/Applications") / name, Path.home() / "Applications" / name]
    for candidate in candidates:
        if candidate.is_dir():
            return str(candidate)
    return False


def _application_record(value: str | bool) -> dict[str, Any]:
    return {
        "available": bool(value),
        "path": value if isinstance(value, str) else None,
    }


def _default_playwright_probe(node_path: str | None) -> bool:
    if not node_path:
        return False
    try:
        completed = subprocess.run(
            [node_path, "-e", "require('playwright')"],
            env=os.environ.copy(),
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0


def inspect_capabilities(
    *,
    which: Callable[[str], str | None] = shutil.which,
    app_exists: Callable[[str], str | bool] = _default_app_probe,
    platform_name: str | None = None,
    playwright_available: bool | None = None,
) -> dict[str, Any]:
    """Return deterministic capability evidence for renderer planning."""

    system = platform_name or platform.system()
    powerpoint_value: str | bool = False
    keynote_value: str | bool = False
    browser_value: str | bool = False
    if system == "Darwin":
        powerpoint_value = app_exists("Microsoft PowerPoint.app")
        keynote_value = app_exists("Keynote.app")
        for app_name in ("Google Chrome.app", "Chromium.app", "Microsoft Edge.app"):
            if candidate := app_exists(app_name):
                if isinstance(candidate, str):
                    executable_names = {
                        "Google Chrome.app": "Google Chrome",
                        "Chromium.app": "Chromium",
                        "Microsoft Edge.app": "Microsoft Edge",
                    }
                    executable = Path(candidate) / "Contents" / "MacOS" / executable_names[app_name]
                    browser_value = str(executable) if executable.is_file() else candidate
                else:
                    browser_value = candidate
                break
    elif system == "Windows":
        powerpoint_value = which("POWERPNT.EXE") or which("powerpnt.exe") or False
        browser_value = which("chrome.exe") or which("msedge.exe") or False
    else:
        browser_value = which("google-chrome") or which("chromium") or which("chromium-browser") or False

    tools = {
        name: {"available": bool(path := which(name)), "path": path}
        for name in ("ffprobe", "ffmpeg", "node")
    }
    if playwright_available is None:
        playwright_available = _default_playwright_probe(tools["node"]["path"])
    tools["playwright"] = {
        "available": playwright_available,
        "path": None,
    }
    powerpoint = _application_record(powerpoint_value)
    keynote = _application_record(keynote_value)
    browser = _application_record(browser_value)
    pptx_levels = ["structural"]
    if powerpoint["available"]:
        pptx_levels.append("playback")
    web_playback = (
        tools["node"]["available"]
        and tools["playwright"]["available"]
        and browser["available"]
    )
    dual_playback = powerpoint["available"] and web_playback

    return {
        "protocol_version": PROTOCOL_VERSION,
        "platform": system,
        "applications": {
            "powerpoint": powerpoint,
            "keynote": keynote,
            "browser": browser,
        },
        "tools": tools,
        "video_validation": {
            "asset_structural": tools["ffprobe"]["available"],
            "rendered_video_tools": tools["ffprobe"]["available"]
            and tools["ffmpeg"]["available"],
            "error": None
            if tools["ffprobe"]["available"]
            else "VIDEO_TOOL_UNAVAILABLE",
        },
        "profiles": {
            "none": {
                "verification_levels": ["structural"],
                "playback_error": None,
            },
            "web_motion_v1": {
                "verification_levels": ["structural", "playback"]
                if web_playback
                else ["structural"],
                "playback_error": None
                if web_playback
                else "MOTION_TARGET_UNAVAILABLE",
            },
            "pptx_basic_v1": {
                "verification_levels": pptx_levels,
                "playback_error": None
                if powerpoint["available"]
                else "MOTION_TARGET_UNAVAILABLE",
            },
            "dual_motion_v1": {
                "verification_levels": ["structural", "playback"]
                if dual_playback
                else ["structural"],
                "playback_error": None if dual_playback else "MOTION_TARGET_UNAVAILABLE",
            },
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON output")
    parser.add_argument("--require-profile", choices=sorted(PROFILE_IDS))
    parser.add_argument("--verification", choices=sorted(VERIFICATION_LEVELS))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = inspect_capabilities()
    error = None
    if args.require_profile and args.verification:
        available = report["profiles"][args.require_profile]["verification_levels"]
        if args.verification not in available:
            error = {
                "code": "MOTION_TARGET_UNAVAILABLE",
                "profile_id": args.require_profile,
                "verification_required": args.verification,
            }
            report["error"] = error

    if args.json or error:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            "motion capabilities: "
            + ", ".join(
                f"{name}={','.join(data['verification_levels'])}"
                for name, data in report["profiles"].items()
            )
        )
    return 2 if error else 0


if __name__ == "__main__":
    sys.exit(main())

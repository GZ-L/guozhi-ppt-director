#!/usr/bin/env python3
"""Inspect a local video asset with ffprobe and emit machine-readable evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


def _error(code: str, message: str, evidence: str | None = None) -> dict[str, Any]:
    return {"code": code, "message": message, "evidence": evidence}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def inspect_video(
    path: Path,
    *,
    which: Callable[[str], str | None] = shutil.which,
    run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "path": str(path),
        "ok": False,
        "verification_level": None,
        "size_bytes": None,
        "checksum_sha256": None,
        "format": None,
        "duration_seconds": None,
        "video": None,
        "audio_streams": [],
        "errors": [],
    }
    if not path.is_file():
        report["errors"].append(
            _error("VIDEO_SOURCE_UNAVAILABLE", "video file does not exist", str(path))
        )
        return report
    ffprobe = which("ffprobe")
    if not ffprobe:
        report["errors"].append(
            _error("VIDEO_TOOL_UNAVAILABLE", "ffprobe is unavailable")
        )
        return report

    command = [
        ffprobe,
        "-v",
        "error",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        str(path),
    ]
    completed = run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        report["errors"].append(
            _error(
                "VIDEO_CODEC_UNSUPPORTED",
                "ffprobe could not read a valid video stream",
                completed.stderr.strip() or None,
            )
        )
        return report
    try:
        metadata = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        report["errors"].append(
            _error("VIDEO_CODEC_UNSUPPORTED", "ffprobe returned invalid JSON", str(exc))
        )
        return report

    streams = metadata.get("streams", [])
    video_stream = next(
        (stream for stream in streams if stream.get("codec_type") == "video"), None
    )
    if video_stream is None:
        report["errors"].append(
            _error("VIDEO_CODEC_UNSUPPORTED", "asset contains no video stream")
        )
        return report
    audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
    format_data = metadata.get("format", {})
    duration = _float(format_data.get("duration")) or _float(video_stream.get("duration"))
    report.update(
        {
            "size_bytes": path.stat().st_size,
            "checksum_sha256": _sha256(path),
            "format": format_data.get("format_name"),
            "duration_seconds": duration,
            "video": {
                "codec": video_stream.get("codec_name"),
                "profile": video_stream.get("profile"),
                "width": video_stream.get("width"),
                "height": video_stream.get("height"),
                "pixel_format": video_stream.get("pix_fmt"),
                "frame_rate": video_stream.get("avg_frame_rate"),
            },
            "audio_streams": [
                {
                    "codec": stream.get("codec_name"),
                    "channels": stream.get("channels"),
                    "sample_rate": stream.get("sample_rate"),
                }
                for stream in audio_streams
            ],
        }
    )
    if not duration or duration <= 0:
        report["errors"].append(
            _error("VIDEO_CODEC_UNSUPPORTED", "video duration is missing or zero")
        )
    report["ok"] = not report["errors"]
    report["verification_level"] = "structural" if report["ok"] else None
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--expect-audio", choices=["enabled", "muted"])
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = inspect_video(args.video)
    if report["ok"] and args.expect_audio == "enabled" and not report["audio_streams"]:
        report["errors"].append(
            _error("VIDEO_CODEC_UNSUPPORTED", "audio was required but no audio stream exists")
        )
    report["ok"] = not report["errors"]
    report["verification_level"] = "structural" if report["ok"] else None
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            f"video verification: ok={report['ok']} codec="
            f"{report['video']['codec'] if report['video'] else 'none'} "
            f"duration={report['duration_seconds']}"
        )
        for error in report["errors"]:
            print(f"ERROR {error['code']}: {error['message']}", file=sys.stderr)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Verify that every expected slide has a readable full-size PNG preview."""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from pathlib import Path
from typing import Any


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SLIDE_NAME = re.compile(r"^slide[-_]?0*(\d+)\.png$", re.IGNORECASE)


def png_dimensions(path: Path) -> tuple[int, int]:
    try:
        with path.open("rb") as stream:
            header = stream.read(24)
    except OSError as exc:
        raise ValueError(f"cannot read preview: {exc}") from exc
    if len(header) != 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        raise ValueError("not a valid PNG with an IHDR header")
    return struct.unpack(">II", header[16:24])


def inspect(preview_dir: Path, expected_slides: int, min_width: int, min_height: int) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    previews: dict[int, list[Path]] = {}
    if expected_slides < 1 or min_width < 1 or min_height < 1:
        return {"ok": False, "previews": [], "errors": [{"code": "PREVIEW_ARGUMENT_INVALID", "message": "counts and dimensions must be positive"}]}
    if not preview_dir.is_dir():
        return {"ok": False, "previews": [], "errors": [{"code": "PREVIEW_DIRECTORY_MISSING", "path": str(preview_dir)}]}

    for path in sorted(preview_dir.iterdir()):
        match = SLIDE_NAME.match(path.name)
        if match:
            previews.setdefault(int(match.group(1)), []).append(path)

    results: list[dict[str, Any]] = []
    for slide in range(1, expected_slides + 1):
        paths = previews.get(slide, [])
        if not paths:
            errors.append({"code": "PREVIEW_SLIDE_MISSING", "slide": slide})
            continue
        if len(paths) > 1:
            errors.append({"code": "PREVIEW_SLIDE_DUPLICATE", "slide": slide, "paths": [str(path) for path in paths]})
            continue
        path = paths[0]
        try:
            width, height = png_dimensions(path)
        except ValueError as exc:
            errors.append({"code": "PREVIEW_PNG_INVALID", "slide": slide, "path": str(path), "message": str(exc)})
            continue
        results.append({"slide": slide, "path": str(path), "width": width, "height": height})
        if width < min_width or height < min_height:
            errors.append(
                {
                    "code": "PREVIEW_RESOLUTION_TOO_LOW",
                    "slide": slide,
                    "path": str(path),
                    "actual": [width, height],
                    "required_minimum": [min_width, min_height],
                }
            )

    unexpected = sorted(slide for slide in previews if slide < 1 or slide > expected_slides)
    if unexpected:
        errors.append({"code": "PREVIEW_SLIDE_UNEXPECTED", "slides": unexpected})
    return {"ok": not errors, "expected_slides": expected_slides, "previews": results, "errors": errors}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview-dir", type=Path, required=True)
    parser.add_argument("--expected-slides", type=int, required=True)
    parser.add_argument("--min-width", type=int, default=1280)
    parser.add_argument("--min-height", type=int, default=720)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = inspect(args.preview_dir, args.expected_slides, args.min_width, args.min_height)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif report["ok"]:
        print(f"OK: verified {len(report['previews'])} full-size slide preview(s)")
    else:
        for error in report["errors"]:
            print(f"ERROR {error['code']}: {json.dumps(error, ensure_ascii=False)}", file=sys.stderr)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Resolve motion-plan object names to final exported PPTX shape IDs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile


P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS = {"p": P_NS}


def resolve_shape_ids(pptx: Path, plan_path: Path, output: Path) -> dict:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    slides = plan.get("slides")
    if not isinstance(slides, list) or not slides:
        raise ValueError("motion plan requires a non-empty slides list")

    try:
        archive = ZipFile(pptx)
    except (BadZipFile, OSError) as exc:
        raise ValueError(f"PPTX is not a readable ZIP package: {pptx}") from exc

    with archive:
        for slide_plan in slides:
            slide_number = slide_plan.get("slide")
            if not isinstance(slide_number, int) or slide_number < 1:
                raise ValueError("slide numbers must be positive integers")
            member = f"ppt/slides/slide{slide_number}.xml"
            try:
                root = ET.fromstring(archive.read(member))
            except KeyError as exc:
                raise ValueError(f"slide {slide_number} is absent from PPTX") from exc

            by_name: dict[str, list[int]] = {}
            for node in root.findall(".//p:cNvPr", NS):
                name = node.get("name")
                shape_id = node.get("id")
                if name and shape_id and shape_id.isdigit():
                    by_name.setdefault(name, []).append(int(shape_id))

            used: set[int] = set()
            groups = slide_plan.get("groups")
            if not isinstance(groups, list) or not groups:
                raise ValueError(f"slide {slide_number} requires motion groups")
            for group in groups:
                group_id = group.get("group_id")
                names = group.get("shape_names")
                if not isinstance(names, list) or not names:
                    raise ValueError(
                        f"slide {slide_number} group {group_id} requires shape_names"
                    )
                resolved: list[int] = []
                for name in names:
                    if not isinstance(name, str) or not name:
                        raise ValueError("shape_names entries must be non-empty strings")
                    matches = by_name.get(name, [])
                    if len(matches) != 1:
                        raise ValueError(
                            f"slide {slide_number} shape name {name!r} matched "
                            f"{len(matches)} exported objects"
                        )
                    shape_id = matches[0]
                    if shape_id in used:
                        raise ValueError(
                            f"slide {slide_number} shape ID {shape_id} appears in multiple groups"
                        )
                    used.add(shape_id)
                    resolved.append(shape_id)
                group["shape_ids"] = resolved

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "ok": True,
        "pptx": str(pptx),
        "plan": str(output),
        "slides": len(slides),
        "groups": sum(len(slide["groups"]) for slide in slides),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pptx", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = resolve_shape_ids(args.pptx, args.plan, args.output)
    except Exception as exc:
        print(
            json.dumps(
                {"ok": False, "code": "MOTION_TARGET_RESOLUTION_FAILED", "error": str(exc)},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

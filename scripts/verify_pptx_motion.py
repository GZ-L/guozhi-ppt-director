#!/usr/bin/env python3
"""Verify PPTX motion targets, transitions, and video package relationships."""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile


P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"p": P_NS, "a": A_NS, "r": R_NS, "pr": PKG_REL_NS}
SLIDE_RE = re.compile(r"^ppt/slides/slide(\d+)\.xml$")


def _error(
    code: str, message: str, *, slide: int | None = None, evidence: str | None = None
) -> dict[str, Any]:
    return {"code": code, "message": message, "slide": slide, "evidence": evidence}


def _parse_xml(archive: ZipFile, name: str) -> ET.Element:
    return ET.fromstring(archive.read(name))


def _relationship_path(slide_path: str) -> str:
    directory, filename = posixpath.split(slide_path)
    return posixpath.join(directory, "_rels", filename + ".rels")


def _resolve_relationship_target(slide_path: str, target: str) -> str:
    return posixpath.normpath(posixpath.join(posixpath.dirname(slide_path), target))


def inspect_pptx(path: Path) -> dict[str, Any]:
    report: dict[str, Any] = {
        "path": str(path),
        "ok": False,
        "verification_level": None,
        "slide_count": 0,
        "transition_slides": [],
        "timing_slides": [],
        "targeted_shape_ids": {},
        "media_parts": [],
        "video_relationships": [],
        "errors": [],
    }
    if not path.is_file():
        report["errors"].append(
            _error("MOTION_STRUCTURE_INVALID", "PPTX file does not exist", evidence=str(path))
        )
        return report

    try:
        with ZipFile(path) as archive:
            names = set(archive.namelist())
            slide_entries = []
            for name in names:
                match = SLIDE_RE.match(name)
                if match:
                    slide_entries.append((int(match.group(1)), name))
            slide_entries.sort()
            report["slide_count"] = len(slide_entries)
            report["media_parts"] = sorted(
                name for name in names if name.startswith("ppt/media/") and not name.endswith("/")
            )

            if not slide_entries:
                report["errors"].append(
                    _error("MOTION_STRUCTURE_INVALID", "PPTX contains no slide XML parts")
                )

            for slide_number, slide_path in slide_entries:
                try:
                    root = _parse_xml(archive, slide_path)
                except ET.ParseError as exc:
                    report["errors"].append(
                        _error(
                            "MOTION_STRUCTURE_INVALID",
                            "slide XML is malformed",
                            slide=slide_number,
                            evidence=str(exc),
                        )
                    )
                    continue

                shape_ids = {
                    value
                    for element in root.findall(".//p:cNvPr", NS)
                    if (value := element.get("id")) is not None
                }
                if root.find("p:transition", NS) is not None:
                    report["transition_slides"].append(slide_number)
                if root.find("p:timing", NS) is not None:
                    report["timing_slides"].append(slide_number)

                targets: list[int] = []
                for target in root.findall(".//p:spTgt", NS):
                    shape_id = target.get("spid")
                    if shape_id is None:
                        report["errors"].append(
                            _error(
                                "MOTION_STRUCTURE_INVALID",
                                "animation target has no shape ID",
                                slide=slide_number,
                            )
                        )
                        continue
                    if shape_id not in shape_ids:
                        report["errors"].append(
                            _error(
                                "MOTION_STRUCTURE_INVALID",
                                "animation targets a shape that is absent from the slide",
                                slide=slide_number,
                                evidence=shape_id,
                            )
                        )
                    try:
                        targets.append(int(shape_id))
                    except ValueError:
                        report["errors"].append(
                            _error(
                                "MOTION_STRUCTURE_INVALID",
                                "animation shape ID is not numeric",
                                slide=slide_number,
                                evidence=shape_id,
                            )
                        )
                report["targeted_shape_ids"][str(slide_number)] = sorted(set(targets))

                rels_path = _relationship_path(slide_path)
                relationships: dict[str, dict[str, str]] = {}
                if rels_path in names:
                    try:
                        rel_root = _parse_xml(archive, rels_path)
                        for rel in rel_root.findall("pr:Relationship", NS):
                            rel_id = rel.get("Id")
                            if rel_id:
                                relationships[rel_id] = dict(rel.attrib)
                    except ET.ParseError as exc:
                        report["errors"].append(
                            _error(
                                "VIDEO_EMBED_FAILED",
                                "slide relationships XML is malformed",
                                slide=slide_number,
                                evidence=str(exc),
                            )
                        )

                linked_ids = {
                    element.get(f"{{{R_NS}}}link")
                    for element in root.findall(".//a:videoFile", NS)
                    if element.get(f"{{{R_NS}}}link")
                }
                video_rel_ids = {
                    rel_id
                    for rel_id, rel in relationships.items()
                    if rel.get("Type", "").rstrip("/").endswith("/video")
                }
                for rel_id in sorted(linked_ids | video_rel_ids):
                    rel = relationships.get(rel_id)
                    if rel is None:
                        report["errors"].append(
                            _error(
                                "VIDEO_EMBED_FAILED",
                                "video reference has no matching relationship",
                                slide=slide_number,
                                evidence=rel_id,
                            )
                        )
                        continue
                    target = rel.get("Target", "")
                    external = rel.get("TargetMode") == "External"
                    resolved = None if external else _resolve_relationship_target(slide_path, target)
                    exists = external or bool(resolved and resolved in names)
                    report["video_relationships"].append(
                        {
                            "slide": slide_number,
                            "relationship_id": rel_id,
                            "target": target,
                            "external": external,
                            "resolved_part": resolved,
                            "exists": exists,
                        }
                    )
                    if not exists:
                        report["errors"].append(
                            _error(
                                "VIDEO_EMBED_FAILED",
                                "embedded video relationship target is missing",
                                slide=slide_number,
                                evidence=resolved,
                            )
                        )
    except (BadZipFile, OSError) as exc:
        report["errors"].append(
            _error(
                "MOTION_STRUCTURE_INVALID",
                "file is not a readable PPTX package",
                evidence=str(exc),
            )
        )
        return report

    report["ok"] = not report["errors"]
    report["verification_level"] = "structural" if report["ok"] else None
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pptx", type=Path, required=True)
    parser.add_argument("--expect-transition", action="store_true")
    parser.add_argument("--expect-build", action="store_true")
    parser.add_argument("--expect-video", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = inspect_pptx(args.pptx)
    expectations = [
        (args.expect_transition, report["transition_slides"], "expected slide transition is missing"),
        (
            args.expect_build,
            any(report["targeted_shape_ids"].values()),
            "expected object build is missing",
        ),
        (args.expect_video, report["video_relationships"], "expected video relationship is missing"),
    ]
    for requested, evidence, message in expectations:
        if requested and not evidence:
            report["errors"].append(_error("MOTION_STRUCTURE_INVALID", message))
    report["ok"] = not report["errors"]
    report["verification_level"] = "structural" if report["ok"] else None

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            f"pptx motion verification: ok={report['ok']} "
            f"transitions={len(report['transition_slides'])} "
            f"timing={len(report['timing_slides'])} "
            f"videos={len(report['video_relationships'])}"
        )
        for error in report["errors"]:
            print(f"ERROR {error['code']}: {error['message']}", file=sys.stderr)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

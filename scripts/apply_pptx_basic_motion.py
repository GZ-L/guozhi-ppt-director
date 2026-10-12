#!/usr/bin/env python3
"""Apply the restricted pptx_basic_v1 motion profile to a clean PPTX package."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZIP_DEFLATED, ZipFile


P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS = {"p": P_NS}
SLIDE_RE = re.compile(r"^ppt/slides/slide(\d+)\.xml$")
EFFECT_FILTERS = {
    "fade": "fade",
    "wipe_left": "wipe(left)",
    "wipe_right": "wipe(right)",
    "wipe_up": "wipe(up)",
    "wipe_down": "wipe(down)",
    "slide_from_left": "slide(fromLeft)",
    "slide_from_right": "slide(fromRight)",
    "slide_from_top": "slide(fromTop)",
    "slide_from_bottom": "slide(fromBottom)",
}
SUPPORTED_EFFECTS = {"appear", *EFFECT_FILTERS}
SUPPORTED_TRIGGERS = {"on_click", "after_previous", "with_previous"}
SUPPORTED_TRANSITIONS = {"none", "fade"}
SUPPORTED_CHOREOGRAPHY_MODES = {"legacy_builds_v1", "in_slide_grouped_v1"}
GROUP_ID_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


class MotionPlanError(ValueError):
    """Raised when a plan exceeds the supported structural writer contract."""


def _validate_plan(plan: dict[str, Any]) -> list[dict[str, Any]]:
    if plan.get("profile_id") != "pptx_basic_v1":
        raise MotionPlanError("profile_id must be pptx_basic_v1")
    choreography_mode = plan.get("choreography_mode", "legacy_builds_v1")
    if choreography_mode not in SUPPORTED_CHOREOGRAPHY_MODES:
        raise MotionPlanError(f"unsupported choreography_mode: {choreography_mode}")
    slides = plan.get("slides")
    if not isinstance(slides, list) or not slides:
        raise MotionPlanError("slides must be a non-empty list")

    seen: set[int] = set()
    normalized: list[dict[str, Any]] = []
    total_group_count = 0
    for item in slides:
        if not isinstance(item, dict):
            raise MotionPlanError("each slide plan must be an object")
        slide = item.get("slide")
        if not isinstance(slide, int) or slide < 1 or slide in seen:
            raise MotionPlanError("slide numbers must be unique positive integers")
        seen.add(slide)
        transition = item.get("transition", "none")
        if transition not in SUPPORTED_TRANSITIONS:
            raise MotionPlanError(f"unsupported transition: {transition}")
        groups = item.get("groups")
        builds = item.get("builds", [])
        if groups is not None:
            if choreography_mode != "in_slide_grouped_v1":
                raise MotionPlanError("groups require choreography_mode in_slide_grouped_v1")
            if builds:
                raise MotionPlanError("a slide cannot combine groups and builds")
            if not isinstance(groups, list) or not groups:
                raise MotionPlanError("groups must be a non-empty list")
            motion_job = item.get("motion_job")
            if not isinstance(motion_job, str) or not motion_job.strip():
                raise MotionPlanError("grouped slides require a non-empty motion_job")
            builds = []
            group_ids: set[str] = set()
            grouped_shape_ids: set[int] = set()
            for group in groups:
                if not isinstance(group, dict):
                    raise MotionPlanError("each motion group must be an object")
                group_id = group.get("group_id")
                if not isinstance(group_id, str) or not GROUP_ID_RE.fullmatch(group_id):
                    raise MotionPlanError("group_id must use lowercase letters, numbers, hyphen, or underscore")
                if group_id in group_ids:
                    raise MotionPlanError(f"duplicate group_id: {group_id}")
                group_ids.add(group_id)
                intent = group.get("intent")
                if not isinstance(intent, str) or not intent.strip():
                    raise MotionPlanError(f"motion group {group_id} requires a non-empty intent")
                shape_ids = group.get("shape_ids")
                if not isinstance(shape_ids, list) or not shape_ids:
                    raise MotionPlanError(f"motion group {group_id} requires shape_ids")
                if any(not isinstance(shape_id, int) or shape_id < 1 for shape_id in shape_ids):
                    raise MotionPlanError("shape_id must be a positive integer")
                if len(shape_ids) != len(set(shape_ids)):
                    raise MotionPlanError(f"motion group {group_id} contains duplicate shape IDs")
                duplicate_shapes = sorted(set(shape_ids) & grouped_shape_ids)
                if duplicate_shapes:
                    raise MotionPlanError(f"shape IDs cannot belong to multiple groups: {duplicate_shapes}")
                grouped_shape_ids.update(shape_ids)
                effect = group.get("effect")
                trigger = group.get("trigger")
                duration = group.get("duration_ms", 400)
                if effect not in SUPPORTED_EFFECTS:
                    raise MotionPlanError(f"unsupported effect: {effect}")
                if trigger not in SUPPORTED_TRIGGERS:
                    raise MotionPlanError(f"unsupported trigger: {trigger}")
                if not isinstance(duration, int) or duration < 1 or duration > 60000:
                    raise MotionPlanError("duration_ms must be between 1 and 60000")
                for index, shape_id in enumerate(shape_ids):
                    builds.append(
                        {
                            "shape_id": shape_id,
                            "effect": effect,
                            "trigger": trigger if index == 0 else "with_previous",
                            "duration_ms": duration,
                        }
                    )
            group_count = len(groups)
            total_group_count += group_count
        else:
            if not isinstance(builds, list):
                raise MotionPlanError("builds must be a list")
            group_count = 0
        normalized_builds = []
        for build in builds:
            if not isinstance(build, dict):
                raise MotionPlanError("each build must be an object")
            shape_id = build.get("shape_id")
            effect = build.get("effect")
            trigger = build.get("trigger")
            duration = build.get("duration_ms", 400)
            if not isinstance(shape_id, int) or shape_id < 1:
                raise MotionPlanError("shape_id must be a positive integer")
            if effect not in SUPPORTED_EFFECTS:
                raise MotionPlanError(f"unsupported effect: {effect}")
            if trigger not in SUPPORTED_TRIGGERS:
                raise MotionPlanError(f"unsupported trigger: {trigger}")
            if not isinstance(duration, int) or duration < 1 or duration > 60000:
                raise MotionPlanError("duration_ms must be between 1 and 60000")
            normalized_builds.append(
                {
                    "shape_id": shape_id,
                    "effect": effect,
                    "trigger": trigger,
                    "duration_ms": duration,
                }
            )
        normalized.append(
            {
                "slide": slide,
                "transition": transition,
                "builds": normalized_builds,
                "group_count": group_count,
            }
        )
    if choreography_mode == "in_slide_grouped_v1" and total_group_count == 0:
        raise MotionPlanError("in_slide_grouped_v1 requires at least one motion group")
    return normalized


def _build_effect_xml(build: dict[str, Any], next_id: int) -> tuple[str, int]:
    shape_id = build["shape_id"]
    trigger = build["trigger"]
    node_type = {
        "on_click": "clickEffect",
        "after_previous": "afterEffect",
        "with_previous": "withEffect",
    }[trigger]
    delay = "indefinite" if trigger == "on_click" else "0"
    outer_id = next_id
    set_id = next_id + 1
    next_id += 2
    behaviors = (
        f'<p:set><p:cBhvr><p:cTn id="{set_id}" dur="1" fill="hold"/>'
        f'<p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>'
        '<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>'
        '</p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>'
    )
    filter_name = EFFECT_FILTERS.get(build["effect"])
    if filter_name:
        effect_id = next_id
        next_id += 1
        behaviors += (
            f'<p:animEffect transition="in" filter="{filter_name}"><p:cBhvr>'
            f'<p:cTn id="{effect_id}" dur="{build["duration_ms"]}" fill="hold"/>'
            f'<p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>'
            '</p:cBhvr></p:animEffect>'
        )
    xml = (
        f'<p:par><p:cTn id="{outer_id}" fill="hold" nodeType="{node_type}">'
        f'<p:stCondLst><p:cond delay="{delay}"/></p:stCondLst>'
        f'<p:childTnLst>{behaviors}</p:childTnLst>'
        '</p:cTn></p:par>'
    )
    return xml, next_id


def _timing_xml(builds: list[dict[str, Any]]) -> str:
    next_id = 3
    effects = []
    build_entries = []
    for build in builds:
        effect, next_id = _build_effect_xml(build, next_id)
        effects.append(effect)
        build_entries.append(f'<p:bldP spid="{build["shape_id"]}" grpId="0"/>')
    return (
        '<p:timing><p:tnLst><p:par>'
        '<p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">'
        '<p:childTnLst><p:seq concurrent="1" nextAc="seek">'
        '<p:cTn id="2" dur="indefinite" nodeType="mainSeq">'
        f'<p:childTnLst>{"".join(effects)}</p:childTnLst>'
        '</p:cTn></p:seq></p:childTnLst></p:cTn>'
        '</p:par></p:tnLst>'
        f'<p:bldLst>{"".join(build_entries)}</p:bldLst>'
        '</p:timing>'
    )


def _patch_slide(xml_bytes: bytes, item: dict[str, Any]) -> bytes:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise MotionPlanError(f"slide XML is malformed: {exc}") from exc
    if root.find("p:timing", NS) is not None:
        raise MotionPlanError("existing timing tree is not modified by pptx_basic_v1")
    if root.find("p:transition", NS) is not None:
        raise MotionPlanError("existing transition is not modified by pptx_basic_v1")

    shape_ids = {
        int(value)
        for element in root.findall(".//p:cNvPr", NS)
        if (value := element.get("id")) is not None and value.isdigit()
    }
    missing = sorted(
        {build["shape_id"] for build in item["builds"] if build["shape_id"] not in shape_ids}
    )
    if missing:
        raise MotionPlanError(f"shape IDs are absent from slide: {missing}")

    additions = ""
    if item["transition"] == "fade":
        additions += '<p:transition spd="med" advClick="1"><p:fade/></p:transition>'
    if item["builds"]:
        additions += _timing_xml(item["builds"])
    if not additions:
        return xml_bytes

    text = xml_bytes.decode("utf-8")
    marker = "<p:extLst"
    if root.find("p:extLst", NS) is not None:
        position = text.rfind(marker)
        if position < 0:
            raise MotionPlanError("root extension list cannot be located in source XML")
        text = text[:position] + additions + text[position:]
    elif "</p:sld>" in text:
        text = text.replace("</p:sld>", additions + "</p:sld>", 1)
    else:
        raise MotionPlanError("slide XML has no supported insertion point")
    return text.encode("utf-8")


def apply_motion(input_path: Path, plan: dict[str, Any], output_path: Path) -> dict[str, Any]:
    input_path = input_path.resolve()
    output_path = output_path.resolve()
    if input_path == output_path:
        raise MotionPlanError("output must be different from input")
    if not input_path.is_file():
        raise MotionPlanError("input PPTX does not exist")
    slides = _validate_plan(plan)
    plan_by_path = {f"ppt/slides/slide{item['slide']}.xml": item for item in slides}
    output_path.parent.mkdir(parents=True, exist_ok=True)

    temporary: Path | None = None
    try:
        with ZipFile(input_path) as source:
            names = set(source.namelist())
            missing_slides = sorted(path for path in plan_by_path if path not in names)
            if missing_slides:
                raise MotionPlanError(f"planned slides are absent from PPTX: {missing_slides}")
            with tempfile.NamedTemporaryFile(
                dir=output_path.parent, prefix=output_path.name + ".", suffix=".tmp", delete=False
            ) as handle:
                temporary = Path(handle.name)
            with ZipFile(temporary, "w", ZIP_DEFLATED) as target:
                for info in source.infolist():
                    data = source.read(info.filename)
                    if info.filename in plan_by_path:
                        data = _patch_slide(data, plan_by_path[info.filename])
                    target.writestr(info, data)
        os.replace(temporary, output_path)
        temporary = None
    except (BadZipFile, OSError) as exc:
        raise MotionPlanError(f"cannot rewrite PPTX package: {exc}") from exc
    finally:
        if temporary and temporary.exists():
            temporary.unlink()

    return {
        "ok": True,
        "profile_id": "pptx_basic_v1",
        "choreography_mode": plan.get("choreography_mode", "legacy_builds_v1"),
        "group_count": sum(item["group_count"] for item in slides),
        "input": str(input_path),
        "output": str(output_path),
        "slides_modified": [item["slide"] for item in slides],
        "verification_level": "declared",
        "next_action": "run scripts/verify_pptx_motion.py for structural verification",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        result = apply_motion(args.input, plan, args.output)
    except (OSError, json.JSONDecodeError, MotionPlanError) as exc:
        error = {"ok": False, "code": "MOTION_STRUCTURE_INVALID", "message": str(exc)}
        print(json.dumps(error, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"wrote {result['output']} with profile {result['profile_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

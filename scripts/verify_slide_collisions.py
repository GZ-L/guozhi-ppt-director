#!/usr/bin/env python3
"""Verify declared slide surfaces do not overlap in rendered layout JSON."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc


def normalize_bbox(value: Any) -> list[float] | None:
    if isinstance(value, list) and len(value) == 4:
        try:
            return [float(item) for item in value]
        except (TypeError, ValueError):
            return None
    if isinstance(value, dict):
        keys = ("left", "top", "width", "height")
        try:
            return [float(value[key]) for key in keys]
        except (KeyError, TypeError, ValueError):
            return None
    return None


def overlap_metrics(first: list[float], second: list[float]) -> dict[str, float]:
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    return {
        "x_overlap_px": min(ax + aw, bx + bw) - max(ax, bx),
        "y_overlap_px": min(ay + ah, by + bh) - max(ay, by),
    }


def inspect(layout_dir: Path, rules_path: Path) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    try:
        rules = load_json(rules_path)
    except ValueError as exc:
        return {"ok": False, "checked_slides": 0, "checks": [], "errors": [{"code": "COLLISION_RULES_INVALID", "message": str(exc)}]}

    slide_rules = rules.get("slides") if isinstance(rules, dict) else None
    if not isinstance(slide_rules, list) or not slide_rules:
        return {"ok": False, "checked_slides": 0, "checks": [], "errors": [{"code": "COLLISION_RULES_INVALID", "message": "rules.slides must be a non-empty array"}]}

    layout_files = sorted(layout_dir.glob("*.layout.json"))
    layouts: dict[int, tuple[Path, dict[str, Any]]] = {}
    for path in layout_files:
        try:
            payload = load_json(path)
        except ValueError as exc:
            errors.append({"code": "LAYOUT_JSON_INVALID", "message": str(exc), "path": str(path)})
            continue
        slide_number = payload.get("slide", {}).get("slide") if isinstance(payload, dict) else None
        if isinstance(slide_number, int):
            layouts[slide_number] = (path, payload)

    for rule in slide_rules:
        if not isinstance(rule, dict) or not isinstance(rule.get("slide"), int):
            errors.append({"code": "COLLISION_RULES_INVALID", "message": "every slide rule requires an integer slide"})
            continue
        slide_number = rule["slide"]
        groups = rule.get("groups")
        min_gap = rule.get("min_gap_px", 0)
        scopes = rule.get("scopes", ["slide"])
        if not isinstance(groups, list) or len(groups) < 2 or not all(isinstance(item, str) for item in groups):
            errors.append({"code": "COLLISION_RULES_INVALID", "slide": slide_number, "message": "groups must contain at least two regex strings"})
            continue
        if not isinstance(min_gap, (int, float)) or min_gap < 0:
            errors.append({"code": "COLLISION_RULES_INVALID", "slide": slide_number, "message": "min_gap_px must be zero or greater"})
            continue
        try:
            patterns = [re.compile(item) for item in groups]
        except re.error as exc:
            errors.append({"code": "COLLISION_RULES_INVALID", "slide": slide_number, "message": f"invalid group regex: {exc}"})
            continue

        layout_entry = layouts.get(slide_number)
        if layout_entry is None:
            errors.append({"code": "LAYOUT_SLIDE_MISSING", "slide": slide_number, "message": "no layout JSON found for declared slide"})
            continue
        path, payload = layout_entry
        selected: list[dict[str, Any]] = []
        for element in payload.get("elements", []):
            if not isinstance(element, dict) or element.get("scope", "slide") not in scopes:
                continue
            name = element.get("name")
            bbox = normalize_bbox(element.get("bbox"))
            matched_groups = [index for index, pattern in enumerate(patterns) if isinstance(name, str) and pattern.search(name)]
            if matched_groups and bbox is not None:
                selected.append({"name": name, "bbox": bbox, "groups": matched_groups})

        missing_groups = [groups[index] for index in range(len(groups)) if not any(index in item["groups"] for item in selected)]
        if missing_groups:
            errors.append({"code": "COLLISION_RULE_NO_MATCH", "slide": slide_number, "patterns": missing_groups, "path": str(path)})

        pair_count = 0
        for index, first in enumerate(selected):
            for second in selected[index + 1 :]:
                pair_count += 1
                metrics = overlap_metrics(first["bbox"], second["bbox"])
                if metrics["x_overlap_px"] > -float(min_gap) and metrics["y_overlap_px"] > -float(min_gap):
                    errors.append(
                        {
                            "code": "SLIDE_COLLISION",
                            "slide": slide_number,
                            "first": {"name": first["name"], "bbox": first["bbox"]},
                            "second": {"name": second["name"], "bbox": second["bbox"]},
                            "min_gap_px": min_gap,
                            **metrics,
                            "path": str(path),
                        }
                    )
        checks.append({"slide": slide_number, "selected_surfaces": len(selected), "checked_pairs": pair_count, "min_gap_px": min_gap})

    return {"ok": not errors, "checked_slides": len(checks), "checks": checks, "errors": errors}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layout-dir", type=Path, required=True)
    parser.add_argument("--rules", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = inspect(args.layout_dir, args.rules)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif report["ok"]:
        print(f"OK: checked {report['checked_slides']} slide collision rule(s)")
    else:
        for error in report["errors"]:
            print(f"ERROR {error['code']}: {json.dumps(error, ensure_ascii=False)}", file=sys.stderr)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

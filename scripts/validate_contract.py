#!/usr/bin/env python3
"""Validate Guozhi PPT Director runtime contracts and optional local style assets."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_VERSION = "1.0"
REQUIRED_OPERATIONS = {
    "deck.create",
    "deck.revise",
    "deck.review",
    "style.list",
    "style.add",
    "style.update",
    "style.remove",
    "help",
}
REQUIRED_ROUTES = {"native_pptx", "web_deck", "dual", "dashiai", "review_only"}
REQUIRED_STATES = {
    "received",
    "normalized",
    "needs_input",
    "confirmed",
    "planned",
    "rendering",
    "qa",
    "completed",
    "blocked",
    "failed",
}
RUNTIME_DOCS = [
    "SKILL.md",
    "CALLING_SPEC.md",
    "OVERVIEW.md",
    "references/question-layer.md",
    "references/output-routes.md",
    "references/dashiai-adapter.md",
    "templates/user-confirmation.md",
    "templates/production-route.md",
]
FORBIDDEN_RUNTIME_TOKENS = [
    "Route " + letter + ":" for letter in "ABCDE"
] + ["Route E/B", "确认 A/B/C", '"方案 B"']


def load_json(relative: str, errors: list[str]) -> dict[str, Any]:
    path = ROOT / relative
    if not path.is_file():
        errors.append(f"missing JSON contract: {relative}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON {relative}: {exc}")
        return {}


def enum_values(schema: dict[str, Any], field: str) -> set[str]:
    values = schema.get("properties", {}).get(field, {}).get("enum", [])
    return {str(value) for value in values}


def validate_registry(errors: list[str]) -> None:
    registry = load_json("contracts/route-registry.json", errors)
    if registry.get("protocol_version") != PROTOCOL_VERSION:
        errors.append("route registry protocol_version must be 1.0")
    routes = registry.get("routes", [])
    ids = [item.get("id") for item in routes if isinstance(item, dict)]
    if len(ids) != len(set(ids)):
        errors.append("route registry contains duplicate IDs")
    if set(ids) != REQUIRED_ROUTES:
        errors.append(f"route registry IDs differ: {sorted(set(ids))}")


def validate_schemas(errors: list[str]) -> None:
    invocation = load_json("contracts/invocation.schema.json", errors)
    result = load_json("contracts/result.schema.json", errors)
    manifest = load_json("templates/run-manifest.json", errors)

    if invocation.get("properties", {}).get("protocol_version", {}).get("const") != PROTOCOL_VERSION:
        errors.append("invocation schema protocol_version must be 1.0")
    if result.get("properties", {}).get("protocol_version", {}).get("const") != PROTOCOL_VERSION:
        errors.append("result schema protocol_version must be 1.0")
    if manifest.get("protocol_version") != PROTOCOL_VERSION:
        errors.append("run manifest protocol_version must be 1.0")

    if enum_values(invocation, "operation") != REQUIRED_OPERATIONS:
        errors.append("invocation operation enum differs from required operations")
    if enum_values(result, "operation") != REQUIRED_OPERATIONS:
        errors.append("result operation enum differs from required operations")
    if enum_values(result, "status") != REQUIRED_STATES:
        errors.append("result status enum differs from required states")

    route_enum = set(
        invocation.get("properties", {})
        .get("constraints", {})
        .get("properties", {})
        .get("route_id", {})
        .get("enum", [])
    )
    if route_enum != REQUIRED_ROUTES:
        errors.append("invocation route enum differs from route registry")


def validate_runtime_docs(errors: list[str]) -> None:
    combined = []
    for relative in RUNTIME_DOCS:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing runtime document: {relative}")
            continue
        combined.append(path.read_text(encoding="utf-8"))
    text = "\n".join(combined)
    for token in FORBIDDEN_RUNTIME_TOKENS:
        if token in text:
            errors.append(f"ambiguous runtime token found: {token}")

    calling = (ROOT / "CALLING_SPEC.md").read_text(encoding="utf-8")
    for token in REQUIRED_OPERATIONS | REQUIRED_ROUTES | REQUIRED_STATES | {"run_id", "interaction_mode"}:
        if token not in calling:
            errors.append(f"CALLING_SPEC.md missing identifier: {token}")


def validate_references(errors: list[str], require_style_assets: bool) -> None:
    pattern = re.compile(r"`((?:references|templates|scripts|contracts|assets)/[^`\s]+)`")
    for path in ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            relative = match.group(1).rstrip("),.;:")
            if "<" in relative or "*" in relative:
                continue
            if not (ROOT / relative).exists() and not (
                relative.startswith("assets/") and not require_style_assets
            ):
                errors.append(f"broken reference in {path.relative_to(ROOT)}: {relative}")


def validate_style_assets(
    errors: list[str], warnings: list[str], require_style_assets: bool
) -> None:
    index = load_json("references/style-library/style-pack-index.json", errors)
    packs = [item for item in index.get("packs", []) if isinstance(item, dict)]
    indexed = {str(item.get("pack_id")) for item in packs}
    pack_root = ROOT / "assets" / "style-library" / "style-packs"
    if not pack_root.is_dir():
        if require_style_assets:
            errors.append("missing style pack directory: assets/style-library/style-packs")
        else:
            warnings.append("style bitmap snapshot is not included in this source checkout")
        return

    directories = {path.name for path in pack_root.iterdir() if path.is_dir()}
    if indexed != directories:
        errors.append(
            f"style pack index/directory mismatch: indexed={sorted(indexed)} directories={sorted(directories)}"
        )
    expected_assets: list[str] = []
    for pack in packs:
        for asset in pack.get("assets", []):
            relative = asset.get("asset_path")
            if isinstance(relative, str):
                expected_assets.append(relative)
            else:
                errors.append(f"missing style asset: {relative}")

    present_assets = [relative for relative in expected_assets if (ROOT / relative).is_file()]
    if not present_assets and expected_assets and not require_style_assets:
        warnings.append(
            "style bitmap snapshot is local-only; manifests and source links were validated"
        )
        return

    for relative in expected_assets:
        if not (ROOT / relative).is_file():
            errors.append(f"missing style asset: {relative}")


def validate_portability(errors: list[str]) -> None:
    extractor = (ROOT / "scripts" / "extract_style_pack_refs.py").read_text(encoding="utf-8")
    if re.search(r"/Users/[^/]+/", extractor):
        errors.append("extract_style_pack_refs.py contains a user-specific path")
    for relative in ["scripts/collect_style_refs.py", "scripts/extract_zcool_style_pack.py"]:
        if "_create_unverified_context" in (ROOT / relative).read_text(encoding="utf-8"):
            errors.append(f"TLS verification disabled in {relative}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-style-assets",
        action="store_true",
        help="fail unless every style bitmap referenced by the manifest exists locally",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    warnings: list[str] = []
    validate_registry(errors)
    validate_schemas(errors)
    validate_runtime_docs(errors)
    validate_references(errors, args.require_style_assets)
    validate_style_assets(errors, warnings, args.require_style_assets)
    validate_portability(errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FAILED: {len(errors)} contract error(s)", file=sys.stderr)
        return 1
    for warning in warnings:
        print(f"WARNING: {warning}")
    print("OK: guozhi-ppt-director protocol 1.0 contracts and style assets are consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

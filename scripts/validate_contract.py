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
PROTOCOL_VERSION = "1.1"
ACCEPTED_INVOCATION_VERSIONS = {"1.0", "1.1"}
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
REQUIRED_MOTION_PROFILES = {
    "none",
    "web_motion_v1",
    "pptx_basic_v1",
    "dual_motion_v1",
}
ROUTE_MOTION_PROFILES = {
    "native_pptx": {"none", "pptx_basic_v1"},
    "web_deck": {"none", "web_motion_v1"},
    "dual": {"none", "dual_motion_v1"},
    "dashiai": {"none"},
    "review_only": {"none"},
}
ROUTE_VIDEO_DELIVERIES = {
    "native_pptx": {"embedded", "linked"},
    "web_deck": {"web", "rendered_video"},
    "dual": {"embedded", "linked", "web"},
    "dashiai": set(),
    "review_only": set(),
}
REQUIRED_MOTION_SCRIPTS = {
    "scripts/check_motion_capabilities.py",
    "scripts/resolve_pptx_motion_shape_ids.py",
    "scripts/apply_pptx_basic_motion.py",
    "scripts/verify_pptx_motion.py",
    "scripts/verify_video_asset.py",
    "scripts/verify_web_motion.mjs",
    "scripts/validate_runtime_payload.py",
}
REQUIRED_AGENT_CONTRACTS = {
    "contracts/intent-registry.json",
    "contracts/capability-handoff.schema.json",
    "contracts/run-manifest.schema.json",
    "contracts/style-selection.schema.json",
    "contracts/media-plan.schema.json",
    "templates/capability-handoff.json",
    "templates/media-capability-handoff.json",
    "templates/media-plan.json",
    "templates/motion-plan.json",
    "templates/style-selection.json",
}
REQUIRED_VISUAL_QA_FILES = {
    "scripts/verify_slide_collisions.py",
    "scripts/verify_slide_previews.py",
    "templates/collision-rules.json",
}
REQUIRED_VISUAL_QA_TOKENS = {
    "full-size slide preview",
    "montage is navigation only",
    "collision verification",
    "Static PPTX, no animation",
    "playback verification",
}
REQUIRED_DEFECT_LOOP_TOKENS = {
    "user-reported defect",
    "minimal reproducer",
    "failing regression test",
    "authority files",
    "dependent files",
    "full validation",
    "artifact-only fix is incomplete",
}
REQUIRED_MOTION_CHOREOGRAPHY_TOKENS = {
    "in-slide choreography",
    "grouped builds",
    "transition-only is insufficient",
    "semantic checkpoints",
    "motion-plan.json",
    "stable object names",
    "all-fade",
}
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
REQUIRED_HANDOFF_ROLES = {
    "source_adapter",
    "media_generator",
    "renderer",
    "visual_qa",
}
RUNTIME_DOCS = [
    "SKILL.md",
    "CALLING_SPEC.md",
    "OVERVIEW.md",
    "references/question-layer.md",
    "references/intent-routing.md",
    "references/output-routes.md",
    "references/motion-video-delivery.md",
    "references/visual-intent-analysis.md",
    "references/xiaohu-ip-studio-adapter.md",
    "references/qa-checklist.md",
    "references/dashiai-adapter.md",
    "templates/user-confirmation.md",
    "templates/production-route.md",
    "templates/qa-report.md",
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
        errors.append(f"route registry protocol_version must be {PROTOCOL_VERSION}")
    routes = registry.get("routes", [])
    ids = [item.get("id") for item in routes if isinstance(item, dict)]
    if len(ids) != len(set(ids)):
        errors.append("route registry contains duplicate IDs")
    if set(ids) != REQUIRED_ROUTES:
        errors.append(f"route registry IDs differ: {sorted(set(ids))}")
    by_id = {item.get("id"): item for item in routes if isinstance(item, dict)}
    for route_id in REQUIRED_ROUTES:
        route = by_id.get(route_id, {})
        profiles = set(route.get("motion_profiles", []))
        deliveries = set(route.get("video_deliveries", []))
        if profiles != ROUTE_MOTION_PROFILES[route_id]:
            errors.append(f"route {route_id} motion_profiles differ from registry contract")
        if deliveries != ROUTE_VIDEO_DELIVERIES[route_id]:
            errors.append(f"route {route_id} video_deliveries differ from registry contract")


def validate_schemas(errors: list[str]) -> None:
    invocation = load_json("contracts/invocation.schema.json", errors)
    result = load_json("contracts/result.schema.json", errors)
    handoff = load_json("contracts/capability-handoff.schema.json", errors)
    manifest_schema = load_json("contracts/run-manifest.schema.json", errors)
    style_selection_schema = load_json("contracts/style-selection.schema.json", errors)
    media_plan_schema = load_json("contracts/media-plan.schema.json", errors)
    intent = load_json("contracts/intent-registry.json", errors)
    manifest = load_json("templates/run-manifest.json", errors)
    handoff_template = load_json("templates/capability-handoff.json", errors)
    media_handoff_template = load_json("templates/media-capability-handoff.json", errors)
    style_selection_template = load_json("templates/style-selection.json", errors)
    media_plan_template = load_json("templates/media-plan.json", errors)
    motion_plan_template = load_json("templates/motion-plan.json", errors)

    invocation_versions = set(
        invocation.get("properties", {}).get("protocol_version", {}).get("enum", [])
    )
    if invocation_versions != ACCEPTED_INVOCATION_VERSIONS:
        errors.append("invocation schema must accept protocol versions 1.0 and 1.1")
    if result.get("properties", {}).get("protocol_version", {}).get("const") != PROTOCOL_VERSION:
        errors.append(f"result schema protocol_version must be {PROTOCOL_VERSION}")
    if manifest.get("protocol_version") != PROTOCOL_VERSION:
        errors.append(f"run manifest protocol_version must be {PROTOCOL_VERSION}")
    if (
        manifest_schema.get("properties", {})
        .get("protocol_version", {})
        .get("const")
        != PROTOCOL_VERSION
    ):
        errors.append(f"run manifest schema protocol_version must be {PROTOCOL_VERSION}")
    if handoff.get("properties", {}).get("protocol_version", {}).get("const") != PROTOCOL_VERSION:
        errors.append(f"capability handoff protocol_version must be {PROTOCOL_VERSION}")
    if handoff_template.get("protocol_version") != PROTOCOL_VERSION:
        errors.append(f"capability handoff template protocol_version must be {PROTOCOL_VERSION}")
    if media_handoff_template.get("role") != "media_generator":
        errors.append("media capability handoff template role must be media_generator")
    if media_handoff_template.get("input", {}).get("generation_scope") not in {
        "baseline_preview",
        "production_assets",
    }:
        errors.append("media capability handoff template requires a valid generation_scope")
    media_context = media_handoff_template.get("director_context", {})
    for field in ["media_plan_path", "media_plan_digest", "confirmation_status"]:
        if not media_context.get(field):
            errors.append(f"media capability handoff template missing {field}")
    if intent.get("protocol_version") != PROTOCOL_VERSION:
        errors.append(f"intent registry protocol_version must be {PROTOCOL_VERSION}")
    if (
        style_selection_schema.get("properties", {})
        .get("protocol_version", {})
        .get("const")
        != PROTOCOL_VERSION
    ):
        errors.append(f"style selection schema protocol_version must be {PROTOCOL_VERSION}")
    if style_selection_template.get("protocol_version") != PROTOCOL_VERSION:
        errors.append(f"style selection template protocol_version must be {PROTOCOL_VERSION}")
    if (
        media_plan_schema.get("properties", {})
        .get("protocol_version", {})
        .get("const")
        != PROTOCOL_VERSION
    ):
        errors.append(f"media plan schema protocol_version must be {PROTOCOL_VERSION}")
    if media_plan_template.get("protocol_version") != PROTOCOL_VERSION:
        errors.append(f"media plan template protocol_version must be {PROTOCOL_VERSION}")
    for field, expected in {
        "style_authority": "ppt_style_lock",
        "source_precedence": "authorized_source_first",
        "text_policy": "editable_ppt_text",
        "media_treatment_authority": "style_pack_assets",
        "fallback_image_form_policy": "visual_intent_only",
    }.items():
        if media_plan_template.get(field) != expected:
            errors.append(f"media plan template {field} must be {expected}")
    if not media_plan_template.get("media_treatment_references"):
        errors.append("media plan template requires media_treatment_references")
    if motion_plan_template.get("profile_id") != "pptx_basic_v1":
        errors.append("motion plan template profile_id must be pptx_basic_v1")
    if motion_plan_template.get("choreography_mode") != "in_slide_grouped_v1":
        errors.append("motion plan template must use in_slide_grouped_v1")
    motion_plan_slides = motion_plan_template.get("slides", [])
    if not motion_plan_slides or not motion_plan_slides[0].get("groups"):
        errors.append("motion plan template must contain grouped in-slide choreography")

    if enum_values(invocation, "operation") != REQUIRED_OPERATIONS:
        errors.append("invocation operation enum differs from required operations")
    if enum_values(result, "operation") != REQUIRED_OPERATIONS:
        errors.append("result operation enum differs from required operations")
    if enum_values(result, "status") != REQUIRED_STATES:
        errors.append("result status enum differs from required states")
    intent_operations = {
        item.get("id") for item in intent.get("operations", []) if isinstance(item, dict)
    }
    if intent_operations != REQUIRED_OPERATIONS:
        errors.append("intent registry operations differ from required operations")
    if enum_values(handoff, "role") != REQUIRED_HANDOFF_ROLES:
        errors.append("capability handoff roles differ from required roles")

    route_enum = set(
        invocation.get("properties", {})
        .get("constraints", {})
        .get("properties", {})
        .get("route_id", {})
        .get("enum", [])
    )
    if route_enum != REQUIRED_ROUTES:
        errors.append("invocation route enum differs from route registry")

    motion_profiles = set(
        invocation.get("properties", {})
        .get("constraints", {})
        .get("properties", {})
        .get("motion", {})
        .get("properties", {})
        .get("profile_id", {})
        .get("enum", [])
    )
    if motion_profiles != REQUIRED_MOTION_PROFILES:
        errors.append("invocation motion profiles differ from required profiles")
    if "theme_id" not in (
        invocation.get("properties", {})
        .get("constraints", {})
        .get("properties", {})
    ):
        errors.append("invocation schema missing theme_id")

    verification_levels = set(
        result.get("properties", {})
        .get("verification", {})
        .get("items", {})
        .get("properties", {})
        .get("level", {})
        .get("enum", [])
    )
    if verification_levels != {"declared", "structural", "playback"}:
        errors.append("result verification levels differ from required levels")
    result_required = set(result.get("required", []))
    expected_result_required = {
        "protocol_version",
        "request_id",
        "run_id",
        "operation",
        "status",
        "resolved_decisions",
        "unresolved_fields",
        "proposed_decisions",
        "artifacts",
        "verification",
        "warnings",
        "error",
        "next_action",
    }
    if result_required != expected_result_required:
        errors.append("result schema does not require the complete Agent envelope")
    if manifest.get("resolved_decisions", {}).get("motion", {}).get("profile_id") != "none":
        errors.append("run manifest static default motion profile must be none")
    if manifest.get("resolved_decisions", {}).get("video", {}).get("requested") is not False:
        errors.append("run manifest static default video requested must be false")
    if "theme_id" not in manifest.get("resolved_decisions", {}):
        errors.append("run manifest missing theme_id decision")
    if manifest.get("state_history") != ["received"]:
        errors.append("run manifest state_history must start with received")
    manifest_required = set(manifest_schema.get("required", []))
    if "state_history" not in manifest_required:
        errors.append("run manifest schema must require state_history")
    manifest_states = set(
        manifest_schema.get("properties", {})
        .get("state_history", {})
        .get("items", {})
        .get("enum", [])
    )
    if manifest_states != REQUIRED_STATES:
        errors.append("run manifest state_history enum differs from required states")
    candidate_schema = (
        style_selection_schema.get("properties", {}).get("candidates", {})
    )
    if candidate_schema.get("minItems") != 3 or candidate_schema.get("maxItems") != 3:
        errors.append("style selection schema must require exactly three candidates")
    if (
        style_selection_schema.get("properties", {})
        .get("selection_method", {})
        .get("const")
        != "deterministic_fit_diversity_v1"
    ):
        errors.append("style selection method must be deterministic_fit_diversity_v1")
    if len(style_selection_template.get("candidates", [])) != 3:
        errors.append("style selection template must contain exactly three candidates")


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
    for token in REQUIRED_VISUAL_QA_TOKENS:
        if token not in text:
            errors.append(f"runtime documents missing visual QA rule: {token}")
    for token in REQUIRED_MOTION_CHOREOGRAPHY_TOKENS:
        if token.lower() not in text.lower():
            errors.append(f"runtime documents missing motion choreography rule: {token}")

    maintenance = (ROOT / "MAINTENANCE_SPEC.md").read_text(encoding="utf-8").lower()
    for token in REQUIRED_DEFECT_LOOP_TOKENS:
        if token.lower() not in maintenance:
            errors.append(f"MAINTENANCE_SPEC.md missing defect-loop rule: {token}")


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
    families = [item.get("visual_family") for item in packs]
    if any(not isinstance(family, str) or not family for family in families):
        errors.append("every style pack must declare a visual_family")
    if len(families) != len(set(families)):
        errors.append("style pack visual_family values must be unique")
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


def validate_motion_scripts(errors: list[str]) -> None:
    for relative in sorted(REQUIRED_MOTION_SCRIPTS):
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing motion capability script: {relative}")
    for relative in sorted(REQUIRED_AGENT_CONTRACTS):
        if not (ROOT / relative).is_file():
            errors.append(f"missing Agent contract: {relative}")
    for relative in sorted(REQUIRED_VISUAL_QA_FILES):
        if not (ROOT / relative).is_file():
            errors.append(f"missing visual QA file: {relative}")


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
    validate_motion_scripts(errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FAILED: {len(errors)} contract error(s)", file=sys.stderr)
        return 1
    for warning in warnings:
        print(f"WARNING: {warning}")
    print(
        f"OK: guozhi-ppt-director protocol {PROTOCOL_VERSION} contracts and style assets are consistent"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

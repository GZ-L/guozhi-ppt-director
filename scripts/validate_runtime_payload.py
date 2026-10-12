#!/usr/bin/env python3
"""Validate invocation, manifest, result, handoff, and style-selection rules."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_VERSION = "1.1"
OPERATIONS = {
    "deck.create",
    "deck.revise",
    "deck.review",
    "style.list",
    "style.add",
    "style.update",
    "style.remove",
    "help",
}
ROUTE_DELIVERABLES = {
    "native_pptx": {"pptx"},
    "web_deck": {"html"},
    "dual": {"dual"},
    "dashiai": {"pptx", "html", "pdf"},
    "review_only": {"review"},
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
HANDOFF_ROLES = {"source_adapter", "media_generator", "renderer", "visual_qa"}
HANDOFF_STATUSES = {"requested", "completed", "blocked", "failed"}
HANDOFF_ROLE_REQUIREMENTS = {
    "source_adapter": ({"sources"}, {"source_records"}),
    "media_generator": ({"media_slots", "generation_scope"}, {"assets"}),
    "renderer": ({"director_package", "output_path"}, {"artifacts"}),
    "visual_qa": ({"artifacts"}, {"findings", "passed"}),
}
RESULT_STATUSES = {
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
ALLOWED_TRANSITIONS = {
    "received": {"normalized", "blocked", "failed"},
    "normalized": {"needs_input", "confirmed", "blocked", "failed"},
    "needs_input": {"confirmed", "blocked"},
    "confirmed": {"planned", "blocked", "failed"},
    "planned": {"rendering", "blocked", "failed"},
    "rendering": {"qa", "blocked", "failed"},
    "qa": {"completed", "blocked", "failed"},
    "completed": set(),
    "blocked": set(),
    "failed": set(),
}
INVOCATION_FIELDS = {
    "protocol_version",
    "request_id",
    "run_id",
    "operation",
    "interaction_mode",
    "source",
    "constraints",
    "confirmation",
    "allow_defaults",
    "output_root",
}
CONSTRAINT_FIELDS = {
    "language",
    "page_count",
    "speaking_minutes",
    "deliverable",
    "route_id",
    "style_id",
    "theme_id",
    "rewrite_boundary",
    "speaker_notes",
    "citations",
    "allow_limited_style",
    "mutation_approved",
    "revision_scope",
    "motion",
    "video",
}
SOURCE_FIELDS = {"type", "location", "role"}
MOTION_FIELDS = {
    "requested",
    "profile_id",
    "playback_targets",
    "verification_required",
    "advance",
    "reduced_motion_fallback",
}
VIDEO_FIELDS = {
    "requested",
    "delivery",
    "playback",
    "audio",
    "loop",
    "poster_frame",
    "fallback",
    "assets",
}
VIDEO_ASSET_FIELDS = {
    "asset_id",
    "source",
    "page_id",
    "mime_type",
    "duration_seconds",
    "trim_start_seconds",
    "trim_end_seconds",
    "checksum_sha256",
}
HANDOFF_FIELDS = {
    "protocol_version",
    "request_id",
    "run_id",
    "capability_id",
    "role",
    "status",
    "producer",
    "input",
    "output",
    "version",
    "director_context",
    "error",
}
DIRECTOR_CONTEXT_FIELDS = {
    "route_id",
    "page_count",
    "style_lock",
    "story_digest",
    "layout_contract_path",
    "media_plan_path",
    "media_plan_digest",
    "confirmation_status",
}
CONFIRMATION_FIELDS = {"status", "exact_text"}
RESULT_FIELDS = {
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
MANIFEST_FIELDS = RESULT_FIELDS | {
    "interaction_mode",
    "state_history",
    "source",
    "capabilities",
    "confirmation",
}
STYLE_SELECTION_FIELDS = {
    "protocol_version",
    "selection_method",
    "recommended_style_id",
    "recent_style_ids",
    "rejected_style_ids",
    "candidates",
}
STYLE_CANDIDATE_FIELDS = {
    "rank",
    "style_id",
    "style_name",
    "style_category",
    "visual_family",
    "fit_score",
    "repeat_penalty",
    "effective_score",
    "fit_evidence",
    "visual_traits",
    "preview_asset",
    "preview_available",
    "recommended",
}
MEDIA_PLAN_FIELDS = {
    "protocol_version",
    "request_id",
    "run_id",
    "style_lock",
    "style_authority",
    "source_precedence",
    "text_policy",
    "media_treatment_authority",
    "media_treatment_references",
    "fallback_image_form_policy",
    "slots",
}
MEDIA_SLOT_FIELDS = {
    "slot_id",
    "slide",
    "visual_need",
    "reader_block",
    "visual_job",
    "anchor_type",
    "hero_thesis",
    "must_show",
    "asset_priority",
    "image_form",
    "aspect_ratio",
    "character_mode",
    "character_id",
    "ppt_style_lock",
    "style_transform",
    "text_policy",
    "motion_intent",
    "confirmation_required",
}
MEDIA_ANCHOR_TYPES = {
    "emotion",
    "explanatory",
    "comic",
    "overview",
    "source_image",
    "product_screenshot",
    "none",
}
MEDIA_IMAGE_FORMS = {
    "physical_metaphor",
    "process",
    "comparison",
    "relationship",
    "timeline",
    "comic",
    "overview",
    "evidence",
    "none",
}
MEDIA_ASSET_TYPES = {
    "authorized_source",
    "product_screenshot",
    "native_ppt",
    "generated_visual",
}


def _error(code: str, field: str, message: str) -> dict[str, str]:
    return {"code": code, "field": field, "message": message}


def _reject_unknown(
    payload: dict[str, Any],
    allowed: set[str],
    prefix: str,
    errors: list[dict[str, str]],
) -> None:
    for field in sorted(set(payload) - allowed):
        path = f"{prefix}.{field}" if prefix else field
        errors.append(_error("FIELD_UNKNOWN", path, "field is not part of protocol 1.1"))


def _static_motion() -> dict[str, Any]:
    return {
        "requested": False,
        "profile_id": "none",
        "playback_targets": [],
        "verification_required": "structural",
        "advance": "manual",
        "reduced_motion_fallback": True,
    }


def _eligible_style_packs() -> dict[str, str]:
    path = ROOT / "references" / "style-library" / "style-pack-index.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        item["pack_id"]: item["visual_family"]
        for item in payload.get("packs", [])
        if isinstance(item, dict)
        and item.get("status") == "ok"
        and isinstance(item.get("pack_id"), str)
        and isinstance(item.get("visual_family"), str)
        and item.get("visual_family")
    }


def normalize_invocation(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(payload)
    if normalized.get("protocol_version") == "1.0":
        normalized["protocol_version"] = PROTOCOL_VERSION
    operation = normalized.get("operation")
    if isinstance(operation, str) and operation.startswith("deck."):
        constraints = normalized.setdefault("constraints", {})
        constraints.setdefault("motion", _static_motion())
        constraints.setdefault("video", {"requested": False})
    return normalized


def _require_material(
    constraints: dict[str, Any], fields: list[str], unresolved: set[str]
) -> None:
    for field in fields:
        value = constraints.get(field)
        if value is None or value == "":
            unresolved.add(field)


def _validate_route(
    route_id: Any,
    deliverable: Any,
    errors: list[dict[str, str]],
) -> None:
    if route_id is not None and (
        not isinstance(route_id, str) or route_id not in ROUTE_DELIVERABLES
    ):
        errors.append(
            _error("ROUTE_UNSUPPORTED", "constraints.route_id", f"unknown route {route_id}")
        )
        return
    if (
        isinstance(route_id, str)
        and route_id in ROUTE_DELIVERABLES
        and deliverable not in ROUTE_DELIVERABLES[route_id]
    ):
        errors.append(
            _error(
                "ROUTE_DELIVERABLE_CONFLICT",
                "constraints.deliverable",
                f"route {route_id} does not deliver {deliverable}",
            )
        )


def _validate_motion(
    route_id: str | None,
    motion: Any,
    errors: list[dict[str, str]],
    unresolved: set[str],
) -> None:
    if not isinstance(motion, dict):
        unresolved.add("motion")
        return
    _reject_unknown(motion, MOTION_FIELDS, "constraints.motion", errors)
    requested = motion.get("requested")
    profile = motion.get("profile_id")
    targets = motion.get("playback_targets")
    if requested is False:
        if profile not in (None, "none") or targets not in (None, [], ()):
            errors.append(
                _error(
                    "MOTION_PROFILE_CONFLICT",
                    "constraints.motion",
                    "requested false requires profile none and no playback targets",
                )
            )
        return
    if requested is not True:
        unresolved.add("motion.requested")
        return
    for field in [
        "profile_id",
        "playback_targets",
        "verification_required",
        "advance",
        "reduced_motion_fallback",
    ]:
        if field not in motion:
            unresolved.add(f"motion.{field}")
    if profile == "none":
        errors.append(
            _error(
                "MOTION_PROFILE_CONFLICT",
                "constraints.motion.profile_id",
                "requested motion cannot use profile none",
            )
        )
    if isinstance(route_id, str) and route_id in ROUTE_MOTION_PROFILES and profile not in ROUTE_MOTION_PROFILES[route_id]:
        errors.append(
            _error(
                "MOTION_PROFILE_UNSUPPORTED",
                "constraints.motion.profile_id",
                f"route {route_id} does not support profile {profile}",
            )
        )
    target_set = {target for target in targets if isinstance(target, str)} if isinstance(targets, list) else set()
    if profile == "web_motion_v1" and target_set != {"browser"}:
        errors.append(
            _error(
                "MOTION_TARGET_CONFLICT",
                "constraints.motion.playback_targets",
                "web_motion_v1 requires only browser",
            )
        )
    if profile == "pptx_basic_v1":
        powerpoint = {"powerpoint_365_windows", "powerpoint_365_macos"}
        if len(target_set) != 1 or not target_set <= powerpoint:
            errors.append(
                _error(
                    "MOTION_TARGET_CONFLICT",
                    "constraints.motion.playback_targets",
                    "pptx_basic_v1 requires exactly one PowerPoint target",
                )
            )
    if profile == "dual_motion_v1":
        powerpoint = {"powerpoint_365_windows", "powerpoint_365_macos"}
        if "browser" not in target_set or not target_set.intersection(powerpoint):
            errors.append(
                _error(
                    "MOTION_TARGET_CONFLICT",
                    "constraints.motion.playback_targets",
                    "dual_motion_v1 requires browser and at least one PowerPoint target",
                )
            )


def _validate_video(
    route_id: str | None,
    video: Any,
    errors: list[dict[str, str]],
    unresolved: set[str],
) -> None:
    if not isinstance(video, dict):
        unresolved.add("video")
        return
    _reject_unknown(video, VIDEO_FIELDS, "constraints.video", errors)
    if video.get("requested") is False:
        return
    if video.get("requested") is not True:
        unresolved.add("video.requested")
        return
    required = ["delivery", "playback", "audio", "loop", "poster_frame", "fallback", "assets"]
    for field in required:
        if field not in video:
            unresolved.add(f"video.{field}")
    delivery = video.get("delivery")
    if (
        isinstance(route_id, str)
        and route_id in ROUTE_VIDEO_DELIVERIES
        and (not isinstance(delivery, str) or delivery not in ROUTE_VIDEO_DELIVERIES[route_id])
    ):
        errors.append(
            _error(
                "VIDEO_DELIVERY_UNSUPPORTED",
                "constraints.video.delivery",
                f"route {route_id} does not support video delivery {delivery}",
            )
        )
    assets = video.get("assets")
    if not isinstance(assets, list) or not assets:
        unresolved.add("video.assets")
        return
    for index, asset in enumerate(assets):
        if not isinstance(asset, dict):
            errors.append(_error("VIDEO_ASSET_INVALID", f"video.assets.{index}", "asset must be an object"))
            continue
        _reject_unknown(
            asset,
            VIDEO_ASSET_FIELDS,
            f"constraints.video.assets.{index}",
            errors,
        )
        for field in ["asset_id", "source", "page_id"]:
            if asset.get(field) in (None, ""):
                unresolved.add(f"video.assets.{index}.{field}")
        start = asset.get("trim_start_seconds", 0)
        end = asset.get("trim_end_seconds")
        if end is not None and (
            not isinstance(start, (int, float))
            or not isinstance(end, (int, float))
            or end <= start
        ):
            errors.append(
                _error(
                    "VIDEO_TRIM_INVALID",
                    f"video.assets.{index}",
                    "trim_end_seconds must be greater than trim_start_seconds",
                )
            )


def validate_invocation(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "status": "needs_input",
            "normalized": {},
            "errors": [_error("PAYLOAD_TYPE_INVALID", "input", "payload must be an object")],
            "unresolved_fields": [],
        }
    normalized = normalize_invocation(payload)
    errors: list[dict[str, str]] = []
    unresolved: set[str] = set()
    _reject_unknown(normalized, INVOCATION_FIELDS, "", errors)
    for field in ["protocol_version", "request_id", "operation", "interaction_mode"]:
        if normalized.get(field) in (None, ""):
            unresolved.add(field)
    if normalized.get("protocol_version") != PROTOCOL_VERSION:
        errors.append(_error("PROTOCOL_UNSUPPORTED", "protocol_version", "supported versions are 1.0 and 1.1"))
    operation = normalized.get("operation")
    if not isinstance(operation, str) or operation not in OPERATIONS:
        errors.append(_error("OPERATION_UNSUPPORTED", "operation", f"unknown operation {operation}"))
    interaction_mode = normalized.get("interaction_mode")
    if interaction_mode not in ("human", "agent"):
        errors.append(
            _error(
                "INTERACTION_MODE_INVALID",
                "interaction_mode",
                f"unknown interaction mode {interaction_mode}",
            )
        )

    sources = normalized.get("source", [])
    if not isinstance(sources, list):
        errors.append(_error("PAYLOAD_TYPE_INVALID", "source", "source must be an array"))
        sources = []
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(
                _error("SOURCE_INVALID", f"source.{index}", "source must be an object")
            )
            continue
        _reject_unknown(source, SOURCE_FIELDS, f"source.{index}", errors)
        if source.get("type") not in ("file", "url", "text", "run", "style"):
            errors.append(
                _error(
                    "SOURCE_INVALID",
                    f"source.{index}.type",
                    f"unknown source type {source.get('type')}",
                )
            )
        if not isinstance(source.get("location"), str) or not source.get("location"):
            unresolved.add(f"source.{index}.location")
    constraints = normalized.get("constraints", {})
    if not isinstance(constraints, dict):
        constraints = {}
        unresolved.add("constraints")
    else:
        _reject_unknown(constraints, CONSTRAINT_FIELDS, "constraints", errors)
    confirmation = normalized.get("confirmation", {})
    if isinstance(confirmation, dict):
        _reject_unknown(confirmation, CONFIRMATION_FIELDS, "confirmation", errors)
        confirmation_status = confirmation.get("status")
    else:
        confirmation_status = None
        errors.append(
            _error("PAYLOAD_TYPE_INVALID", "confirmation", "confirmation must be an object")
        )
    confirmed = confirmation_status in ("confirmed", "defaults_authorized")

    if operation == "deck.create" and not sources:
        unresolved.add("source")
    if operation == "deck.revise":
        if not normalized.get("run_id") and not sources:
            unresolved.add("run_id_or_source")
        if constraints.get("revision_scope") in (None, ""):
            unresolved.add("revision_scope")
    if operation == "deck.review" and not sources:
        unresolved.add("source")
    if isinstance(operation, str) and operation in {"style.add", "style.update", "style.remove"}:
        if not sources:
            unresolved.add("source")
        if constraints.get("mutation_approved") is not True:
            unresolved.add("mutation_approved")

    route_id = constraints.get("route_id")
    deliverable = constraints.get("deliverable")
    _validate_route(route_id, deliverable, errors)

    if isinstance(operation, str) and operation in {"deck.create", "deck.revise"}:
        _validate_motion(route_id, constraints.get("motion"), errors, unresolved)
        _validate_video(route_id, constraints.get("video"), errors, unresolved)
    if confirmed and operation == "deck.create":
        _require_material(
            constraints,
            ["page_count", "deliverable", "route_id", "rewrite_boundary", "speaker_notes"],
            unresolved,
        )
        if route_id == "dashiai":
            if constraints.get("theme_id") in (None, ""):
                unresolved.add("theme_id")
        elif constraints.get("style_id") in (None, ""):
            unresolved.add("style_id")
        if not isinstance(confirmation, dict) or confirmation.get("exact_text") in (None, ""):
            unresolved.add("confirmation.exact_text")

    status = "normalized" if not errors and not unresolved else "needs_input"
    return {
        "ok": not errors and not unresolved,
        "status": status,
        "normalized": normalized,
        "errors": errors,
        "unresolved_fields": sorted(unresolved),
    }


def _validate_proposed_style_selection(
    proposed: Any,
    required: bool,
    errors: list[dict[str, str]],
    unresolved: set[str],
    prefix: str,
) -> None:
    if not isinstance(proposed, dict):
        if required:
            unresolved.add(f"{prefix}.style_candidates")
        return
    selection = proposed.get("style_candidates")
    if selection is None:
        if required:
            unresolved.add(f"{prefix}.style_candidates")
        return
    report = validate_style_selection(selection)
    for item in report["errors"]:
        errors.append(
            _error(item["code"], f"{prefix}.style_candidates.{item['field']}", item["message"])
        )
    for field in report["unresolved_fields"]:
        unresolved.add(f"{prefix}.style_candidates.{field}")
    if isinstance(selection, dict) and proposed.get("recommended_style_id") != selection.get(
        "recommended_style_id"
    ):
        errors.append(
            _error(
                "STYLE_RECOMMENDATION_INVALID",
                f"{prefix}.recommended_style_id",
                "outer recommended_style_id must match the validated style selection",
            )
        )


def validate_result(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "errors": [_error("PAYLOAD_TYPE_INVALID", "input", "payload must be an object")],
        }
    errors: list[dict[str, str]] = []
    _reject_unknown(payload, RESULT_FIELDS, "", errors)
    required = [
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
    ]
    for field in required:
        if field not in payload:
            errors.append(_error("RESULT_FIELD_MISSING", field, "required result field is missing"))
    if payload.get("protocol_version") != PROTOCOL_VERSION:
        errors.append(
            _error("PROTOCOL_UNSUPPORTED", "protocol_version", "result requires protocol 1.1")
        )
    result_operation = payload.get("operation")
    if not isinstance(result_operation, str) or result_operation not in OPERATIONS:
        errors.append(
            _error(
                "OPERATION_UNSUPPORTED",
                "operation",
                f"unknown operation {result_operation}",
            )
        )
    if not isinstance(payload.get("request_id"), str) or not payload.get("request_id"):
        errors.append(
            _error("RESULT_FIELD_INVALID", "request_id", "request_id must be a non-empty string")
        )
    status = payload.get("status")
    if not isinstance(status, str) or status not in RESULT_STATUSES:
        errors.append(_error("RESULT_STATE_INVALID", "status", f"unknown status {status}"))
    unresolved = payload.get("unresolved_fields", [])
    unresolved_set: set[str] = set()
    _validate_proposed_style_selection(
        payload.get("proposed_decisions"),
        isinstance(unresolved, list) and "style_id" in unresolved,
        errors,
        unresolved_set,
        "proposed_decisions",
    )
    for field in sorted(unresolved_set):
        errors.append(
            _error("RESULT_FIELD_MISSING", field, "required proposed style selection is missing")
        )
    if status == "needs_input" and (not unresolved or not payload.get("next_action")):
        errors.append(
            _error(
                "RESULT_STATE_INVALID",
                "status",
                "needs_input requires unresolved_fields and next_action",
            )
        )
    if isinstance(status, str) and status in {"blocked", "failed"} and not payload.get("error"):
        errors.append(
            _error("RESULT_STATE_INVALID", "error", f"{status} requires an error object")
        )
    if status == "completed":
        if (
            isinstance(result_operation, str)
            and result_operation in {"deck.create", "deck.revise"}
            and (not isinstance(payload.get("run_id"), str) or not payload.get("run_id"))
        ):
            errors.append(
                _error(
                    "RESULT_FIELD_INVALID",
                    "run_id",
                    "completed deck work requires a non-empty run_id",
                )
            )
        if unresolved:
            errors.append(_error("RESULT_STATE_INVALID", "unresolved_fields", "completed cannot have unresolved fields"))
        if payload.get("error") is not None:
            errors.append(_error("RESULT_STATE_INVALID", "error", "completed cannot contain an error"))
        if isinstance(payload.get("operation"), str) and payload.get("operation") in {"deck.create", "deck.revise"} and not payload.get("artifacts"):
            errors.append(_error("RESULT_STATE_INVALID", "artifacts", "completed deck work requires artifacts"))
        for index, artifact in enumerate(payload.get("artifacts", [])):
            if not isinstance(artifact, dict) or artifact.get("verified") is not True:
                errors.append(
                    _error(
                        "ARTIFACT_UNVERIFIED",
                        f"artifacts.{index}",
                        "completed artifacts must be verified",
                    )
                )
                continue
            path = artifact.get("path")
            if not isinstance(path, str) or not path or not Path(path).exists():
                errors.append(
                    _error(
                        "ARTIFACT_MISSING",
                        f"artifacts.{index}.path",
                        "verified artifact path does not exist",
                    )
                )

        decisions = payload.get("resolved_decisions", {})
        motion = decisions.get("motion", {}) if isinstance(decisions, dict) else {}
        verification = payload.get("verification", [])
        if motion.get("requested") is True:
            required_level = motion.get("verification_required", "structural")
            rank = {"declared": 0, "structural": 1, "playback": 2}
            for target in motion.get("playback_targets", []):
                matching = [
                    item
                    for item in verification
                    if isinstance(item, dict)
                    and item.get("capability") == "motion"
                    and item.get("target") == target
                    and item.get("verified") is True
                    and rank.get(item.get("level"), -1) >= rank.get(required_level, 1)
                ]
                if not matching:
                    errors.append(
                        _error(
                            "VERIFICATION_MISSING",
                            "verification",
                            f"missing {required_level} motion evidence for {target}",
                        )
                    )
        video = decisions.get("video", {}) if isinstance(decisions, dict) else {}
        if video.get("requested") is True and not any(
            isinstance(item, dict)
            and item.get("capability") == "video"
            and item.get("verified") is True
            and item.get("level") in {"structural", "playback"}
            for item in verification
        ):
            errors.append(_error("VERIFICATION_MISSING", "verification", "video evidence is missing"))
    return {"ok": not errors, "errors": errors}


def validate_handoff(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "errors": [_error("PAYLOAD_TYPE_INVALID", "input", "payload must be an object")],
            "unresolved_fields": [],
        }
    errors: list[dict[str, str]] = []
    unresolved: set[str] = set()
    _reject_unknown(payload, HANDOFF_FIELDS, "", errors)
    required = [
        "protocol_version",
        "request_id",
        "run_id",
        "capability_id",
        "role",
        "status",
        "producer",
        "input",
        "output",
        "version",
        "error",
    ]
    for field in required:
        if field not in payload or payload.get(field) == "":
            unresolved.add(field)
    if payload.get("protocol_version") != PROTOCOL_VERSION:
        errors.append(
            _error("PROTOCOL_UNSUPPORTED", "protocol_version", "handoff requires protocol 1.1")
        )
    for field in ["request_id", "run_id", "capability_id", "producer"]:
        if not isinstance(payload.get(field), str) or not payload.get(field):
            unresolved.add(field)
    for field in ["input", "output"]:
        if not isinstance(payload.get(field), dict):
            errors.append(
                _error("PAYLOAD_TYPE_INVALID", field, f"{field} must be an object")
            )
    role = payload.get("role")
    status = payload.get("status")
    if not isinstance(role, str) or role not in HANDOFF_ROLES:
        errors.append(_error("HANDOFF_ROLE_INVALID", "role", f"unknown role {role}"))
    if not isinstance(status, str) or status not in HANDOFF_STATUSES:
        errors.append(_error("HANDOFF_STATUS_INVALID", "status", f"unknown status {status}"))
    if isinstance(role, str) and role in HANDOFF_ROLE_REQUIREMENTS:
        required_input, required_output = HANDOFF_ROLE_REQUIREMENTS[role]
        handoff_input = payload.get("input")
        if isinstance(handoff_input, dict):
            for field in sorted(required_input):
                if handoff_input.get(field) in (None, "", []):
                    unresolved.add(f"input.{field}")
        if status == "completed":
            handoff_output = payload.get("output")
            if isinstance(handoff_output, dict):
                for field in sorted(required_output):
                    if handoff_output.get(field) in (None, "", []):
                        unresolved.add(f"output.{field}")
    if isinstance(role, str) and role in {"media_generator", "renderer", "visual_qa"}:
        context = payload.get("director_context")
        if not isinstance(context, dict):
            unresolved.add("director_context")
        else:
            _reject_unknown(
                context, DIRECTOR_CONTEXT_FIELDS, "director_context", errors
            )
            for field in ["route_id", "page_count", "style_lock", "story_digest"]:
                if context.get(field) in (None, ""):
                    unresolved.add(f"director_context.{field}")
            if role == "media_generator" and context.get("media_plan_path") in (
                None,
                "",
            ):
                unresolved.add("director_context.media_plan_path")
    if role == "media_generator":
        context = payload.get("director_context")
        handoff_input = payload.get("input")
        plan_payload: dict[str, Any] | None = None
        if isinstance(context, dict):
            for field in ["media_plan_digest", "confirmation_status"]:
                if context.get(field) in (None, ""):
                    unresolved.add(f"director_context.{field}")
            confirmation_status = context.get("confirmation_status")
            if confirmation_status not in (None, "") and (
                not isinstance(confirmation_status, str)
                or confirmation_status
                not in {"pending", "confirmed", "defaults_authorized"}
            ):
                errors.append(
                    _error(
                        "PAYLOAD_TYPE_INVALID",
                        "director_context.confirmation_status",
                        "confirmation_status must be a supported string",
                    )
                )
            path_value = context.get("media_plan_path")
            digest_value = context.get("media_plan_digest")
            if digest_value not in (None, "") and (
                not isinstance(digest_value, str)
                or not digest_value.startswith("sha256:")
                or len(digest_value) != 71
                or any(character not in "0123456789abcdef" for character in digest_value[7:])
            ):
                errors.append(
                    _error(
                        "PAYLOAD_TYPE_INVALID",
                        "director_context.media_plan_digest",
                        "media_plan_digest must be sha256 followed by 64 lowercase hex characters",
                    )
                )
            if path_value not in (None, "") and not isinstance(path_value, str):
                errors.append(
                    _error(
                        "PAYLOAD_TYPE_INVALID",
                        "director_context.media_plan_path",
                        "media_plan_path must be a string",
                    )
                )
            elif isinstance(path_value, str) and path_value:
                plan_path = Path(path_value)
                if not plan_path.is_absolute():
                    plan_path = ROOT / plan_path
                try:
                    plan_bytes = plan_path.read_bytes()
                    loaded_plan = json.loads(plan_bytes.decode("utf-8"))
                except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                    errors.append(
                        _error(
                            "MEDIA_PLAN_UNREADABLE",
                            "director_context.media_plan_path",
                            str(exc),
                        )
                    )
                else:
                    plan_report = validate_media_plan(loaded_plan)
                    if not plan_report["ok"]:
                        errors.append(
                            _error(
                                "MEDIA_PLAN_INVALID",
                                "director_context.media_plan_path",
                                "referenced media plan failed runtime validation",
                            )
                        )
                    else:
                        plan_payload = loaded_plan
                        expected_context = {
                            "request_id": payload.get("request_id"),
                            "run_id": payload.get("run_id"),
                            "style_lock": context.get("style_lock"),
                        }
                        mismatched = [
                            field
                            for field, expected in expected_context.items()
                            if plan_payload.get(field) != expected
                        ]
                        if mismatched:
                            errors.append(
                                _error(
                                    "MEDIA_PLAN_CONTEXT_MISMATCH",
                                    "director_context.media_plan_path",
                                    "media plan differs from handoff "
                                    + ", ".join(mismatched),
                                )
                            )
                    actual_digest = "sha256:" + hashlib.sha256(plan_bytes).hexdigest()
                    supplied_digest = context.get("media_plan_digest")
                    if isinstance(supplied_digest, str) and supplied_digest != actual_digest:
                        errors.append(
                            _error(
                                "MEDIA_PLAN_DIGEST_MISMATCH",
                                "director_context.media_plan_digest",
                                "media plan digest does not match referenced file",
                            )
                        )

        requested_slot_ids: list[str] = []
        generation_scope = None
        if isinstance(handoff_input, dict):
            generation_scope = handoff_input.get("generation_scope")
            if not isinstance(generation_scope, str) or generation_scope not in {
                "baseline_preview",
                "production_assets",
            }:
                errors.append(
                    _error(
                        "MEDIA_GENERATION_SCOPE_INVALID",
                        "input.generation_scope",
                        "generation_scope must be baseline_preview or production_assets",
                    )
                )
            media_slots = handoff_input.get("media_slots")
            if isinstance(media_slots, list):
                for index, slot in enumerate(media_slots):
                    if not isinstance(slot, dict) or not isinstance(slot.get("slot_id"), str):
                        errors.append(
                            _error(
                                "MEDIA_SLOT_BINDING_INVALID",
                                f"input.media_slots.{index}",
                                "every requested slot must identify a media-plan slot",
                            )
                        )
                        continue
                    slot_id = slot["slot_id"]
                    requested_slot_ids.append(slot_id)
                    if plan_payload is not None:
                        plan_slots = {
                            item.get("slot_id"): item
                            for item in plan_payload.get("slots", [])
                            if isinstance(item, dict)
                        }
                        plan_slot = plan_slots.get(slot_id)
                        if plan_slot is None or any(
                            key not in plan_slot or plan_slot[key] != value
                            for key, value in slot.items()
                        ):
                            errors.append(
                                _error(
                                    "MEDIA_SLOT_BINDING_INVALID",
                                    f"input.media_slots.{index}",
                                    "requested slot differs from the validated media plan",
                                )
                            )
                if len(requested_slot_ids) != len(set(requested_slot_ids)):
                    errors.append(
                        _error(
                            "MEDIA_SLOT_BINDING_INVALID",
                            "input.media_slots",
                            "requested media slot IDs must be unique",
                        )
                    )
                if generation_scope == "baseline_preview" and len(media_slots) != 1:
                    errors.append(
                        _error(
                            "MEDIA_GENERATION_SCOPE_INVALID",
                            "input.media_slots",
                            "baseline_preview must request exactly one media slot",
                        )
                    )
            if (
                generation_scope == "production_assets"
                and isinstance(context, dict)
                and context.get("confirmation_status")
                not in {"confirmed", "defaults_authorized"}
            ):
                errors.append(
                    _error(
                        "MEDIA_GENERATION_NOT_CONFIRMED",
                        "director_context.confirmation_status",
                        "production assets require confirmed decisions",
                    )
                )

        if status == "completed":
            handoff_output = payload.get("output")
            assets = handoff_output.get("assets") if isinstance(handoff_output, dict) else None
            if isinstance(assets, list):
                returned_slot_ids: list[str] = []
                required_asset_fields = {
                    "asset_id",
                    "slot_id",
                    "path_or_url",
                    "source_type",
                    "ppt_style_lock",
                    "style_transform",
                    "text_policy",
                    "provenance",
                    "verified",
                }
                for index, asset in enumerate(assets):
                    valid = isinstance(asset, dict) and all(
                        asset.get(field) not in (None, "")
                        for field in required_asset_fields
                    )
                    if valid:
                        returned_slot_ids.append(asset["slot_id"])
                        valid = (
                            isinstance(asset.get("source_type"), str)
                            and asset.get("source_type") in MEDIA_ASSET_TYPES
                            and isinstance(context, dict)
                            and asset.get("ppt_style_lock") == context.get("style_lock")
                            and asset.get("style_transform") == "inherit_ppt_style"
                            and asset.get("text_policy") == "editable_ppt_text"
                            and asset.get("verified") is True
                        )
                    if not valid:
                        errors.append(
                            _error(
                                "MEDIA_ASSET_PROOF_INVALID",
                                f"output.assets.{index}",
                                "asset must prove slot, source, PPT style inheritance, editability, provenance, and verification",
                            )
                        )
                if set(returned_slot_ids) != set(requested_slot_ids) or len(
                    returned_slot_ids
                ) != len(set(returned_slot_ids)):
                    errors.append(
                        _error(
                            "MEDIA_ASSET_SLOT_MISMATCH",
                            "output.assets",
                            "completed assets must map one-to-one to requested media slots",
                        )
                    )
    if status == "completed" and not payload.get("output"):
        unresolved.add("output")
    if isinstance(status, str) and status in {"blocked", "failed"} and not payload.get("error"):
        unresolved.add("error")
    return {
        "ok": not errors and not unresolved,
        "errors": errors,
        "unresolved_fields": sorted(unresolved),
    }


def validate_manifest(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "errors": [_error("PAYLOAD_TYPE_INVALID", "input", "payload must be an object")],
            "unresolved_fields": [],
        }
    errors: list[dict[str, str]] = []
    _reject_unknown(payload, MANIFEST_FIELDS, "", errors)
    unresolved: set[str] = set()
    required = [
        "protocol_version",
        "request_id",
        "run_id",
        "operation",
        "interaction_mode",
        "status",
        "state_history",
        "source",
        "resolved_decisions",
        "unresolved_fields",
        "proposed_decisions",
        "capabilities",
        "artifacts",
        "warnings",
        "verification",
        "error",
        "next_action",
        "confirmation",
    ]
    for field in required:
        if field not in payload:
            unresolved.add(field)
    manifest_unresolved = payload.get("unresolved_fields")
    _validate_proposed_style_selection(
        payload.get("proposed_decisions"),
        isinstance(manifest_unresolved, list) and "style_id" in manifest_unresolved,
        errors,
        unresolved,
        "proposed_decisions",
    )
    for field in ["request_id", "run_id"]:
        if not isinstance(payload.get(field), str) or not payload.get(field):
            unresolved.add(field)
    if payload.get("protocol_version") != PROTOCOL_VERSION:
        errors.append(
            _error("PROTOCOL_UNSUPPORTED", "protocol_version", "manifest requires protocol 1.1")
        )
    if payload.get("operation") not in ("deck.create", "deck.revise"):
        errors.append(
            _error(
                "OPERATION_UNSUPPORTED",
                "operation",
                "run manifests are only for deck.create or deck.revise",
            )
        )
    if payload.get("interaction_mode") not in ("human", "agent"):
        errors.append(
            _error(
                "INTERACTION_MODE_INVALID",
                "interaction_mode",
                f"unknown interaction mode {payload.get('interaction_mode')}",
            )
        )
    history = payload.get("state_history")
    status = payload.get("status")
    if not isinstance(history, list) or not history:
        unresolved.add("state_history")
    else:
        if history[0] != "received":
            errors.append(_error("STATE_TRANSITION_INVALID", "state_history", "history must start at received"))
        for previous, current in zip(history, history[1:]):
            if (
                not isinstance(previous, str)
                or not isinstance(current, str)
                or current not in ALLOWED_TRANSITIONS.get(previous, set())
            ):
                errors.append(
                    _error(
                        "STATE_TRANSITION_INVALID",
                        "state_history",
                        f"transition {previous} -> {current} is not allowed",
                    )
                )
        if history[-1] != status:
            errors.append(_error("STATE_TRANSITION_INVALID", "status", "status must equal the last history entry"))

    capabilities = payload.get("capabilities", [])
    if not isinstance(capabilities, list):
        errors.append(_error("PAYLOAD_TYPE_INVALID", "capabilities", "capabilities must be an array"))
    else:
        for index, handoff in enumerate(capabilities):
            if not isinstance(handoff, dict):
                errors.append(_error("HANDOFF_INVALID", f"capabilities.{index}", "handoff must be an object"))
                continue
            report = validate_handoff(handoff)
            for item in report["errors"]:
                errors.append(_error(item["code"], f"capabilities.{index}.{item['field']}", item["message"]))
            for field in report["unresolved_fields"]:
                unresolved.add(f"capabilities.{index}.{field}")
            if handoff.get("request_id") != payload.get("request_id") or handoff.get(
                "run_id"
            ) != payload.get("run_id"):
                errors.append(
                    _error(
                        "HANDOFF_CONTEXT_MISMATCH",
                        f"capabilities.{index}",
                        "capability request_id and run_id must match the manifest",
                    )
                )
            if (
                handoff.get("role") == "media_generator"
                and isinstance(handoff.get("input"), dict)
                and handoff["input"].get("generation_scope") == "production_assets"
            ):
                manifest_confirmation = payload.get("confirmation")
                confirmation_status = (
                    manifest_confirmation.get("status")
                    if isinstance(manifest_confirmation, dict)
                    else None
                )
                if status not in {"confirmed", "planned", "rendering", "qa", "completed"} or confirmation_status not in {
                    "confirmed",
                    "defaults_authorized",
                }:
                    errors.append(
                        _error(
                            "MANIFEST_CAPABILITY_CONFIRMATION_MISMATCH",
                            f"capabilities.{index}.input.generation_scope",
                            "production media requires a confirmed manifest state and confirmation",
                        )
                    )

    advanced_states = {"confirmed", "planned", "rendering", "qa", "completed"}
    if isinstance(status, str) and status in advanced_states:
        decisions = payload.get("resolved_decisions")
        if not isinstance(decisions, dict):
            unresolved.add("resolved_decisions")
        else:
            _validate_route(
                decisions.get("route_id"), decisions.get("deliverable"), errors
            )
            _require_material(
                decisions,
                ["page_count", "deliverable", "route_id", "rewrite_boundary", "speaker_notes"],
                unresolved,
            )
            if decisions.get("route_id") == "dashiai":
                if decisions.get("theme_id") in (None, ""):
                    unresolved.add("theme_id")
            elif decisions.get("style_id") in (None, ""):
                unresolved.add("style_id")
            _validate_motion(decisions.get("route_id"), decisions.get("motion"), errors, unresolved)
            _validate_video(decisions.get("route_id"), decisions.get("video"), errors, unresolved)
        if not payload.get("source"):
            unresolved.add("source")
        if payload.get("unresolved_fields"):
            errors.append(_error("MANIFEST_STATE_INVALID", "unresolved_fields", f"{status} cannot have unresolved fields"))
        confirmation = payload.get("confirmation")
        if isinstance(confirmation, dict):
            _reject_unknown(
                confirmation, CONFIRMATION_FIELDS, "confirmation", errors
            )
        if not isinstance(confirmation, dict) or confirmation.get("status") not in (
            "confirmed",
            "defaults_authorized",
        ):
            unresolved.add("confirmation")
    if status == "completed":
        artifacts = payload.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            unresolved.add("artifacts")
        elif any(not isinstance(item, dict) or item.get("verified") is not True for item in artifacts):
            errors.append(_error("ARTIFACT_UNVERIFIED", "artifacts", "completed manifest artifacts must be verified"))
        else:
            for index, artifact in enumerate(artifacts):
                path = artifact.get("path")
                if not isinstance(path, str) or not path or not Path(path).exists():
                    errors.append(
                        _error(
                            "ARTIFACT_MISSING",
                            f"artifacts.{index}.path",
                            "verified artifact path does not exist",
                        )
                    )
    if isinstance(status, str) and status in {"blocked", "failed"} and not payload.get("error"):
        unresolved.add("error")
    return {"ok": not errors and not unresolved, "errors": errors, "unresolved_fields": sorted(unresolved)}


def validate_style_selection(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "errors": [_error("PAYLOAD_TYPE_INVALID", "input", "payload must be an object")],
            "unresolved_fields": [],
        }
    errors: list[dict[str, str]] = []
    unresolved: set[str] = set()
    _reject_unknown(payload, STYLE_SELECTION_FIELDS, "", errors)
    for field in STYLE_SELECTION_FIELDS:
        if field not in payload:
            unresolved.add(field)
    if payload.get("protocol_version") != PROTOCOL_VERSION:
        errors.append(
            _error(
                "PROTOCOL_UNSUPPORTED",
                "protocol_version",
                "style selection requires protocol 1.1",
            )
        )
    if payload.get("selection_method") != "deterministic_fit_diversity_v1":
        errors.append(
            _error(
                "STYLE_SELECTION_METHOD_INVALID",
                "selection_method",
                "style candidates must use deterministic_fit_diversity_v1 and never random selection",
            )
        )

    recent = payload.get("recent_style_ids")
    rejected = payload.get("rejected_style_ids")
    if not isinstance(recent, list) or any(not isinstance(item, str) for item in recent):
        errors.append(
            _error("PAYLOAD_TYPE_INVALID", "recent_style_ids", "recent_style_ids must be an array of strings")
        )
        recent = []
    if not isinstance(rejected, list) or any(not isinstance(item, str) for item in rejected):
        errors.append(
            _error("PAYLOAD_TYPE_INVALID", "rejected_style_ids", "rejected_style_ids must be an array of strings")
        )
        rejected = []

    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 3:
        errors.append(
            _error(
                "STYLE_CANDIDATE_COUNT_INVALID",
                "candidates",
                "style_candidates must contain exactly three eligible style candidates",
            )
        )
        candidates = candidates if isinstance(candidates, list) else []

    eligible_packs = _eligible_style_packs()
    style_ids: list[str] = []
    visual_families: list[str] = []
    ranks: list[int] = []
    recommended: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        prefix = f"candidates.{index}"
        if not isinstance(candidate, dict):
            errors.append(
                _error("STYLE_CANDIDATE_INVALID", prefix, "candidate must be an object")
            )
            continue
        _reject_unknown(candidate, STYLE_CANDIDATE_FIELDS, prefix, errors)
        for field in STYLE_CANDIDATE_FIELDS:
            if field not in candidate:
                unresolved.add(f"{prefix}.{field}")

        style_id = candidate.get("style_id")
        family = candidate.get("visual_family")
        rank = candidate.get("rank")
        if isinstance(style_id, str):
            style_ids.append(style_id)
            if style_id not in eligible_packs:
                errors.append(
                    _error(
                        "STYLE_CANDIDATE_INELIGIBLE",
                        f"{prefix}.style_id",
                        f"style pack {style_id} is not an eligible complete pack",
                    )
                )
            elif family != eligible_packs[style_id]:
                errors.append(
                    _error(
                        "STYLE_FAMILY_MISMATCH",
                        f"{prefix}.visual_family",
                        f"visual_family must be {eligible_packs[style_id]}",
                    )
                )
            if style_id in rejected:
                errors.append(
                    _error(
                        "STYLE_CANDIDATE_REJECTED",
                        f"{prefix}.style_id",
                        "a user-rejected style cannot be offered again in the same run",
                    )
                )
        else:
            unresolved.add(f"{prefix}.style_id")
        if isinstance(family, str) and family:
            visual_families.append(family)
        else:
            unresolved.add(f"{prefix}.visual_family")
        if isinstance(rank, int) and not isinstance(rank, bool):
            ranks.append(rank)
        else:
            unresolved.add(f"{prefix}.rank")

        fit_score = candidate.get("fit_score")
        penalty = candidate.get("repeat_penalty")
        effective = candidate.get("effective_score")
        if not isinstance(fit_score, int) or isinstance(fit_score, bool) or not 10 <= fit_score <= 16:
            errors.append(
                _error("STYLE_SCORE_INVALID", f"{prefix}.fit_score", "fit_score must be an integer from 10 to 16")
            )
        expected_penalty = 2 if style_id in recent else 0
        if penalty != expected_penalty:
            errors.append(
                _error(
                    "STYLE_REPEAT_PENALTY_INVALID",
                    f"{prefix}.repeat_penalty",
                    f"repeat_penalty must be {expected_penalty} for this candidate",
                )
            )
        if (
            isinstance(fit_score, int)
            and not isinstance(fit_score, bool)
            and isinstance(penalty, int)
            and not isinstance(penalty, bool)
            and effective != fit_score - penalty
        ):
            errors.append(
                _error(
                    "STYLE_EFFECTIVE_SCORE_INVALID",
                    f"{prefix}.effective_score",
                    "effective_score must equal fit_score minus repeat_penalty",
                )
            )

        traits = candidate.get("visual_traits")
        if (
            not isinstance(traits, list)
            or not 3 <= len(traits) <= 5
            or any(not isinstance(item, str) or not item for item in traits)
        ):
            errors.append(
                _error(
                    "STYLE_DESCRIPTION_INVALID",
                    f"{prefix}.visual_traits",
                    "visual_traits must contain three to five non-empty strings",
                )
            )
        for field in ["style_name", "style_category", "fit_evidence"]:
            if not isinstance(candidate.get(field), str) or not candidate.get(field):
                unresolved.add(f"{prefix}.{field}")

        preview = candidate.get("preview_asset")
        preview_path = Path(preview) if isinstance(preview, str) else None
        if preview_path is not None and not preview_path.is_absolute():
            preview_path = ROOT / preview_path
        if (
            candidate.get("preview_available") is not True
            or preview_path is None
            or not preview_path.is_file()
        ):
            errors.append(
                _error(
                    "STYLE_PREVIEW_UNAVAILABLE",
                    f"{prefix}.preview_asset",
                    "every offered style must have a readable preview asset",
                )
            )
        if candidate.get("recommended") is True:
            recommended.append(candidate)

    if len(style_ids) != len(set(style_ids)):
        errors.append(
            _error("STYLE_CANDIDATE_DUPLICATE", "candidates", "style candidate IDs must be unique")
        )
    if len(visual_families) != len(set(visual_families)):
        errors.append(
            _error(
                "STYLE_DIVERSITY_INSUFFICIENT",
                "candidates",
                "the three candidates must use three distinct visual families",
            )
        )
    if sorted(ranks) != [1, 2, 3]:
        errors.append(
            _error("STYLE_RANK_INVALID", "candidates", "candidate ranks must be exactly 1, 2, and 3")
        )
    recommended_id = payload.get("recommended_style_id")
    if (
        len(recommended) != 1
        or recommended[0].get("style_id") != recommended_id
        or recommended[0].get("rank") != 1
    ):
        errors.append(
            _error(
                "STYLE_RECOMMENDATION_INVALID",
                "recommended_style_id",
                "one recommended candidate at rank 1 must match recommended_style_id",
            )
        )
    if recommended and any(
        isinstance(item, dict)
        and isinstance(item.get("effective_score"), int)
        and item.get("effective_score") > recommended[0].get("effective_score", -1)
        for item in candidates
    ):
        errors.append(
            _error(
                "STYLE_RECOMMENDATION_INVALID",
                "recommended_style_id",
                "the recommended candidate must have the highest effective score",
            )
        )
    return {
        "ok": not errors and not unresolved,
        "errors": errors,
        "unresolved_fields": sorted(unresolved),
    }


def validate_media_plan(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "errors": [_error("PAYLOAD_TYPE_INVALID", "input", "payload must be an object")],
            "unresolved_fields": [],
        }
    errors: list[dict[str, str]] = []
    unresolved: set[str] = set()
    _reject_unknown(payload, MEDIA_PLAN_FIELDS, "", errors)
    for field in MEDIA_PLAN_FIELDS:
        if field not in payload or payload.get(field) == "":
            unresolved.add(field)

    if payload.get("protocol_version") != PROTOCOL_VERSION:
        errors.append(
            _error("PROTOCOL_UNSUPPORTED", "protocol_version", "media plan requires protocol 1.1")
        )
    style_lock = payload.get("style_lock")
    if not isinstance(style_lock, str) or not style_lock:
        unresolved.add("style_lock")
    if payload.get("style_authority") != "ppt_style_lock":
        errors.append(
            _error(
                "MEDIA_STYLE_AUTHORITY_CONFLICT",
                "style_authority",
                "PPT style lock must remain the only visual style authority",
            )
        )
    if payload.get("source_precedence") != "authorized_source_first":
        errors.append(
            _error(
                "MEDIA_SOURCE_PRECEDENCE_INVALID",
                "source_precedence",
                "authorized source assets must be considered before generated visuals",
            )
        )
    if payload.get("text_policy") != "editable_ppt_text":
        errors.append(
            _error(
                "MEDIA_TEXT_EDITABILITY_INVALID",
                "text_policy",
                "presentation text must remain editable outside raster assets",
            )
        )
    if payload.get("media_treatment_authority") != "style_pack_assets":
        errors.append(
            _error(
                "MEDIA_TREATMENT_AUTHORITY_CONFLICT",
                "media_treatment_authority",
                "template media treatment assets must control generated-image rendering",
            )
        )
    if payload.get("fallback_image_form_policy") != "visual_intent_only":
        errors.append(
            _error(
                "MEDIA_TREATMENT_AUTHORITY_CONFLICT",
                "fallback_image_form_policy",
                "external visual analysis may choose image form only",
            )
        )
    treatment_references = payload.get("media_treatment_references")
    valid_treatment_references = (
        isinstance(treatment_references, list)
        and bool(treatment_references)
        and all(isinstance(item, str) and item for item in treatment_references)
        and len(treatment_references) == len(set(treatment_references))
    )
    if valid_treatment_references:
        for index, reference in enumerate(treatment_references):
            reference_path = Path(reference)
            if not reference_path.is_absolute():
                reference_path = ROOT / reference_path
            style_bound = not (
                isinstance(style_lock, str) and style_lock.startswith("ref-")
            ) or f"style-packs/{style_lock}/" in reference.replace("\\", "/")
            if not reference_path.is_file() or not style_bound:
                errors.append(
                    _error(
                        "MEDIA_TREATMENT_REFERENCE_INVALID",
                        f"media_treatment_references.{index}",
                        "media treatment reference must be a readable asset from the confirmed style pack",
                    )
                )
    else:
        errors.append(
            _error(
                "MEDIA_TREATMENT_REFERENCE_INVALID",
                "media_treatment_references",
                "at least one readable template image treatment reference is required",
            )
        )

    slots = payload.get("slots")
    if not isinstance(slots, list):
        errors.append(_error("PAYLOAD_TYPE_INVALID", "slots", "slots must be an array"))
        slots = []
    slot_ids: list[str] = []
    for index, slot in enumerate(slots):
        prefix = f"slots.{index}"
        if not isinstance(slot, dict):
            errors.append(_error("PAYLOAD_TYPE_INVALID", prefix, "slot must be an object"))
            continue
        _reject_unknown(slot, MEDIA_SLOT_FIELDS, prefix, errors)
        for field in MEDIA_SLOT_FIELDS:
            if field not in slot:
                unresolved.add(f"{prefix}.{field}")
        slot_id = slot.get("slot_id")
        if not isinstance(slot_id, str) or not slot_id:
            unresolved.add(f"{prefix}.slot_id")
        else:
            slot_ids.append(slot_id)
        if not isinstance(slot.get("slide"), int) or isinstance(slot.get("slide"), bool) or slot.get("slide", 0) < 1:
            errors.append(_error("MEDIA_SLOT_INVALID", f"{prefix}.slide", "slide must be a positive integer"))
        if slot.get("anchor_type") not in MEDIA_ANCHOR_TYPES:
            errors.append(_error("MEDIA_SLOT_INVALID", f"{prefix}.anchor_type", "unknown anchor type"))
        if slot.get("image_form") not in MEDIA_IMAGE_FORMS:
            errors.append(_error("MEDIA_SLOT_INVALID", f"{prefix}.image_form", "unknown image form"))

        if (
            slot.get("ppt_style_lock") != style_lock
            or slot.get("style_transform") != "inherit_ppt_style"
        ):
            errors.append(
                _error(
                    "MEDIA_STYLE_AUTHORITY_CONFLICT",
                    prefix,
                    "every media slot must inherit the confirmed PPT style lock",
                )
            )
        if slot.get("text_policy") != "editable_ppt_text":
            errors.append(
                _error(
                    "MEDIA_TEXT_EDITABILITY_INVALID",
                    f"{prefix}.text_policy",
                    "titles, labels, captions, and conclusions must remain editable PPT text",
                )
            )

        priority = slot.get("asset_priority")
        if (
            not isinstance(priority, list)
            or not priority
            or any(item not in MEDIA_ASSET_TYPES for item in priority)
            or len(priority) != len(set(priority))
            or priority[0] == "generated_visual"
        ):
            errors.append(
                _error(
                    "MEDIA_SOURCE_PRECEDENCE_INVALID",
                    f"{prefix}.asset_priority",
                    "generated_visual cannot precede authorized source, screenshot, or native PPT options",
                )
            )

        visual_need = slot.get("visual_need")
        must_show = slot.get("must_show")
        if visual_need is True:
            for field in ["reader_block", "visual_job", "hero_thesis"]:
                if not isinstance(slot.get(field), str) or not slot.get(field):
                    unresolved.add(f"{prefix}.{field}")
            if not isinstance(must_show, list) or not must_show or any(
                not isinstance(item, str) or not item for item in must_show
            ):
                unresolved.add(f"{prefix}.must_show")
        elif visual_need is False:
            if slot.get("anchor_type") != "none" or slot.get("image_form") != "none" or must_show not in ([], None):
                errors.append(
                    _error(
                        "MEDIA_SLOT_INVALID",
                        prefix,
                        "a no-visual slot must use none forms and an empty must_show list",
                    )
                )
        else:
            errors.append(_error("PAYLOAD_TYPE_INVALID", f"{prefix}.visual_need", "visual_need must be boolean"))

        character_mode = slot.get("character_mode")
        if character_mode not in {"none", "optional_ip", "custom"}:
            errors.append(_error("MEDIA_SLOT_INVALID", f"{prefix}.character_mode", "unknown character mode"))
        elif character_mode == "none":
            if slot.get("character_id") not in (None, ""):
                errors.append(
                    _error("MEDIA_SLOT_INVALID", f"{prefix}.character_id", "character_id requires a character mode")
                )
        elif (
            not isinstance(slot.get("character_id"), str)
            or not slot.get("character_id")
            or slot.get("confirmation_required") is not True
        ):
            errors.append(
                _error(
                    "MEDIA_IP_CONFIRMATION_REQUIRED",
                    f"{prefix}.character_mode",
                    "an IP or custom character requires an explicit character choice and confirmation",
                )
            )

    if len(slot_ids) != len(set(slot_ids)):
        errors.append(_error("MEDIA_SLOT_DUPLICATE", "slots", "slot IDs must be unique"))
    return {
        "ok": not errors and not unresolved,
        "errors": errors,
        "unresolved_fields": sorted(unresolved),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--kind",
        choices=["invocation", "result", "handoff", "manifest", "style_selection", "media_plan"],
        required=True,
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report = {"ok": False, "errors": [_error("PAYLOAD_UNREADABLE", "input", str(exc))]}
    else:
        validator = {
            "invocation": validate_invocation,
            "result": validate_result,
            "handoff": validate_handoff,
            "manifest": validate_manifest,
            "style_selection": validate_style_selection,
            "media_plan": validate_media_plan,
        }[args.kind]
        report = validator(payload)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif report["ok"]:
        print(f"runtime {args.kind} validation: OK")
    else:
        for error in report.get("errors", []):
            print(f"ERROR {error['code']} {error['field']}: {error['message']}", file=sys.stderr)
        for field in report.get("unresolved_fields", []):
            print(f"UNRESOLVED: {field}", file=sys.stderr)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

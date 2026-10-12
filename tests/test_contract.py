from __future__ import annotations

import json
import hashlib
import importlib.util
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from zipfile import ZIP_DEFLATED, ZipFile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DOCS = [
    ROOT / "SKILL.md",
    ROOT / "CALLING_SPEC.md",
    ROOT / "OVERVIEW.md",
    ROOT / "references" / "question-layer.md",
    ROOT / "references" / "output-routes.md",
    ROOT / "references" / "dashiai-adapter.md",
    ROOT / "templates" / "user-confirmation.md",
    ROOT / "templates" / "production-route.md",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_script_module(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ContractTests(unittest.TestCase):
    def test_runtime_docs_do_not_use_ambiguous_route_aliases(self) -> None:
        text = "\n".join(read(path) for path in RUNTIME_DOCS)
        forbidden = [
            "Route A:",
            "Route B:",
            "Route C:",
            "Route D:",
            "Route E:",
            "Route E/B",
            "确认 A/B/C",
            '"方案 B"',
        ]
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, text)

    def test_calling_spec_defines_stable_operations_and_states(self) -> None:
        text = read(ROOT / "CALLING_SPEC.md")
        required = [
            "deck.create",
            "deck.revise",
            "deck.review",
            "style.list",
            "style.add",
            "style.update",
            "style.remove",
            "needs_input",
            "confirmed",
            "completed",
            "blocked",
            "failed",
            "run_id",
            "interaction_mode",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_style_recommendation_includes_preview_and_plain_language_description(self) -> None:
        files = [
            ROOT / "SKILL.md",
            ROOT / "CALLING_SPEC.md",
            ROOT / "references" / "question-layer.md",
            ROOT / "templates" / "user-confirmation.md",
        ]
        required = ["style category", "visual traits", "preview asset"]
        for path in files:
            text = read(path).lower()
            for token in required:
                with self.subTest(path=path.name, token=token):
                    self.assertIn(token, text)

    def test_style_confirmation_requires_three_named_visual_candidates(self) -> None:
        contract_files = [
            ROOT / "SKILL.md",
            ROOT / "CALLING_SPEC.md",
            ROOT / "references" / "question-layer.md",
            ROOT / "templates" / "user-confirmation.md",
        ]
        required = ["style_candidates", "recommended_style_id", "preview asset"]
        for path in contract_files:
            text = read(path).lower()
            for token in required:
                with self.subTest(path=path.name, token=token):
                    self.assertIn(token, text)

        behavior = (
            read(ROOT / "CALLING_SPEC.md")
            + read(ROOT / "references" / "question-layer.md")
            + read(ROOT / "references" / "style-library" / "style-match-rules.md")
        ).lower()
        for token in [
            "three eligible style candidates",
            "one recommended candidate",
            "two visual alternatives",
            "deterministic",
            "never random",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, behavior)

    def test_style_selection_contract_exists_and_runtime_rejects_duplicates(self) -> None:
        schema = ROOT / "contracts" / "style-selection.schema.json"
        template = ROOT / "templates" / "style-selection.json"
        self.assertTrue(schema.is_file())
        self.assertTrue(template.is_file())
        json.loads(read(schema))
        payload = json.loads(read(template))
        module = load_script_module(
            "validate_runtime_style_selection", "scripts/validate_runtime_payload.py"
        )
        report = module.validate_style_selection(payload)
        self.assertTrue(report["ok"], report["errors"])

        payload["candidates"][1]["style_id"] = payload["candidates"][0]["style_id"]
        report = module.validate_style_selection(payload)
        self.assertFalse(report["ok"])
        self.assertIn("STYLE_CANDIDATE_DUPLICATE", {e["code"] for e in report["errors"]})

    def test_style_selection_rejects_same_visual_family_and_random_method(self) -> None:
        payload = json.loads(read(ROOT / "templates" / "style-selection.json"))
        module = load_script_module(
            "validate_runtime_style_diversity", "scripts/validate_runtime_payload.py"
        )
        payload["candidates"][1]["visual_family"] = payload["candidates"][0][
            "visual_family"
        ]
        report = module.validate_style_selection(payload)
        self.assertFalse(report["ok"])
        self.assertIn("STYLE_DIVERSITY_INSUFFICIENT", {e["code"] for e in report["errors"]})

        payload = json.loads(read(ROOT / "templates" / "style-selection.json"))
        payload["selection_method"] = "random"
        report = module.validate_style_selection(payload)
        self.assertFalse(report["ok"])
        self.assertIn("STYLE_SELECTION_METHOD_INVALID", {e["code"] for e in report["errors"]})

    def test_machine_contract_files_exist_and_parse(self) -> None:
        paths = [
            ROOT / "contracts" / "route-registry.json",
            ROOT / "contracts" / "invocation.schema.json",
            ROOT / "contracts" / "result.schema.json",
            ROOT / "contracts" / "capability-handoff.schema.json",
            ROOT / "contracts" / "intent-registry.json",
            ROOT / "contracts" / "run-manifest.schema.json",
            ROOT / "contracts" / "style-selection.schema.json",
            ROOT / "contracts" / "media-plan.schema.json",
            ROOT / "templates" / "run-manifest.json",
            ROOT / "templates" / "capability-handoff.json",
            ROOT / "templates" / "media-capability-handoff.json",
            ROOT / "templates" / "style-selection.json",
            ROOT / "templates" / "media-plan.json",
            ROOT / "templates" / "motion-plan.json",
        ]
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue(path.is_file())
                json.loads(read(path))

    def test_visual_intent_adapter_preserves_ppt_style_authority(self) -> None:
        requirements = {
            ROOT / "SKILL.md": [
                "media-plan.json",
                "ppt style lock is authoritative",
                "template media treatment is authoritative",
                "never changes the deck style",
            ],
            ROOT / "CALLING_SPEC.md": [
                "media-plan.json",
                "image form",
                "inherit_ppt_style",
                "visual_intent_only",
            ],
            ROOT / "references" / "visual-intent-analysis.md": [
                "media-plan.json",
                "ppt style lock is authoritative",
                "image form",
                "inherit_ppt_style",
                "template media treatment is authoritative",
                "visual_intent_only",
            ],
            ROOT / "references" / "xiaohu-ip-studio-adapter.md": [
                "media-plan.json",
                "ppt style lock is authoritative",
                "image form",
                "inherit_ppt_style",
                "template media treatment is authoritative",
                "visual_intent_only",
                "never changes the deck style",
            ],
            ROOT / "references" / "qa-checklist.md": [
                "media-plan.json",
                "ppt style lock is authoritative",
                "inherit_ppt_style",
            ],
        }
        for path, required in requirements.items():
            text = read(path).lower()
            for token in required:
                with self.subTest(path=path.name, token=token):
                    self.assertIn(token, text)

    def test_media_agent_handoff_and_maintenance_rules_are_synchronized(self) -> None:
        requirements = {
            ROOT / "CALLING_SPEC.md": [
                "media_plan_digest",
                "generation_scope",
                "baseline_preview",
                "production_assets",
                "confirmation_status",
            ],
            ROOT / "references" / "xiaohu-ip-studio-adapter.md": [
                "media_plan_digest",
                "generation_scope",
                "baseline_preview",
                "production_assets",
                "one-to-one",
            ],
            ROOT / "MAINTENANCE_SPEC.md": [
                "visual intent integration maintenance rule",
                "media_plan_digest",
                "generation_scope",
                "asset proof",
                "single-director",
            ],
            ROOT / "OVERVIEW.md": [
                "standalone skill",
                "parent agent",
                "capability handoff",
                "host agent executes",
            ],
        }
        for path, required in requirements.items():
            text = read(path).lower()
            for token in required:
                with self.subTest(path=path.name, token=token):
                    self.assertIn(token, text)

    def test_motion_video_contracts(self) -> None:
        invocation = json.loads(read(ROOT / "contracts" / "invocation.schema.json"))
        result = json.loads(read(ROOT / "contracts" / "result.schema.json"))
        registry = json.loads(read(ROOT / "contracts" / "route-registry.json"))
        manifest = json.loads(read(ROOT / "templates" / "run-manifest.json"))

        version_schema = invocation["properties"]["protocol_version"]
        self.assertEqual(set(version_schema["enum"]), {"1.0", "1.1"})
        self.assertEqual(result["properties"]["protocol_version"]["const"], "1.1")
        self.assertEqual(manifest["protocol_version"], "1.1")

        constraints = invocation["properties"]["constraints"]["properties"]
        motion = constraints["motion"]["properties"]
        self.assertEqual(
            set(motion["profile_id"]["enum"]),
            {"none", "web_motion_v1", "pptx_basic_v1", "dual_motion_v1"},
        )
        self.assertEqual(
            set(motion["verification_required"]["enum"]),
            {"structural", "playback"},
        )
        self.assertNotIn("playback_target", motion)
        self.assertEqual(motion["playback_targets"]["type"], "array")
        self.assertEqual(motion["playback_targets"]["minItems"], 1)
        video = constraints["video"]["properties"]
        self.assertEqual(
            set(video["delivery"]["enum"]),
            {"embedded", "linked", "web", "rendered_video"},
        )
        self.assertEqual(video["assets"]["minItems"], 1)
        self.assertIn("assets", constraints["video"]["allOf"][0]["then"]["required"])

        routes = {route["id"]: route for route in registry["routes"]}
        self.assertEqual(
            set(routes["native_pptx"]["motion_profiles"]),
            {"none", "pptx_basic_v1"},
        )
        self.assertEqual(
            set(routes["web_deck"]["motion_profiles"]),
            {"none", "web_motion_v1"},
        )
        self.assertIn("verification", result["properties"])
        self.assertEqual(
            set(
                result["properties"]["verification"]["items"]["properties"][
                    "level"
                ]["enum"]
            ),
            {"declared", "structural", "playback"},
        )

        self.assertEqual(manifest["resolved_decisions"]["motion"]["profile_id"], "none")
        self.assertFalse(manifest["resolved_decisions"]["video"]["requested"])
        self.assertIn("theme_id", invocation["properties"]["constraints"]["properties"])

    def test_result_schema_requires_complete_agent_envelope(self) -> None:
        result = json.loads(read(ROOT / "contracts" / "result.schema.json"))
        required = {
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
        self.assertEqual(set(result["required"]), required)
        self.assertFalse(result["properties"]["artifacts"]["items"]["additionalProperties"])
        self.assertEqual(
            set(result["properties"]["error"]["required"]),
            {"code", "stage", "message", "evidence"},
        )

    def test_motion_runtime_docs_are_synchronized(self) -> None:
        files = [
            ROOT / "SKILL.md",
            ROOT / "CALLING_SPEC.md",
            ROOT / "OVERVIEW.md",
            ROOT / "README.md",
            ROOT / "MAINTENANCE_SPEC.md",
            ROOT / "references" / "output-routes.md",
            ROOT / "references" / "motion-video-delivery.md",
            ROOT / "references" / "director-production-contract.md",
            ROOT / "references" / "qa-checklist.md",
            ROOT / "references" / "question-layer.md",
            ROOT / "templates" / "user-confirmation.md",
            ROOT / "templates" / "production-route.md",
            ROOT / "templates" / "outline.md",
            ROOT / "templates" / "qa-report.md",
        ]
        combined = "\n".join(read(path) for path in files)
        required = [
            "pptx_basic_v1",
            "web_motion_v1",
            "dual_motion_v1",
            "verification_required",
            "MOTION_TARGET_UNAVAILABLE",
            "scripts/check_motion_capabilities.py",
            "scripts/resolve_pptx_motion_shape_ids.py",
            "scripts/apply_pptx_basic_motion.py",
            "scripts/verify_pptx_motion.py",
            "scripts/verify_video_asset.py",
            "scripts/verify_web_motion.mjs",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, combined)
        self.assertNotIn("all PowerPoint animations", combined)

    def test_style_pack_extractor_has_no_user_specific_binary_path(self) -> None:
        text = read(ROOT / "scripts" / "extract_style_pack_refs.py")
        self.assertNotIn("/Users/guozhi", text)

    def test_style_collection_keeps_tls_verification_enabled(self) -> None:
        paths = [
            ROOT / "scripts" / "collect_style_refs.py",
            ROOT / "scripts" / "extract_zcool_style_pack.py",
        ]
        for path in paths:
            with self.subTest(path=path):
                self.assertNotIn("_create_unverified_context", read(path))

    def test_contract_validator_accepts_the_skill(self) -> None:
        validator = ROOT / "scripts" / "validate_contract.py"
        self.assertTrue(validator.is_file())
        result = subprocess.run(
            [sys.executable, str(validator)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator_enforces_motion_scripts_and_route_capabilities(self) -> None:
        text = read(ROOT / "scripts" / "validate_contract.py")
        required = [
            "scripts/check_motion_capabilities.py",
            "scripts/resolve_pptx_motion_shape_ids.py",
            "scripts/apply_pptx_basic_motion.py",
            "scripts/verify_pptx_motion.py",
            "scripts/verify_video_asset.py",
            "scripts/verify_web_motion.mjs",
            "scripts/validate_runtime_payload.py",
            "scripts/verify_slide_collisions.py",
            "scripts/verify_slide_previews.py",
            "templates/collision-rules.json",
            "templates/motion-plan.json",
            "contracts/intent-registry.json",
            "contracts/capability-handoff.schema.json",
            "contracts/run-manifest.schema.json",
            "contracts/style-selection.schema.json",
            "templates/style-selection.json",
            "deterministic_fit_diversity_v1",
            "motion_profiles",
            "video_deliveries",
            "ROUTE_MOTION_PROFILES",
            "REQUIRED_VISUAL_QA_FILES",
            "REQUIRED_DEFECT_LOOP_TOKENS",
            "in_slide_grouped_v1",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_contract_validator_accepts_strict_local_asset_snapshot(self) -> None:
        asset_root = ROOT / "assets" / "style-library" / "style-packs"
        if not any(asset_root.rglob("*.png")):
            self.skipTest("published source checkout intentionally excludes style bitmaps")
        validator = ROOT / "scripts" / "validate_contract.py"
        result = subprocess.run(
            [sys.executable, str(validator), "--require-style-assets"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class VisualQaContractTests(unittest.TestCase):
    @staticmethod
    def _write_png(path: Path, width: int, height: int) -> None:
        def chunk(kind: bytes, payload: bytes) -> bytes:
            body = kind + payload
            return (
                struct.pack(">I", len(payload))
                + body
                + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
            )

        row = b"\x00" + (b"\xff\xff\xff" * width)
        data = b"\x89PNG\r\n\x1a\n"
        data += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        data += chunk(b"IDAT", zlib.compress(row * height))
        data += chunk(b"IEND", b"")
        path.write_bytes(data)

    def test_surface_collision_verifier_rejects_overlap_and_accepts_separation(self) -> None:
        verifier = ROOT / "scripts" / "verify_slide_collisions.py"
        self.assertTrue(verifier.is_file())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            layout_dir = root / "layout"
            layout_dir.mkdir()
            rules = root / "rules.json"
            rules.write_text(
                json.dumps(
                    {
                        "slides": [
                            {
                                "slide": 1,
                                "groups": ["^left-card$", "^right-card$"],
                                "min_gap_px": 0,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            layout = {
                "schema": "openai.presentation.layout/v4",
                "unit": "px",
                "slide": {"slide": 1, "frame": {"width": 1280, "height": 720}},
                "elements": [
                    {"name": "left-card", "bbox": [72, 196, 510, 100], "scope": "slide"},
                    {"name": "right-card", "bbox": [554, 215, 184, 82], "scope": "slide"},
                ],
            }
            layout_path = layout_dir / "slide-01.layout.json"
            layout_path.write_text(json.dumps(layout), encoding="utf-8")

            failed = subprocess.run(
                [sys.executable, str(verifier), "--layout-dir", str(layout_dir), "--rules", str(rules), "--json"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(failed.returncode, 0, failed.stdout + failed.stderr)
            report = json.loads(failed.stdout)
            self.assertIn("SLIDE_COLLISION", {error["code"] for error in report["errors"]})

            layout["elements"][1]["bbox"] = [600, 215, 184, 82]
            layout_path.write_text(json.dumps(layout), encoding="utf-8")
            passed = subprocess.run(
                [sys.executable, str(verifier), "--layout-dir", str(layout_dir), "--rules", str(rules), "--json"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
            self.assertTrue(json.loads(passed.stdout)["ok"])

    def test_preview_verifier_rejects_thumbnail_and_accepts_full_size_slide(self) -> None:
        verifier = ROOT / "scripts" / "verify_slide_previews.py"
        self.assertTrue(verifier.is_file())
        with tempfile.TemporaryDirectory() as tmp:
            preview_dir = Path(tmp)
            preview = preview_dir / "slide-1.png"
            self._write_png(preview, 320, 180)
            failed = subprocess.run(
                [sys.executable, str(verifier), "--preview-dir", str(preview_dir), "--expected-slides", "1", "--min-width", "1280", "--min-height", "720", "--json"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(failed.returncode, 0, failed.stdout + failed.stderr)
            report = json.loads(failed.stdout)
            self.assertIn("PREVIEW_RESOLUTION_TOO_LOW", {error["code"] for error in report["errors"]})

            self._write_png(preview, 1280, 720)
            passed = subprocess.run(
                [sys.executable, str(verifier), "--preview-dir", str(preview_dir), "--expected-slides", "1", "--min-width", "1280", "--min-height", "720", "--json"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
            self.assertTrue(json.loads(passed.stdout)["ok"])

    def test_surface_collision_verifier_checks_repeated_surfaces_in_same_group(self) -> None:
        verifier = ROOT / "scripts" / "verify_slide_collisions.py"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            layout_dir = root / "layout"
            layout_dir.mkdir()
            (root / "rules.json").write_text(
                json.dumps(
                    {
                        "slides": [
                            {
                                "slide": 1,
                                "groups": ["^card-[0-9]+$", "^sentinel$"],
                                "min_gap_px": 0,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (layout_dir / "slide-01.layout.json").write_text(
                json.dumps(
                    {
                        "slide": {"slide": 1},
                        "elements": [
                            {"name": "card-0", "bbox": [10, 10, 100, 100], "scope": "slide"},
                            {"name": "card-1", "bbox": [90, 20, 100, 100], "scope": "slide"},
                            {"name": "sentinel", "bbox": [400, 400, 10, 10], "scope": "slide"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(verifier), "--layout-dir", str(layout_dir), "--rules", str(root / "rules.json"), "--json"],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        collisions = [error for error in report["errors"] if error["code"] == "SLIDE_COLLISION"]
        self.assertEqual(len(collisions), 1)
        self.assertEqual({collisions[0]["first"]["name"], collisions[0]["second"]["name"]}, {"card-0", "card-1"})

    def test_user_reported_defect_and_visual_qa_rules_are_explicit(self) -> None:
        maintenance = read(ROOT / "MAINTENANCE_SPEC.md").lower()
        for token in [
            "user-reported defect",
            "minimal reproducer",
            "failing regression test",
            "authority files",
            "dependent files",
            "full validation",
            "artifact-only fix is incomplete",
        ]:
            with self.subTest(scope="maintenance", token=token):
                self.assertIn(token, maintenance)

        runtime = "\n".join(
            read(path)
            for path in [
                ROOT / "CALLING_SPEC.md",
                ROOT / "references" / "qa-checklist.md",
                ROOT / "templates" / "qa-report.md",
            ]
        ).lower()
        for token in [
            "full-size slide preview",
            "montage is navigation only",
            "collision verification",
            "static pptx, no animation",
            "playback verification",
        ]:
            with self.subTest(scope="runtime", token=token):
                self.assertIn(token, runtime)


class MotionCapabilityTests(unittest.TestCase):
    def test_missing_powerpoint_blocks_playback_but_keeps_structural_verification(self) -> None:
        module = load_script_module(
            "check_motion_capabilities", "scripts/check_motion_capabilities.py"
        )

        report = module.inspect_capabilities(
            which=lambda name: "/usr/bin/" + name if name == "ffprobe" else None,
            app_exists=lambda name: name == "Keynote.app",
            platform_name="Darwin",
        )

        self.assertFalse(report["applications"]["powerpoint"]["available"])
        self.assertTrue(report["applications"]["keynote"]["available"])
        pptx = report["profiles"]["pptx_basic_v1"]
        self.assertIn("structural", pptx["verification_levels"])
        self.assertNotIn("playback", pptx["verification_levels"])
        self.assertEqual(pptx["playback_error"], "MOTION_TARGET_UNAVAILABLE")

    def test_available_powerpoint_enables_playback_verification(self) -> None:
        module = load_script_module(
            "check_motion_capabilities_available", "scripts/check_motion_capabilities.py"
        )
        report = module.inspect_capabilities(
            which=lambda name: None,
            app_exists=lambda name: name == "Microsoft PowerPoint.app",
            platform_name="Darwin",
        )
        self.assertIn(
            "playback",
            report["profiles"]["pptx_basic_v1"]["verification_levels"],
        )

    def test_chrome_and_node_enable_web_playback_verification(self) -> None:
        module = load_script_module(
            "check_web_motion_capabilities", "scripts/check_motion_capabilities.py"
        )
        report = module.inspect_capabilities(
            which=lambda name: "/usr/bin/node" if name == "node" else None,
            app_exists=lambda name: name == "Google Chrome.app",
            platform_name="Darwin",
            playwright_available=True,
        )
        self.assertTrue(report["applications"]["browser"]["available"])
        self.assertIn(
            "playback",
            report["profiles"]["web_motion_v1"]["verification_levels"],
        )

    def test_all_targets_enable_dual_playback_verification(self) -> None:
        module = load_script_module(
            "check_dual_motion_capabilities", "scripts/check_motion_capabilities.py"
        )
        report = module.inspect_capabilities(
            which=lambda name: "/usr/bin/" + name if name == "node" else None,
            app_exists=lambda name: name
            in {"Microsoft PowerPoint.app", "Google Chrome.app"},
            platform_name="Darwin",
            playwright_available=True,
        )
        self.assertIn(
            "playback",
            report["profiles"]["dual_motion_v1"]["verification_levels"],
        )

    def test_missing_playwright_blocks_web_playback_verification(self) -> None:
        module = load_script_module(
            "check_missing_playwright", "scripts/check_motion_capabilities.py"
        )
        report = module.inspect_capabilities(
            which=lambda name: "/usr/bin/node" if name == "node" else None,
            app_exists=lambda name: name == "Google Chrome.app",
            platform_name="Darwin",
            playwright_available=False,
        )
        self.assertNotIn(
            "playback",
            report["profiles"]["web_motion_v1"]["verification_levels"],
        )


class PptxMotionVerificationTests(unittest.TestCase):
    def _write_fixture(
        self, path: Path, *, target_shape_id: str = "2", include_media: bool = True
    ) -> None:
        slide = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
 xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
 <p:cSld><p:spTree><p:sp><p:nvSpPr><p:cNvPr id="2" name="Build target"/></p:nvSpPr></p:sp></p:spTree></p:cSld>
 <p:transition spd="med"><p:fade/></p:transition>
 <p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" nodeType="tmRoot"><p:childTnLst>
  <p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>
   <p:par><p:cTn id="3" nodeType="clickEffect"><p:childTnLst><p:set><p:cBhvr><p:cTn id="4" dur="1" fill="hold"/><p:tgtEl><p:spTgt spid="{target_shape_id}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set></p:childTnLst></p:cTn></p:par>
  </p:childTnLst></p:cTn></p:seq>
 </p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>
 <p:extLst><p:ext uri="video"><a:videoFile r:link="rId5"/></p:ext></p:extLst>
</p:sld>'''
        rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/video" Target="../media/video1.mp4"/>
</Relationships>'''
        content_types = '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="xml" ContentType="application/xml"/>
 <Default Extension="mp4" ContentType="video/mp4"/>
</Types>'''
        with ZipFile(path, "w", ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", content_types)
            archive.writestr("ppt/slides/slide1.xml", slide)
            archive.writestr("ppt/slides/_rels/slide1.xml.rels", rels)
            if include_media:
                archive.writestr("ppt/media/video1.mp4", b"fixture-video")

    def test_detects_transition_build_target_and_embedded_video(self) -> None:
        module = load_script_module(
            "verify_pptx_motion", "scripts/verify_pptx_motion.py"
        )
        with tempfile.TemporaryDirectory() as tmp:
            pptx = Path(tmp) / "motion.pptx"
            self._write_fixture(pptx)
            report = module.inspect_pptx(pptx)

        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["verification_level"], "structural")
        self.assertEqual(report["transition_slides"], [1])
        self.assertEqual(report["timing_slides"], [1])
        self.assertEqual(report["targeted_shape_ids"]["1"], [2])
        self.assertEqual(report["media_parts"], ["ppt/media/video1.mp4"])
        self.assertEqual(report["video_relationships"][0]["relationship_id"], "rId5")

    def test_rejects_missing_shape_target_and_media_part(self) -> None:
        module = load_script_module(
            "verify_pptx_motion_invalid", "scripts/verify_pptx_motion.py"
        )
        with tempfile.TemporaryDirectory() as tmp:
            pptx = Path(tmp) / "invalid.pptx"
            self._write_fixture(pptx, target_shape_id="99", include_media=False)
            report = module.inspect_pptx(pptx)

        self.assertFalse(report["ok"])
        codes = {error["code"] for error in report["errors"]}
        self.assertIn("MOTION_STRUCTURE_INVALID", codes)
        self.assertIn("VIDEO_EMBED_FAILED", codes)

    def test_rejects_non_zip_input(self) -> None:
        module = load_script_module(
            "verify_pptx_motion_bad_zip", "scripts/verify_pptx_motion.py"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "not-a-deck.pptx"
            path.write_text("not a zip", encoding="utf-8")
            report = module.inspect_pptx(path)
        self.assertFalse(report["ok"])
        self.assertEqual(report["errors"][0]["code"], "MOTION_STRUCTURE_INVALID")


class PptxMotionWriterTests(unittest.TestCase):
    def _write_static_fixture(self, path: Path, *, existing_timing: bool = False) -> None:
        timing = "<p:timing><p:tnLst/></p:timing>" if existing_timing else ""
        slide = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
 <p:cSld><p:spTree>
  <p:sp><p:nvSpPr><p:cNvPr id="2" name="First"/></p:nvSpPr><p:extLst/></p:sp>
  <p:sp><p:nvSpPr><p:cNvPr id="3" name="Second"/></p:nvSpPr></p:sp>
 </p:spTree></p:cSld>{timing}<p:extLst/></p:sld>'''
        with ZipFile(path, "w", ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", "<Types/>")
            archive.writestr("ppt/slides/slide1.xml", slide)

    def test_writes_basic_motion_without_changing_source(self) -> None:
        writer = load_script_module(
            "apply_pptx_basic_motion", "scripts/apply_pptx_basic_motion.py"
        )
        verifier = load_script_module(
            "verify_written_pptx_motion", "scripts/verify_pptx_motion.py"
        )
        plan = {
            "profile_id": "pptx_basic_v1",
            "slides": [
                {
                    "slide": 1,
                    "transition": "fade",
                    "builds": [
                        {
                            "shape_id": 2,
                            "effect": "appear",
                            "trigger": "on_click",
                            "duration_ms": 1,
                        },
                        {
                            "shape_id": 3,
                            "effect": "fade",
                            "trigger": "after_previous",
                            "duration_ms": 400,
                        },
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.pptx"
            output = Path(tmp) / "animated.pptx"
            self._write_static_fixture(source)
            source_bytes = source.read_bytes()
            result = writer.apply_motion(source, plan, output)
            report = verifier.inspect_pptx(output)
            self.assertEqual(source.read_bytes(), source_bytes)

        self.assertTrue(result["ok"])
        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["transition_slides"], [1])
        self.assertEqual(report["targeted_shape_ids"]["1"], [2, 3])

    def test_rejects_unsupported_effect_and_existing_timing(self) -> None:
        writer = load_script_module(
            "apply_pptx_basic_motion_invalid", "scripts/apply_pptx_basic_motion.py"
        )
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.pptx"
            output = Path(tmp) / "animated.pptx"
            self._write_static_fixture(source)
            bad_effect = {
                "profile_id": "pptx_basic_v1",
                "slides": [
                    {
                        "slide": 1,
                        "transition": "fade",
                        "builds": [
                            {
                                "shape_id": 2,
                                "effect": "fly_in",
                                "trigger": "on_click",
                                "duration_ms": 400,
                            }
                        ],
                    }
                ],
            }
            with self.assertRaisesRegex(writer.MotionPlanError, "unsupported effect"):
                writer.apply_motion(source, bad_effect, output)

            self._write_static_fixture(source, existing_timing=True)
            valid = {
                "profile_id": "pptx_basic_v1",
                "slides": [{"slide": 1, "transition": "fade", "builds": []}],
            }
            with self.assertRaisesRegex(writer.MotionPlanError, "existing timing"):
                writer.apply_motion(source, valid, output)

    def test_writes_grouped_in_slide_choreography(self) -> None:
        writer = load_script_module(
            "apply_grouped_pptx_motion", "scripts/apply_pptx_basic_motion.py"
        )
        verifier = load_script_module(
            "verify_grouped_pptx_motion", "scripts/verify_pptx_motion.py"
        )
        plan = {
            "profile_id": "pptx_basic_v1",
            "choreography_mode": "in_slide_grouped_v1",
            "slides": [
                {
                    "slide": 1,
                    "motion_job": "reveal a card as one visual unit",
                    "transition": "fade",
                    "groups": [
                        {
                            "group_id": "card_one",
                            "intent": "show card background and copy together",
                            "shape_ids": [2, 3],
                            "effect": "fade",
                            "trigger": "after_previous",
                            "duration_ms": 400,
                        }
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.pptx"
            output = Path(tmp) / "animated.pptx"
            self._write_static_fixture(source)
            result = writer.apply_motion(source, plan, output)
            report = verifier.inspect_pptx(output)
            with ZipFile(output) as archive:
                slide_xml = archive.read("ppt/slides/slide1.xml").decode("utf-8")

        self.assertTrue(result["ok"])
        self.assertEqual(result["choreography_mode"], "in_slide_grouped_v1")
        self.assertEqual(result["group_count"], 1)
        self.assertEqual(report["targeted_shape_ids"]["1"], [2, 3])
        self.assertIn('nodeType="afterEffect"', slide_xml)
        self.assertIn('nodeType="withEffect"', slide_xml)

    def test_writes_visible_card_and_image_entrance_filters(self) -> None:
        writer = load_script_module(
            "apply_visible_pptx_motion", "scripts/apply_pptx_basic_motion.py"
        )
        plan = {
            "profile_id": "pptx_basic_v1",
            "choreography_mode": "in_slide_grouped_v1",
            "slides": [
                {
                    "slide": 1,
                    "motion_job": "raise a card, then wipe in its conclusion",
                    "transition": "fade",
                    "groups": [
                        {
                            "group_id": "card",
                            "intent": "raise the card as one unit",
                            "shape_ids": [2],
                            "effect": "slide_from_bottom",
                            "trigger": "after_previous",
                            "duration_ms": 500,
                        },
                        {
                            "group_id": "conclusion",
                            "intent": "wipe in the conclusion",
                            "shape_ids": [3],
                            "effect": "wipe_right",
                            "trigger": "on_click",
                            "duration_ms": 500,
                        },
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.pptx"
            output = Path(tmp) / "animated.pptx"
            self._write_static_fixture(source)
            writer.apply_motion(source, plan, output)
            with ZipFile(output) as archive:
                slide_xml = archive.read("ppt/slides/slide1.xml").decode("utf-8")

        self.assertIn('filter="slide(fromBottom)"', slide_xml)
        self.assertIn('filter="wipe(right)"', slide_xml)

    def test_rejects_transition_only_or_duplicate_grouped_choreography(self) -> None:
        writer = load_script_module(
            "reject_invalid_grouped_pptx_motion", "scripts/apply_pptx_basic_motion.py"
        )
        transition_only = {
            "profile_id": "pptx_basic_v1",
            "choreography_mode": "in_slide_grouped_v1",
            "slides": [{"slide": 1, "transition": "fade", "builds": []}],
        }
        with self.assertRaisesRegex(writer.MotionPlanError, "at least one motion group"):
            writer._validate_plan(transition_only)

        duplicate_shape = {
            "profile_id": "pptx_basic_v1",
            "choreography_mode": "in_slide_grouped_v1",
            "slides": [
                {
                    "slide": 1,
                    "motion_job": "reveal two cards",
                    "transition": "fade",
                    "groups": [
                        {"group_id": "card_one", "intent": "first card", "shape_ids": [2], "effect": "fade", "trigger": "after_previous"},
                        {"group_id": "card_two", "intent": "second card", "shape_ids": [2, 3], "effect": "fade", "trigger": "after_previous"},
                    ],
                }
            ],
        }
        with self.assertRaisesRegex(writer.MotionPlanError, "multiple groups"):
            writer._validate_plan(duplicate_shape)

    def test_motion_execution_plan_requires_in_slide_choreography_rules(self) -> None:
        template = ROOT / "templates" / "motion-plan.json"
        self.assertTrue(template.is_file())
        payload = json.loads(read(template))
        self.assertEqual(payload["choreography_mode"], "in_slide_grouped_v1")
        self.assertTrue(payload["slides"][0]["groups"])

        runtime = "\n".join(
            read(path)
            for path in [
                ROOT / "CALLING_SPEC.md",
                ROOT / "references" / "motion-video-delivery.md",
                ROOT / "references" / "qa-checklist.md",
                ROOT / "templates" / "production-route.md",
                ROOT / "templates" / "outline.md",
            ]
        ).lower()
        for token in [
            "in-slide choreography",
            "grouped builds",
            "transition-only is insufficient",
            "semantic checkpoints",
            "motion-plan.json",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, runtime)


class PptxMotionNameResolverTests(unittest.TestCase):
    def test_resolves_exported_shape_names_before_motion_is_applied(self) -> None:
        resolver = load_script_module(
            "resolve_pptx_motion_shape_ids", "scripts/resolve_pptx_motion_shape_ids.py"
        )
        with tempfile.TemporaryDirectory() as tmp:
            pptx = Path(tmp) / "deck.pptx"
            plan_path = Path(tmp) / "plan.json"
            output = Path(tmp) / "resolved.json"
            slide_xml = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree>
    <p:sp><p:nvSpPr><p:cNvPr id="2" name="card-surface"/></p:nvSpPr></p:sp>
    <p:pic><p:nvPicPr><p:cNvPr id="23" name="source-image"/></p:nvPicPr></p:pic>
  </p:spTree></p:cSld>
</p:sld>'''
            with ZipFile(pptx, "w", ZIP_DEFLATED) as archive:
                archive.writestr("ppt/slides/slide1.xml", slide_xml)
            plan_path.write_text(
                json.dumps(
                    {
                        "profile_id": "pptx_basic_v1",
                        "choreography_mode": "in_slide_grouped_v1",
                        "slides": [
                            {
                                "slide": 1,
                                "motion_job": "reveal card and image",
                                "transition": "fade",
                                "groups": [
                                    {
                                        "group_id": "visual",
                                        "intent": "reveal the editable card and source image",
                                        "shape_names": ["card-surface", "source-image"],
                                        "shape_ids": [2, 8],
                                        "effect": "fade",
                                        "trigger": "after_previous",
                                        "duration_ms": 500,
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = resolver.resolve_shape_ids(pptx, plan_path, output)
            resolved = json.loads(output.read_text(encoding="utf-8"))

        self.assertTrue(report["ok"])
        self.assertEqual(resolved["slides"][0]["groups"][0]["shape_ids"], [2, 23])


class VideoAssetVerificationTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg required")
    def test_inspects_real_h264_video_metadata(self) -> None:
        module = load_script_module(
            "verify_video_asset", "scripts/verify_video_asset.py"
        )
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "sample.mp4"
            command = [
                shutil.which("ffmpeg"),
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=320x180:d=0.5",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-y",
                str(video),
            ]
            subprocess.run(command, check=True, capture_output=True)
            report = module.inspect_video(video)

        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["video"]["codec"], "h264")
        self.assertEqual(report["video"]["width"], 320)
        self.assertEqual(report["video"]["height"], 180)
        self.assertGreater(report["duration_seconds"], 0)

    def test_rejects_non_video_file(self) -> None:
        module = load_script_module(
            "verify_video_asset_invalid", "scripts/verify_video_asset.py"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "not-video.mp4"
            path.write_text("invalid", encoding="utf-8")
            report = module.inspect_video(path)
        self.assertFalse(report["ok"])
        self.assertEqual(report["errors"][0]["code"], "VIDEO_CODEC_UNSUPPORTED")


class WebMotionVerificationTests(unittest.TestCase):
    def test_browser_bridge_reveals_builds_and_plays_video(self) -> None:
        node = shutil.which("node")
        node_path = os.environ.get("NODE_PATH")
        if not node or not node_path:
            self.skipTest("NODE_PATH with Playwright is required")
        probe = subprocess.run(
            [node, "-e", "require('playwright')"],
            env=os.environ.copy(),
            capture_output=True,
            check=False,
        )
        if probe.returncode != 0:
            self.skipTest("Playwright is unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "sample.mp4"
            if shutil.which("ffmpeg"):
                subprocess.run(
                    [
                        shutil.which("ffmpeg"),
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-f",
                        "lavfi",
                        "-i",
                        "color=c=black:s=160x90:d=1",
                        "-c:v",
                        "libx264",
                        "-pix_fmt",
                        "yuv420p",
                        "-y",
                        str(video),
                    ],
                    check=True,
                    capture_output=True,
                )
            else:
                self.skipTest("ffmpeg is required for the browser video fixture")
            html = root / "deck.html"
            html.write_text(
                f'''<!doctype html><html><body>
<section data-scene-id="s1"><div data-build-id="b1">A</div><div data-build-id="b2">B</div>
<video data-video-id="v1" muted src="{video.as_uri()}"></video></section>
<script>
let index = 0;
window.__GUOZHI_DECK_QA__ = {{
 version: "1",
 getState() {{ return {{ sceneId: "s1", revealIndex: index, complete: index >= 2 }}; }},
 advance() {{ index = Math.min(2, index + 1); return this.getState(); }}
}};
</script></body></html>''',
                encoding="utf-8",
            )
            command = [
                node,
                str(ROOT / "scripts" / "verify_web_motion.mjs"),
                "--url",
                html.as_uri(),
                "--expect-builds",
                "2",
                "--expect-video",
                "--json",
            ]
            chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
            if chrome.is_file():
                command.extend(["--browser-executable", str(chrome)])
            completed = subprocess.run(
                command,
                env=os.environ.copy(),
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["states"][-1]["revealIndex"], 2)
        self.assertTrue(report["videos"][0]["playable"])


class RuntimePayloadValidationTests(unittest.TestCase):
    def _module(self, name: str = "validate_runtime_payload"):
        return load_script_module(name, "scripts/validate_runtime_payload.py")

    def _valid_agent_invocation(self) -> dict:
        return {
            "protocol_version": "1.1",
            "request_id": "req-agent-valid",
            "run_id": "run-agent-valid",
            "operation": "deck.create",
            "interaction_mode": "agent",
            "source": [
                {"type": "url", "location": "https://example.com/article", "role": "primary"}
            ],
            "constraints": {
                "language": "zh-CN",
                "page_count": 6,
                "deliverable": "pptx",
                "route_id": "native_pptx",
                "style_id": "ref-16-black-ai-collaboration-editorial",
                "rewrite_boundary": "rebuild",
                "speaker_notes": True,
                "motion": {
                    "requested": False,
                    "profile_id": "none",
                    "playback_targets": [],
                    "verification_required": "structural",
                    "advance": "manual",
                    "reduced_motion_fallback": True,
                },
                "video": {"requested": False},
            },
            "confirmation": {"status": "confirmed", "exact_text": "按此配置执行"},
        }

    def _valid_media_plan(self) -> dict:
        return {
            "protocol_version": "1.1",
            "request_id": "req-media-plan",
            "run_id": "run-media-plan",
            "style_lock": "ref-16-black-ai-collaboration-editorial",
            "style_authority": "ppt_style_lock",
            "source_precedence": "authorized_source_first",
            "text_policy": "editable_ppt_text",
            "media_treatment_authority": "style_pack_assets",
            "media_treatment_references": [
                "assets/style-library/style-packs/ref-16-black-ai-collaboration-editorial/body-01.png"
            ],
            "fallback_image_form_policy": "visual_intent_only",
            "slots": [
                {
                    "slot_id": "media-slide-03",
                    "slide": 3,
                    "visual_need": True,
                    "reader_block": "抽象流程缺少视觉锚点",
                    "visual_job": "把三步工作流转成可扫描的关系图",
                    "anchor_type": "explanatory",
                    "hero_thesis": "选择路径比工具数量更重要",
                    "must_show": ["输入", "判断", "输出"],
                    "asset_priority": [
                        "authorized_source",
                        "native_ppt",
                        "generated_visual",
                    ],
                    "image_form": "process",
                    "aspect_ratio": "custom_slot",
                    "character_mode": "none",
                    "character_id": None,
                    "ppt_style_lock": "ref-16-black-ai-collaboration-editorial",
                    "style_transform": "inherit_ppt_style",
                    "text_policy": "editable_ppt_text",
                    "motion_intent": "按流程阶段依次出现",
                    "confirmation_required": False,
                }
            ],
        }

    def test_accepts_complete_agent_invocation(self) -> None:
        report = self._module().validate_invocation(self._valid_agent_invocation())
        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["normalized"]["protocol_version"], "1.1")

    def test_normalizes_legacy_static_invocation(self) -> None:
        payload = self._valid_agent_invocation()
        payload["protocol_version"] = "1.0"
        payload["constraints"].pop("motion")
        payload["constraints"].pop("video")
        report = self._module("validate_runtime_legacy").validate_invocation(payload)
        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["normalized"]["protocol_version"], "1.1")
        self.assertEqual(
            report["normalized"]["constraints"]["motion"]["profile_id"], "none"
        )
        self.assertFalse(report["normalized"]["constraints"]["video"]["requested"])

    def test_rejects_route_deliverable_and_motion_conflicts(self) -> None:
        payload = self._valid_agent_invocation()
        payload["constraints"]["deliverable"] = "html"
        payload["constraints"]["motion"] = {
            "requested": True,
            "profile_id": "web_motion_v1",
            "playback_targets": ["browser"],
            "verification_required": "playback",
            "advance": "manual",
            "reduced_motion_fallback": True,
        }
        report = self._module("validate_runtime_conflict").validate_invocation(payload)
        codes = {error["code"] for error in report["errors"]}
        self.assertFalse(report["ok"])
        self.assertIn("ROUTE_DELIVERABLE_CONFLICT", codes)
        self.assertIn("MOTION_PROFILE_UNSUPPORTED", codes)

    def test_rejects_confirmed_create_with_missing_material_decisions(self) -> None:
        payload = self._valid_agent_invocation()
        for field in ["page_count", "style_id", "rewrite_boundary", "speaker_notes"]:
            payload["constraints"].pop(field)
        report = self._module("validate_runtime_missing").validate_invocation(payload)
        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "needs_input")
        self.assertEqual(
            set(report["unresolved_fields"]),
            {"page_count", "style_id", "rewrite_boundary", "speaker_notes"},
        )

    def test_dashiai_requires_theme_instead_of_style_id(self) -> None:
        payload = self._valid_agent_invocation()
        payload["constraints"].update(
            {"deliverable": "pptx", "route_id": "dashiai", "style_id": None}
        )
        report = self._module("validate_runtime_dashiai").validate_invocation(payload)
        self.assertIn("theme_id", report["unresolved_fields"])
        payload["constraints"]["theme_id"] = "theme-minimal-tech"
        report = self._module("validate_runtime_dashiai_valid").validate_invocation(payload)
        self.assertTrue(report["ok"], report["errors"])

    def test_result_state_semantics_are_enforced(self) -> None:
        module = self._module("validate_runtime_results")
        incomplete = {
            "protocol_version": "1.1",
            "request_id": "req-result",
            "run_id": "run-result",
            "operation": "deck.create",
            "status": "needs_input",
            "resolved_decisions": {},
            "unresolved_fields": [],
            "proposed_decisions": {},
            "artifacts": [],
            "verification": [],
            "warnings": [],
            "error": None,
            "next_action": None,
        }
        report = module.validate_result(incomplete)
        self.assertFalse(report["ok"])
        self.assertIn("RESULT_STATE_INVALID", {e["code"] for e in report["errors"]})

        completed = dict(incomplete)
        completed.update(
            {
                "status": "completed",
                "unresolved_fields": [],
                "artifacts": [
                    {"type": "pptx", "path": "/tmp/deck.pptx", "verified": False}
                ],
                "next_action": None,
            }
        )
        report = module.validate_result(completed)
        self.assertFalse(report["ok"])
        self.assertIn("ARTIFACT_UNVERIFIED", {e["code"] for e in report["errors"]})

        completed["artifacts"] = [
            {"type": "pptx", "path": "/tmp/missing-guozhi-deck.pptx", "verified": True}
        ]
        report = module.validate_result(completed)
        self.assertFalse(report["ok"])
        self.assertIn("ARTIFACT_MISSING", {e["code"] for e in report["errors"]})

        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = Path(temp_dir) / "deck.pptx"
            artifact.write_bytes(b"verified fixture")
            completed["artifacts"] = [
                {"type": "pptx", "path": str(artifact), "verified": True}
            ]
            report = module.validate_result(completed)
            self.assertTrue(report["ok"], report["errors"])

    def test_capability_handoff_requires_director_context_for_renderer(self) -> None:
        module = self._module("validate_runtime_handoff")
        payload = {
            "protocol_version": "1.1",
            "request_id": "req-handoff",
            "run_id": "run-handoff",
            "capability_id": "renderer-native-01",
            "role": "renderer",
            "status": "requested",
            "producer": "presentations",
            "input": {
                "director_package": "/tmp/package",
                "output_path": "/tmp/deck.pptx",
            },
            "output": {},
            "version": None,
            "error": None,
        }
        report = module.validate_handoff(payload)
        self.assertFalse(report["ok"])
        self.assertIn("director_context", report["unresolved_fields"])
        payload["director_context"] = {
            "route_id": "native_pptx",
            "page_count": 6,
            "style_lock": "ref-16-black-ai-collaboration-editorial",
            "story_digest": "sha256:demo",
        }
        report = module.validate_handoff(payload)
        self.assertTrue(report["ok"], report["errors"])

        payload["status"] = "completed"
        report = module.validate_handoff(payload)
        self.assertFalse(report["ok"])
        self.assertIn("output.artifacts", report["unresolved_fields"])
        payload["output"] = {
            "artifacts": [
                {"type": "pptx", "path": "/tmp/deck.pptx", "verified": True}
            ]
        }
        report = module.validate_handoff(payload)
        self.assertTrue(report["ok"], report["errors"])

    def test_media_plan_enforces_style_source_text_and_ip_rules(self) -> None:
        module = self._module("validate_runtime_media_plan")
        payload = self._valid_media_plan()
        report = module.validate_media_plan(payload)
        self.assertTrue(report["ok"], report["errors"])

        cases = [
            (
                "MEDIA_STYLE_AUTHORITY_CONFLICT",
                lambda item: item.update({"style_authority": "xiaohu_style"}),
            ),
            (
                "MEDIA_STYLE_AUTHORITY_CONFLICT",
                lambda item: item["slots"][0].update(
                    {"style_transform": "preserve_ip_skin"}
                ),
            ),
            (
                "MEDIA_STYLE_AUTHORITY_CONFLICT",
                lambda item: item["slots"][0].update(
                    {"ppt_style_lock": "another-style"}
                ),
            ),
            (
                "MEDIA_SOURCE_PRECEDENCE_INVALID",
                lambda item: item["slots"][0].update(
                    {
                        "asset_priority": [
                            "generated_visual",
                            "authorized_source",
                        ]
                    }
                ),
            ),
            (
                "MEDIA_TEXT_EDITABILITY_INVALID",
                lambda item: item["slots"][0].update(
                    {"text_policy": "baked_in"}
                ),
            ),
            (
                "MEDIA_TREATMENT_AUTHORITY_CONFLICT",
                lambda item: item.update(
                    {"media_treatment_authority": "visual_intent_adapter"}
                ),
            ),
            (
                "MEDIA_TREATMENT_REFERENCE_INVALID",
                lambda item: item.update({"media_treatment_references": []}),
            ),
            (
                "MEDIA_TREATMENT_REFERENCE_INVALID",
                lambda item: item.update(
                    {
                        "media_treatment_references": [
                            "assets/style-library/style-packs/ref-20-black-blue-saas-proposal/body-01.png"
                        ]
                    }
                ),
            ),
            (
                "MEDIA_IP_CONFIRMATION_REQUIRED",
                lambda item: item["slots"][0].update(
                    {
                        "character_mode": "optional_ip",
                        "character_id": "xiaohu-role-01",
                        "confirmation_required": False,
                    }
                ),
            ),
        ]
        for expected_code, mutate in cases:
            candidate = json.loads(json.dumps(payload))
            mutate(candidate)
            report = module.validate_media_plan(candidate)
            with self.subTest(expected_code=expected_code):
                self.assertFalse(report["ok"])
                self.assertIn(expected_code, {e["code"] for e in report["errors"]})

    def test_media_generator_handoff_requires_validated_media_plan_path(self) -> None:
        module = self._module("validate_runtime_media_handoff")
        plan = self._valid_media_plan()
        plan["request_id"] = "req-media-handoff"
        plan["run_id"] = "run-media-handoff"
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_path = Path(temp_dir) / "media-plan.json"
            plan_path.write_text(
                json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            digest = "sha256:" + hashlib.sha256(plan_path.read_bytes()).hexdigest()
            payload = {
                "protocol_version": "1.1",
                "request_id": "req-media-handoff",
                "run_id": "run-media-handoff",
                "capability_id": "xiaohu-media-generator-01",
                "role": "media_generator",
                "status": "requested",
                "producer": "xiaohu-ip-studio",
                "input": {
                    "media_slots": plan["slots"],
                    "generation_scope": "production_assets",
                },
                "output": {},
                "version": None,
                "director_context": {
                    "route_id": "native_pptx",
                    "page_count": 6,
                    "style_lock": "ref-16-black-ai-collaboration-editorial",
                    "story_digest": "sha256:demo",
                },
                "error": None,
            }
            report = module.validate_handoff(payload)
            self.assertFalse(report["ok"])
            self.assertIn(
                "director_context.media_plan_path", report["unresolved_fields"]
            )

            payload["director_context"].update(
                {
                    "media_plan_path": str(plan_path),
                    "media_plan_digest": digest,
                    "confirmation_status": "confirmed",
                }
            )
            report = module.validate_handoff(payload)
            self.assertTrue(report["ok"], report["errors"])

            payload["director_context"]["media_plan_path"] = str(
                Path(temp_dir) / "missing-media-plan.json"
            )
            report = module.validate_handoff(payload)
            self.assertFalse(report["ok"])
            self.assertIn("MEDIA_PLAN_UNREADABLE", {e["code"] for e in report["errors"]})

    def test_media_handoff_enforces_scope_confirmation_and_asset_proof(self) -> None:
        module = self._module("validate_runtime_media_scope")
        plan = self._valid_media_plan()
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_path = Path(temp_dir) / "media-plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            digest = "sha256:" + hashlib.sha256(plan_path.read_bytes()).hexdigest()
            payload = {
                "protocol_version": "1.1",
                "request_id": plan["request_id"],
                "run_id": plan["run_id"],
                "capability_id": "media-generator-01",
                "role": "media_generator",
                "status": "requested",
                "producer": "media-adapter",
                "input": {
                    "media_slots": plan["slots"],
                    "generation_scope": "production_assets",
                },
                "output": {},
                "version": None,
                "director_context": {
                    "route_id": "native_pptx",
                    "page_count": 6,
                    "style_lock": plan["style_lock"],
                    "story_digest": "sha256:demo",
                    "media_plan_path": str(plan_path),
                    "media_plan_digest": digest,
                    "confirmation_status": "pending",
                },
                "error": None,
            }
            report = module.validate_handoff(payload)
            self.assertFalse(report["ok"])
            self.assertIn("MEDIA_GENERATION_NOT_CONFIRMED", {e["code"] for e in report["errors"]})

            payload["input"]["generation_scope"] = "baseline_preview"
            report = module.validate_handoff(payload)
            self.assertTrue(report["ok"], report["errors"])

            payload["director_context"]["confirmation_status"] = "confirmed"
            payload["input"]["generation_scope"] = "production_assets"
            payload["status"] = "completed"
            payload["output"] = {"assets": [{"slot_id": "media-slide-03"}]}
            report = module.validate_handoff(payload)
            self.assertFalse(report["ok"])
            self.assertIn("MEDIA_ASSET_PROOF_INVALID", {e["code"] for e in report["errors"]})

            payload["output"] = {
                "assets": [
                    {
                        "asset_id": "asset-slide-03",
                        "slot_id": "media-slide-03",
                        "path_or_url": "https://example.com/asset-slide-03.png",
                        "source_type": "generated_visual",
                        "ppt_style_lock": plan["style_lock"],
                        "style_transform": "inherit_ppt_style",
                        "text_policy": "editable_ppt_text",
                        "provenance": "media-adapter:job-123",
                        "verified": True,
                    }
                ]
            }
            report = module.validate_handoff(payload)
            self.assertTrue(report["ok"], report["errors"])

    def test_manifest_rejects_production_media_before_run_confirmation(self) -> None:
        module = self._module("validate_runtime_media_manifest_state")
        plan = self._valid_media_plan()
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_path = Path(temp_dir) / "media-plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            digest = "sha256:" + hashlib.sha256(plan_path.read_bytes()).hexdigest()
            handoff = {
                "protocol_version": "1.1",
                "request_id": plan["request_id"],
                "run_id": plan["run_id"],
                "capability_id": "media-generator-early",
                "role": "media_generator",
                "status": "requested",
                "producer": "media-adapter",
                "input": {
                    "media_slots": plan["slots"],
                    "generation_scope": "production_assets",
                },
                "output": {},
                "version": None,
                "director_context": {
                    "route_id": "native_pptx",
                    "page_count": 6,
                    "style_lock": plan["style_lock"],
                    "story_digest": "sha256:demo",
                    "media_plan_path": str(plan_path),
                    "media_plan_digest": digest,
                    "confirmation_status": "confirmed",
                },
                "error": None,
            }
            manifest = json.loads(read(ROOT / "templates" / "run-manifest.json"))
            manifest.update(
                {
                    "request_id": plan["request_id"],
                    "run_id": plan["run_id"],
                    "status": "needs_input",
                    "state_history": ["received", "normalized", "needs_input"],
                    "unresolved_fields": ["page_count"],
                    "next_action": "Confirm page count.",
                    "capabilities": [handoff],
                }
            )
            report = module.validate_manifest(manifest)
            self.assertFalse(report["ok"])
            self.assertIn(
                "MANIFEST_CAPABILITY_CONFIRMATION_MISMATCH",
                {e["code"] for e in report["errors"]},
            )

    def test_manifest_rejects_capability_from_another_request_or_run(self) -> None:
        module = self._module("validate_runtime_handoff_manifest_binding")
        manifest = json.loads(read(ROOT / "templates" / "run-manifest.json"))
        manifest.update({"request_id": "req-current", "run_id": "run-current"})
        manifest["capabilities"] = [
            {
                "protocol_version": "1.1",
                "request_id": "req-other",
                "run_id": "run-other",
                "capability_id": "source-adapter-other-run",
                "role": "source_adapter",
                "status": "requested",
                "producer": "source-provider",
                "input": {"sources": [{"type": "url", "location": "https://example.com"}]},
                "output": {},
                "version": None,
                "error": None,
            }
        ]
        report = module.validate_manifest(manifest)
        self.assertFalse(report["ok"])
        self.assertIn("HANDOFF_CONTEXT_MISMATCH", {e["code"] for e in report["errors"]})

    def test_malformed_media_handoff_returns_structured_errors(self) -> None:
        module = self._module("validate_runtime_malformed_media_handoff")
        payload = {
            "protocol_version": "1.1",
            "request_id": "req-malformed-media",
            "run_id": "run-malformed-media",
            "capability_id": "media-malformed",
            "role": "media_generator",
            "status": "completed",
            "producer": "media-provider",
            "input": {
                "media_slots": [{"slot_id": "slot-1"}],
                "generation_scope": ["production_assets"],
            },
            "output": {
                "assets": [
                    {
                        "asset_id": "asset-1",
                        "slot_id": "slot-1",
                        "path_or_url": "https://example.com/asset.png",
                        "source_type": ["generated_visual"],
                        "ppt_style_lock": "style-1",
                        "style_transform": "inherit_ppt_style",
                        "text_policy": "editable_ppt_text",
                        "provenance": "provider:job",
                        "verified": True,
                    }
                ]
            },
            "version": None,
            "director_context": {
                "route_id": "native_pptx",
                "page_count": 1,
                "style_lock": "style-1",
                "story_digest": "sha256:demo",
                "media_plan_path": 123,
                "media_plan_digest": [],
                "confirmation_status": [],
            },
            "error": None,
        }
        report = module.validate_handoff(payload)
        self.assertFalse(report["ok"])
        self.assertIn("PAYLOAD_TYPE_INVALID", {e["code"] for e in report["errors"]})

    def test_confirmed_agent_media_orchestration_happy_path(self) -> None:
        module = self._module("validate_runtime_agent_media_happy_path")
        invocation = self._valid_agent_invocation()
        self.assertTrue(module.validate_invocation(invocation)["ok"])

        plan = self._valid_media_plan()
        plan["request_id"] = invocation["request_id"]
        plan["run_id"] = invocation["run_id"]
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_path = Path(temp_dir) / "media-plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            digest = "sha256:" + hashlib.sha256(plan_path.read_bytes()).hexdigest()
            handoff = {
                "protocol_version": "1.1",
                "request_id": invocation["request_id"],
                "run_id": invocation["run_id"],
                "capability_id": "media-generator-confirmed",
                "role": "media_generator",
                "status": "requested",
                "producer": "media-provider",
                "input": {
                    "media_slots": plan["slots"],
                    "generation_scope": "production_assets",
                },
                "output": {},
                "version": None,
                "director_context": {
                    "route_id": "native_pptx",
                    "page_count": 6,
                    "style_lock": plan["style_lock"],
                    "story_digest": "sha256:demo",
                    "media_plan_path": str(plan_path),
                    "media_plan_digest": digest,
                    "confirmation_status": "confirmed",
                },
                "error": None,
            }
            self.assertTrue(module.validate_handoff(handoff)["ok"])

            manifest = json.loads(read(ROOT / "templates" / "run-manifest.json"))
            manifest.update(
                {
                    "request_id": invocation["request_id"],
                    "run_id": invocation["run_id"],
                    "interaction_mode": "agent",
                    "status": "planned",
                    "state_history": ["received", "normalized", "confirmed", "planned"],
                    "source": [
                        {
                            "source_id": "source-1",
                            "type": "url",
                            "path_or_url": "https://example.com/article",
                        }
                    ],
                    "unresolved_fields": [],
                    "capabilities": [handoff],
                    "confirmation": invocation["confirmation"],
                }
            )
            manifest["resolved_decisions"].update(invocation["constraints"])
            report = module.validate_manifest(manifest)
            self.assertTrue(report["ok"], report["errors"])

    def test_malformed_payloads_return_structured_errors(self) -> None:
        module = self._module("validate_runtime_malformed")
        invocation = module.validate_invocation(
            {
                "protocol_version": "1.1",
                "request_id": "req-malformed",
                "operation": ["deck.create"],
                "interaction_mode": "agent",
                "constraints": [],
            }
        )
        self.assertFalse(invocation["ok"])
        self.assertTrue(invocation["errors"] or invocation["unresolved_fields"])

        invocation = module.validate_invocation(
            {
                "protocol_version": "1.1",
                "request_id": "req-typo",
                "operation": "deck.create",
                "interaction_mode": "agent",
                "source": [
                    {"type": "url", "location": "https://example.com/article"}
                ],
                "constraints": {"page_counts": 6},
            }
        )
        self.assertFalse(invocation["ok"])
        self.assertIn("FIELD_UNKNOWN", {item["code"] for item in invocation["errors"]})

        invocation = module.validate_invocation([])
        self.assertFalse(invocation["ok"])
        self.assertIn("PAYLOAD_TYPE_INVALID", {item["code"] for item in invocation["errors"]})

        result = module.validate_result(
            {
                "protocol_version": "1.1",
                "request_id": "req-malformed",
                "run_id": None,
                "operation": "deck.create",
                "status": ["completed"],
                "resolved_decisions": {},
                "unresolved_fields": [],
                "proposed_decisions": {},
                "artifacts": [],
                "verification": [],
                "warnings": [],
                "error": None,
                "next_action": None,
            }
        )
        self.assertFalse(result["ok"])
        self.assertIn("RESULT_STATE_INVALID", {item["code"] for item in result["errors"]})

    def test_manifest_enforces_state_order_and_capability_handoffs(self) -> None:
        module = self._module("validate_runtime_manifest")
        manifest = json.loads(read(ROOT / "templates" / "run-manifest.json"))
        manifest.update(
            {
                "request_id": "req-manifest",
                "run_id": "run-manifest",
                "status": "rendering",
                "state_history": ["received", "rendering"],
            }
        )
        report = module.validate_manifest(manifest)
        self.assertFalse(report["ok"])
        self.assertIn("STATE_TRANSITION_INVALID", {e["code"] for e in report["errors"]})

        manifest.update(
            {
                "status": "planned",
                "state_history": ["received", "normalized", "confirmed", "planned"],
                "source": [{"source_id": "src-1", "type": "url", "path_or_url": "https://example.com"}],
                "unresolved_fields": [],
                "confirmation": {"status": "confirmed", "exact_text": "确认"},
            }
        )
        manifest["resolved_decisions"].update(
            {
                "page_count": 6,
                "deliverable": "pptx",
                "route_id": "native_pptx",
                "style_id": "ref-16-black-ai-collaboration-editorial",
                "rewrite_boundary": "rebuild",
                "speaker_notes": True,
            }
        )
        report = module.validate_manifest(manifest)
        self.assertTrue(report["ok"], report["errors"])

        manifest.update(
            {
                "status": ["failed"],
                "state_history": ["received", ["failed"]],
                "confirmation": {"status": ["confirmed"], "exact_text": "确认"},
            }
        )
        report = module.validate_manifest(manifest)
        self.assertFalse(report["ok"])
        self.assertIn("STATE_TRANSITION_INVALID", {e["code"] for e in report["errors"]})


class IntentRoutingContractTests(unittest.TestCase):
    def test_every_operation_has_positive_and_ambiguous_cases(self) -> None:
        registry = json.loads(read(ROOT / "contracts" / "intent-registry.json"))
        operations = {
            "deck.create",
            "deck.revise",
            "deck.review",
            "style.list",
            "style.add",
            "style.update",
            "style.remove",
            "help",
        }
        by_id = {entry["id"]: entry for entry in registry["operations"]}
        self.assertEqual(set(by_id), operations)
        for operation in operations:
            with self.subTest(operation=operation):
                self.assertGreaterEqual(len(by_id[operation]["positive_examples"]), 2)
        self.assertGreaterEqual(len(registry["ambiguous_examples"]), 3)
        self.assertTrue(
            all(item["expected_status"] == "needs_input" for item in registry["ambiguous_examples"])
        )

    def test_trigger_metadata_covers_motion_video_review_and_style_management(self) -> None:
        frontmatter = read(ROOT / "SKILL.md").split("---", 2)[1].lower()
        for token in ["motion", "video", "review", "style library", "agent"]:
            with self.subTest(token=token):
                self.assertIn(token, frontmatter)

    def test_calling_spec_has_no_stale_protocol_1_0_run_output(self) -> None:
        self.assertNotIn("new protocol `1.0` run", read(ROOT / "CALLING_SPEC.md"))

if __name__ == "__main__":
    unittest.main()

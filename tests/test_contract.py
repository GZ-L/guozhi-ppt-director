from __future__ import annotations

import json
import subprocess
import sys
import unittest
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

    def test_machine_contract_files_exist_and_parse(self) -> None:
        paths = [
            ROOT / "contracts" / "route-registry.json",
            ROOT / "contracts" / "invocation.schema.json",
            ROOT / "contracts" / "result.schema.json",
            ROOT / "templates" / "run-manifest.json",
        ]
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue(path.is_file())
                json.loads(read(path))

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


if __name__ == "__main__":
    unittest.main()

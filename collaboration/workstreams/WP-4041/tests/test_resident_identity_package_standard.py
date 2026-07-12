import copy
import hashlib
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLES = sorted((ROOT / "examples").glob("*_identity_package.yaml"))
ALLOWED_AUTHORITY = {"none", "advisory", "operational_support", "office_delegate", "steward_delegated"}
READINESS = ["draft", "character_review_ready", "identity_complete", "presentation_ready", "runtime_ready", "commissioned", "revision_required", "retired"]
REQUIRED_TOP = {"contract", "canonical_identity", "character_bible", "physical_identity", "voice_identity", "visual_presentation", "office_environment", "relationships", "preferences_and_growth", "runtime_presentation_contract", "validation_and_commissioning", "privacy", "provenance", "implementation_bindings"}


def load(path):
    # Example .yaml files are intentionally JSON-compatible YAML for stdlib deterministic validation.
    return json.loads(path.read_text())


class ResidentIdentityPackageStandardTests(unittest.TestCase):
    def test_all_examples_validate(self):
        self.assertEqual(len(EXAMPLES), 5)
        for path in EXAMPLES:
            pkg = load(path)
            self.assertTrue(REQUIRED_TOP.issubset(pkg))
            self.assertEqual(pkg["contract"], {"name": "estate.resident_identity_package", "version": "1.0.0"})
            self.assertRegex(pkg["canonical_identity"]["resident_id"], r"^resident\.[a-z0-9_]+$")
            self.assertGreaterEqual(len(pkg["canonical_identity"]["identity_anchors"]), 3)
            self.assertTrue(pkg["physical_identity"]["non_explicit"])

    def test_identity_and_implementation_bindings_remain_separate(self):
        for path in EXAMPLES:
            pkg = load(path)
            identity_before = copy.deepcopy(pkg["canonical_identity"])
            pkg["implementation_bindings"] = {"provider": "new", "model": "new", "voice_engine": "new", "portrait_renderer": "new", "interface": "new"}
            self.assertEqual(identity_before, pkg["canonical_identity"])

    def test_readiness_state_required_fields(self):
        for path in EXAMPLES:
            pkg = load(path)
            state = pkg["validation_and_commissioning"].get("readiness_state")
            self.assertIn(state, READINESS)
            if READINESS.index(state) >= READINESS.index("identity_complete"):
                for section in ["canonical_identity", "character_bible", "physical_identity", "voice_identity", "privacy", "provenance"]:
                    self.assertTrue(pkg[section])

    def test_audience_scoped_private_fields(self):
        allowed_scopes = {"public", "resident", "steward", "office", "restricted"}
        for path in EXAMPLES:
            pkg = load(path)
            for field in pkg["privacy"]["audience_scoped_fields"]:
                self.assertIn(field["scope"], allowed_scopes)
                self.assertNotEqual(field["scope"], "public")

    def test_provider_model_voice_portrait_replacement_without_identity_mutation(self):
        for path in EXAMPLES:
            pkg = load(path)
            before = hashlib.sha256(json.dumps(pkg["canonical_identity"], sort_keys=True).encode()).hexdigest()
            pkg["implementation_bindings"].update(provider="p2", model="m2", voice_engine="v2", portrait_renderer="r2")
            after = hashlib.sha256(json.dumps(pkg["canonical_identity"], sort_keys=True).encode()).hexdigest()
            self.assertEqual(before, after)

    def test_relationship_scope_enforcement(self):
        allowed = {"public", "resident", "steward", "office", "restricted"}
        for path in EXAMPLES:
            pkg = load(path)
            self.assertIn(pkg["relationships"]["steward"]["scope"], allowed)
            for rel in pkg["relationships"]["active_residents"]:
                self.assertIn(rel["scope"], allowed)

    def test_wp4053_preference_evolution_linkage_without_silent_drift(self):
        needs_evidence = {"evolving", "changed", "retired", "disputed"}
        for path in EXAMPLES:
            pkg = load(path)
            self.assertIn("WP-4053", pkg["preferences_and_growth"]["wp_4053_linkage"])
            for pref in pkg["preferences_and_growth"]["preferences"]:
                if pref["category"] in needs_evidence:
                    self.assertIn("WP-4053", pref.get("wp_4053_evidence", ""))

    def test_rejection_of_unknown_authority_claims(self):
        for path in EXAMPLES:
            pkg = load(path)
            self.assertIn(pkg["canonical_identity"]["authority_summary"]["claim"], ALLOWED_AUTHORITY)
        bad = load(EXAMPLES[0])
        bad["canonical_identity"]["authority_summary"]["claim"] = "unlimited"
        self.assertNotIn(bad["canonical_identity"]["authority_summary"]["claim"], ALLOWED_AUTHORITY)

    def test_deterministic_serialization(self):
        for path in EXAMPLES:
            pkg = load(path)
            a = json.dumps(pkg, sort_keys=True, separators=(",", ":"))
            b = json.dumps(load(path), sort_keys=True, separators=(",", ":"))
            self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()

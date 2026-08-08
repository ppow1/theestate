import os
import unittest

os.environ.setdefault("WEBUI_SECRET_KEY", "estate-binding-test-key-20260807")

from open_webui.utils.middleware import _estate_allowed_tool_params


class TestOpenWebUIMCPArgumentBinding(unittest.TestCase):
    def test_required_mcp_fields_survive_when_schema_omits_properties(self):
        self.assertEqual(_estate_allowed_tool_params({
            "parameters": {"required": ["request_id"]}
        }), {"request_id"})


    def test_declared_and_required_mcp_fields_are_preserved_without_duplicates(self):
        self.assertEqual(_estate_allowed_tool_params({
        "parameters": {
            "properties": {"claim_next": {"type": "boolean"}},
            "required": ["worker_id", "claim_next"],
        }
        }), {"claim_next", "worker_id"})


    def test_comms8_create_required_arguments_are_all_bindable(self):
        self.assertEqual(_estate_allowed_tool_params({
        "parameters": {
            "required": ["workflow_id", "objective", "input_data", "idempotency_key"]
        }
        }), {"workflow_id", "objective", "input_data", "idempotency_key"})


if __name__ == "__main__":
    unittest.main()

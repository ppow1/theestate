import ast
from pathlib import Path
from uuid import uuid4


MIDDLEWARE = Path(r"A:\AI\OpenWebUI\.venv\Lib\site-packages\open_webui\utils\middleware.py")


def _load_followup_normalizer():
    tree = ast.parse(MIDDLEWARE.read_text(encoding="utf-8"))
    wanted = {"_estate_followup_output_from_response", "output_id"}
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in wanted]
    namespace = {
        "get_response_data": lambda response: (response, response),
        "uuid4": uuid4,
    }
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(MIDDLEWARE), "exec"), namespace)
    return namespace["_estate_followup_output_from_response"]


def _load_explicit_choice():
    tree = ast.parse(MIDDLEWARE.read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_estate_explicit_mcp_tool_choice")
    namespace = {"json": __import__("json"), "re": __import__("re")}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(MIDDLEWARE), "exec"), namespace)
    return namespace["_estate_explicit_mcp_tool_choice"]


def test_tool_result_followup_json_response_is_returned_to_assistant():
    normalize = _load_followup_normalizer()
    response = {
        "choices": [{"message": {"role": "assistant", "content": "authoritative read result"}}]
    }

    output = normalize(response)

    assert output[0]["role"] == "assistant"
    assert output[0]["content"][0]["text"] == "authoritative read result"
    assert output[0]["status"] == "completed"


def test_tool_result_followup_preserves_backend_output_items():
    normalize = _load_followup_normalizer()
    backend_output = [{"type": "message", "status": "completed", "content": [{"text": "result"}]}]

    assert normalize({"output": backend_output}) == backend_output


def test_tool_result_followup_failure_is_not_treated_as_assistant_success():
    normalize = _load_followup_normalizer()

    try:
        normalize({"error": {"detail": "follow-up failed"}})
    except RuntimeError as exc:
        assert "follow-up failed" in str(exc)
    else:
        raise AssertionError("provider follow-up error was silently accepted")


def test_exact_enabled_comms8_action_gets_named_native_tool_choice():
    choose = _load_explicit_choice()
    tools = {
        "estate_comms8_read_request": {
            "type": "mcp",
            "spec": {"name": "estate_comms8_read_request", "parameters": {"type": "object"}},
        },
        "get_current_objective": {
            "type": "function",
            "spec": {"name": "get_current_objective", "parameters": {"type": "object"}},
        },
    }

    assert choose(
        [{"role": "user", "content": "Call estate_comms8_read_request for ec8-test."}], tools
    ) == {"type": "function", "function": {"name": "estate_comms8_read_request"}}


def test_natural_language_without_exact_name_keeps_automatic_selection():
    choose = _load_explicit_choice()
    tools = {
        "estate_comms8_read_request": {
            "type": "mcp",
            "spec": {"name": "estate_comms8_read_request", "parameters": {"type": "object"}},
        }
    }
    assert choose([{"role": "user", "content": "Read the current Estate request."}], tools) is None

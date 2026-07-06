import json, os, subprocess, sys
from pathlib import Path
from wsgiref.util import setup_testing_defaults

from estate.ai_services.manifest import validate_manifest
from estate.ai_services.discovery import rediscover
from estate.ai_services.control import request
from estate.ai_services.policy import evaluate
from estate.ai_services.api import app, serve


def _manifest(service_id="textgen", endpoint="http://127.0.0.1:5000/v1"):
    return {"service_id":service_id,"display_name":"TextGen","service_type":"model_runtime","local_only":True,"host_policy":{"bind":"127.0.0.1","allow_public_bind":False},"default_endpoint":endpoint,"ports":[5000],"paths":{"models":"A:\\AI\\TextGen\\models"},"operations":{"status":{"api_template":"GET /v1/models"},"load_model":{"command_template":"load {model}"}},"approval":{"load_model":{"required":True},"stop":{"required":True}}}


def _write(root, data, name="textgen"):
    p=root/"runtime/ai_services/implementations"/name
    p.mkdir(parents=True)
    (p/"service.manifest.json").write_text(json.dumps(data), encoding="utf-8")


def test_manifest_schema_validation_and_cloud_rejection():
    assert validate_manifest(_manifest())["valid"] is True
    check = validate_manifest(_manifest(endpoint="https://api.example.com"))
    assert check["valid"] is False
    assert any(e["type"] == "non_loopback_endpoint_rejected" for e in check["errors"])


def test_rediscovery_scans_manifests_and_rejects_unsafe_without_moving_models(tmp_path):
    _write(tmp_path, _manifest())
    _write(tmp_path, {**_manifest("bad", "http://0.0.0.0:9999"), "local_only": False}, "bad")
    reg=rediscover(tmp_path, actor="codex")
    assert reg["service_count"] == 1
    assert reg["services"][0]["service_id"] == "textgen"
    assert reg["rejected_manifests"]
    assert not (tmp_path/"A:/AI/TextGen/models").exists()
    assert (tmp_path/"runtime/ai_services/state.json").exists()


def test_loopback_policy_and_alfred_gate():
    svc=_manifest()
    assert evaluate("status", svc, actor="alfred", host="127.0.0.1")["allowed"] is True
    assert evaluate("status", svc, actor="alfred", host="0.0.0.0")["allowed"] is False
    assert evaluate("load_model", svc, actor="alfred")["allowed"] is False
    assert evaluate("load_model", svc, actor="alfred", approved_by="steward")["allowed"] is True
    assert evaluate("delete", svc, actor="alfred", approved_by="steward")["allowed"] is False


def test_textgen_model_load_planning_and_audit_allowed_and_denied(tmp_path):
    _write(tmp_path, _manifest())
    rediscover(tmp_path)
    denied=request("load_model", "textgen", actor="alfred", root=tmp_path, model="Qwen3.gguf")
    allowed=request("load_model", "textgen", actor="alfred", approved_by="steward", root=tmp_path, model="Qwen3.gguf")
    assert denied["policy"]["allowed"] is False
    assert allowed["planned_command"] == "load Qwen3.gguf"
    lines=(tmp_path/"runtime/ai_services/audit_log.jsonl").read_text().splitlines()
    assert any('"policy_result": "denied"' in line for line in lines)
    assert any('"policy_result": "allowed"' in line for line in lines)


def test_cli_status_and_rediscover_commands(tmp_path):
    _write(tmp_path, _manifest())
    env={**os.environ, "PYTHONPATH": str(Path.cwd()/"src"), "ESTATE_ROOT": str(tmp_path)}
    r=subprocess.run([sys.executable,"-m","estate.cli.main","ai-services","rediscover","--json"], env=env, cwd=tmp_path, text=True, capture_output=True, check=True)
    assert json.loads(r.stdout)["service_count"] == 1
    r=subprocess.run([sys.executable,"-m","estate.cli.main","ai-services","status","--json"], env=env, cwd=tmp_path, text=True, capture_output=True, check=True)
    assert json.loads(r.stdout)["local_only"] is True


def test_api_status_endpoint_and_loopback_serve_policy():
    environ={"PATH_INFO":"/ai-services/status","REQUEST_METHOD":"GET"}; setup_testing_defaults(environ)
    captured={}
    body=b"".join(app(environ, lambda status, headers: captured.update(status=status, headers=headers)))
    assert captured["status"].startswith("200")
    assert json.loads(body)["local_only"] is True
    try:
        serve(host="0.0.0.0")
    except ValueError as e:
        assert "loopback" in str(e)
    else:
        raise AssertionError("public bind was not rejected")

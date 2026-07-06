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

class _Runner:
    def __init__(self): self.started=[]; self.stopped=[]
    def start(self, command, cwd=None, log_path=None):
        self.started.append({"command":command,"cwd":cwd,"log_path":log_path}); return {"pid":4321}
    def stop(self, pid):
        self.stopped.append(pid); return {"stopped":True,"pid":pid}


def test_dry_run_start_returns_plan_without_launching(tmp_path):
    data=_manifest(); data["operations"]["start"]={"command_template":"textgen.bat --listen"}; data["approval"]["start"]={"required":True}
    _write(tmp_path, data); rediscover(tmp_path); runner=_Runner()
    plan=request("start","textgen",actor="alfred",approved_by="steward",root=tmp_path,dry_run=True,runner=runner)
    assert plan["result"] == "planned"
    assert plan["approval_state"] == "approved"
    assert runner.started == []


def test_start_without_approval_records_requires_approval(tmp_path):
    data=_manifest(); data["operations"]["start"]={"command_template":"textgen.bat --listen"}; data["approval"]["start"]={"required":True}
    _write(tmp_path, data); rediscover(tmp_path)
    plan=request("start","textgen",actor="alfred",root=tmp_path,dry_run=False)
    assert plan["approval_state"] == "requires_approval"
    assert (tmp_path/"runtime/ai_services/approvals.json").exists()


def test_start_with_approval_uses_runner_and_records_process_state(tmp_path):
    data=_manifest(); data["operations"]["start"]={"command_template":"textgen.bat --listen"}; data["approval"]["start"]={"required":True}
    _write(tmp_path, data); rediscover(tmp_path); runner=_Runner()
    plan=request("start","textgen",actor="alfred",approved_by="steward",root=tmp_path,dry_run=False,runner=runner)
    assert plan["result"] == "executed"
    assert runner.started and runner.started[0]["command"] == "textgen.bat --listen"
    state=json.loads((tmp_path/"runtime/ai_services/state.json").read_text())
    assert state["processes"]["textgen"]["pid"] == 4321


def test_stop_only_targets_tracked_process(tmp_path):
    data=_manifest(); data["operations"]["stop"]={"command_template":"stop tracked"}
    _write(tmp_path, data); rediscover(tmp_path); runner=_Runner()
    denied=request("stop","textgen",actor="alfred",approved_by="steward",root=tmp_path,dry_run=False,runner=runner)
    assert denied["result"] == "failed" and "no_tracked_process" in denied["error"]
    state={"version":"ai-services-state-v1","services":{},"processes":{"textgen":{"pid":1234,"current_status":"running"}}}
    (tmp_path/"runtime/ai_services/state.json").write_text(json.dumps(state))
    ok=request("stop","textgen",actor="alfred",approved_by="steward",root=tmp_path,dry_run=False,runner=runner)
    assert ok["result"] == "executed" and runner.stopped == [1234]


def test_textgen_model_load_model_name_validation(tmp_path):
    models=tmp_path/"models"; models.mkdir(); (models/"Qwen3-8B-Q6_K.gguf").write_text("x")
    data=_manifest(); data["paths"]["models"]=str(models)
    _write(tmp_path, data); rediscover(tmp_path)
    ok=request("load_model","textgen",actor="alfred",approved_by="steward",root=tmp_path,model="Qwen3-8B-Q6_K.gguf")
    assert ok["policy"]["allowed"] is True
    for bad in ["../secret.gguf", "a;b.gguf", "sub/model.gguf", "missing.gguf"]:
        res=request("load_model","textgen",actor="alfred",approved_by="steward",root=tmp_path,model=bad)
        assert res["policy"]["allowed"] is False


def test_textgen_model_load_approval_and_execution(tmp_path):
    data=_manifest(); _write(tmp_path, data); rediscover(tmp_path); runner=_Runner()
    need=request("load_model","textgen",actor="alfred",root=tmp_path,model="Qwen3.gguf",dry_run=False,runner=runner)
    assert need["approval_state"] == "requires_approval"
    ok=request("load_model","textgen",actor="alfred",approved_by="steward",root=tmp_path,model="Qwen3.gguf",dry_run=False,runner=runner)
    assert ok["result"] == "executed"
    assert runner.started and "Qwen3.gguf" in runner.started[0]["command"]


def test_audit_log_distinguishes_planned_denied_approved_executed(tmp_path):
    data=_manifest(); data["operations"]["start"]={"command_template":"textgen.bat --listen"}; data["approval"]["start"]={"required":True}
    _write(tmp_path, data); rediscover(tmp_path); runner=_Runner()
    request("start","textgen",actor="alfred",approved_by="steward",root=tmp_path,dry_run=True)
    request("load_model","textgen",actor="alfred",root=tmp_path,model="../bad")
    request("start","textgen",actor="alfred",approved_by="steward",root=tmp_path,dry_run=False,runner=runner)
    text=(tmp_path/"runtime/ai_services/audit_log.jsonl").read_text()
    assert "planned_dry_run" in text and "policy_denied" in text and "approval_granted" in text and "execution_succeeded" in text


def test_cloud_endpoint_and_alfred_boundary_remain_rejected():
    svc=_manifest(endpoint="https://api.example.com")
    assert evaluate("status", svc, actor="alfred")["allowed"] is False
    assert evaluate("delete", _manifest(), actor="alfred", approved_by="steward")["allowed"] is False

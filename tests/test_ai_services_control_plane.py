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
    def __init__(self, alive=True): self.started=[]; self.stopped=[]; self.alive=alive
    def start(self, command, cwd=None, log_path=None):
        self.started.append({"command":command,"cwd":cwd,"log_path":log_path}); return {"pid":4321}
    def stop(self, pid):
        self.stopped.append(pid); return {"stopped":True,"pid":pid}
    def is_alive(self, pid):
        return self.alive

class _Health:
    def __init__(self, healthy=True, error="connection_refused", status=None):
        self.healthy=healthy; self.error=error; self.status=status; self.calls=[]
    def check(self, endpoint, timeout_seconds=30, interval_seconds=2, runner=None, pid=None):
        self.calls.append(endpoint)
        if self.healthy:
            return {"healthy":True,"status":"healthy","attempts":1,"pid_alive":True}
        return {"healthy":False,"status":self.status or "health_failed","error":self.error,"attempts":1,"pid_alive":False if self.status=="process_exited" else True}


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
    plan=request("start","textgen",actor="alfred",approved_by="steward",root=tmp_path,dry_run=False,runner=runner,health_checker=_Health(True))
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
    ok=request("load_model","textgen",actor="alfred",approved_by="steward",root=tmp_path,model="Qwen3.gguf",dry_run=False,runner=runner,health_checker=_Health(True))
    assert ok["result"] == "executed"
    assert runner.started and "Qwen3.gguf" in runner.started[0]["command"]


def test_audit_log_distinguishes_planned_denied_approved_executed(tmp_path):
    data=_manifest(); data["operations"]["start"]={"command_template":"textgen.bat --listen"}; data["approval"]["start"]={"required":True}
    _write(tmp_path, data); rediscover(tmp_path); runner=_Runner()
    request("start","textgen",actor="alfred",approved_by="steward",root=tmp_path,dry_run=True)
    request("load_model","textgen",actor="alfred",root=tmp_path,model="../bad")
    request("start","textgen",actor="alfred",approved_by="steward",root=tmp_path,dry_run=False,runner=runner,health_checker=_Health(True))
    text=(tmp_path/"runtime/ai_services/audit_log.jsonl").read_text()
    assert "planned_dry_run" in text and "policy_denied" in text and "approval_granted" in text and "execution_succeeded" in text


def test_cloud_endpoint_and_alfred_boundary_remain_rejected():
    svc=_manifest(endpoint="https://api.example.com")
    assert evaluate("status", svc, actor="alfred")["allowed"] is False
    assert evaluate("delete", _manifest(), actor="alfred", approved_by="steward")["allowed"] is False


def test_process_started_but_health_fails_is_not_executed_and_state_not_running(tmp_path):
    data=_manifest(); data["operations"]["start"]={"command_template":"textgen.bat --listen"}; data["approval"]["start"]={"required":True}
    _write(tmp_path, data); rediscover(tmp_path); runner=_Runner(); health=_Health(False, "connection_refused")
    res=request("start","textgen",actor="alfred",approved_by="steward",root=tmp_path,dry_run=False,runner=runner,health_checker=health)
    assert res["result"] == "health_failed"
    assert res["execution"]["diagnostics"]["expected_endpoint"] == "http://127.0.0.1:5000/v1/models"
    state=json.loads((tmp_path/"runtime/ai_services/state.json").read_text())
    assert state["services"]["textgen"]["status"] == "health_failed"
    assert state["processes"]["textgen"]["health_error"] == "connection_refused"
    assert state["services"]["textgen"]["status"] != "running"


def test_audit_records_process_started_and_health_failed_separately(tmp_path):
    data=_manifest(); data["operations"]["start"]={"command_template":"textgen.bat --listen"}; data["approval"]["start"]={"required":True}
    _write(tmp_path, data); rediscover(tmp_path)
    request("start","textgen",actor="alfred",approved_by="steward",root=tmp_path,dry_run=False,runner=_Runner(),health_checker=_Health(False))
    events=[json.loads(line)["result"] for line in (tmp_path/"runtime/ai_services/audit_log.jsonl").read_text().splitlines()]
    assert "process_started" in events and "health_check_failed" in events and "execution_failed" in events
    assert "execution_succeeded" not in events[events.index("health_check_failed"):]


def test_health_success_records_health_before_execution_success(tmp_path):
    data=_manifest(); data["operations"]["start"]={"command_template":"textgen.bat --listen"}; data["approval"]["start"]={"required":True}
    _write(tmp_path, data); rediscover(tmp_path)
    res=request("start","textgen",actor="alfred",approved_by="steward",root=tmp_path,dry_run=False,runner=_Runner(),health_checker=_Health(True))
    assert res["result"] == "executed"
    events=[json.loads(line)["result"] for line in (tmp_path/"runtime/ai_services/audit_log.jsonl").read_text().splitlines()]
    assert events.index("health_check_succeeded") < events.index("execution_succeeded")
    state=json.loads((tmp_path/"runtime/ai_services/state.json").read_text())
    assert state["services"]["textgen"]["status"] == "running"


def test_quick_process_exit_before_health_is_reported(tmp_path):
    data=_manifest(); data["operations"]["start"]={"command_template":"textgen.bat --listen"}; data["approval"]["start"]={"required":True}
    _write(tmp_path, data); rediscover(tmp_path)
    res=request("start","textgen",actor="alfred",approved_by="steward",root=tmp_path,dry_run=False,runner=_Runner(alive=False),health_checker=_Health(False, "process_exited_before_health", "process_exited"))
    assert res["result"] == "health_failed"
    assert res["execution"]["lifecycle_state"] == "process_exited"
    text=(tmp_path/"runtime/ai_services/audit_log.jsonl").read_text()
    assert "process_exited_before_health" in text


def test_textgen_model_load_uses_models_health_endpoint(tmp_path):
    data=_manifest(); _write(tmp_path, data); rediscover(tmp_path); health=_Health(True)
    request("load_model","textgen",actor="alfred",approved_by="steward",root=tmp_path,model="Qwen3.gguf",dry_run=False,runner=_Runner(),health_checker=health)
    assert health.calls == ["http://127.0.0.1:5000/v1/models"]


class _InterruptingHealth:
    def __init__(self, exc):
        self.exc=exc; self.calls=[]
    def check(self, endpoint, timeout_seconds=30, interval_seconds=2, runner=None, pid=None):
        self.calls.append(endpoint)
        raise self.exc


def test_health_check_keyboard_interrupt_records_interrupted_state_and_json(tmp_path):
    data=_manifest(); data["operations"]["start"]={"command_template":"textgen.bat --listen"}; data["approval"]["start"]={"required":True}
    _write(tmp_path, data); rediscover(tmp_path); health=_InterruptingHealth(KeyboardInterrupt())
    res=request("start","textgen",actor="alfred",approved_by="steward",root=tmp_path,dry_run=False,runner=_Runner(),health_checker=health)
    assert res["result"] == "interrupted"
    assert res["approval_state"] == "interrupted"
    assert res["execution"]["lifecycle_state"] == "interrupted"
    assert res["execution"]["health"]["status"] == "interrupted"
    state=json.loads((tmp_path/"runtime/ai_services/state.json").read_text())
    assert state["services"]["textgen"]["status"] == "interrupted"
    assert state["services"]["textgen"]["status"] != "health_pending"
    assert state["processes"]["textgen"]["health_status"] == "interrupted"
    events=[json.loads(line)["result"] for line in (tmp_path/"runtime/ai_services/audit_log.jsonl").read_text().splitlines()]
    assert "health_check_interrupted" in events and "execution_interrupted" in events
    assert "execution_succeeded" not in events[events.index("health_check_interrupted"):]


def test_health_check_interrupted_error_records_interrupted_state(tmp_path):
    data=_manifest(); data["operations"]["start"]={"command_template":"textgen.bat --listen"}; data["approval"]["start"]={"required":True}
    _write(tmp_path, data); rediscover(tmp_path)
    res=request("start","textgen",actor="alfred",approved_by="steward",root=tmp_path,dry_run=False,runner=_Runner(),health_checker=_InterruptingHealth(InterruptedError("signal")))
    assert res["result"] == "interrupted"
    state=json.loads((tmp_path/"runtime/ai_services/state.json").read_text())
    assert state["services"]["textgen"]["status"] == "interrupted"
    assert state["processes"]["textgen"]["health_error"] == "InterruptedError"

def _textgen_batch_manifest():
    data=_manifest()
    data["paths"]["application"]="A:\\AI\\TextGen\\textgen-4.9"
    data["paths"]["launcher"]="A:\\AI\\TextGen\\textgen-4.9\\textgen.bat"
    data["operations"]["load_model"]={
        "command_type":"windows_batch",
        "working_directory":"A:\\AI\\TextGen\\textgen-4.9",
        "launcher":"textgen.bat",
        "arguments":["--nowebui","--listen","--model","{model}","--loader","llama.cpp"],
    }
    return data


def test_textgen_manifest_exposes_structured_windows_batch_launcher():
    manifest=json.loads(Path("runtime/ai_services/implementations/textgen/service.manifest.json").read_text())
    op=manifest["operations"]["load_model"]
    assert op["command_type"] == "windows_batch"
    assert op["working_directory"] == "A:\\AI\\TextGen\\textgen-4.9"
    assert op["launcher"] == "textgen.bat"
    assert op["arguments"] == ["--nowebui","--listen","--model","{model}","--loader","llama.cpp"]
    assert "command_template" not in op


def test_textgen_batch_dry_run_plans_cmd_batch_semantics(tmp_path):
    _write(tmp_path, _textgen_batch_manifest()); rediscover(tmp_path)
    plan=request("load_model","textgen",actor="alfred",approved_by="steward",root=tmp_path,model="Qwen3-8B-Q6_K.gguf")
    cmd=plan["planned_command"]
    assert cmd["command_type"] == "windows_batch"
    assert cmd["working_directory"] == "A:\\AI\\TextGen\\textgen-4.9"
    assert cmd["launcher"] == "textgen.bat"
    assert cmd["subprocess_args"] == ["cmd.exe","/d","/c","textgen.bat","--nowebui","--listen","--model","Qwen3-8B-Q6_K.gguf","--loader","llama.cpp"]
    assert "powershell" not in json.dumps(cmd).lower()


def test_textgen_batch_execution_passes_manifest_working_directory_and_safe_args(tmp_path):
    _write(tmp_path, _textgen_batch_manifest()); rediscover(tmp_path); runner=_Runner(); health=_Health(True)
    res=request("load_model","textgen",actor="alfred",approved_by="steward",root=tmp_path,model="Qwen3-8B-Q6_K.gguf",dry_run=False,runner=runner,health_checker=health)
    assert res["result"] == "executed"
    started=runner.started[0]
    assert started["cwd"] == "A:\\AI\\TextGen\\textgen-4.9"
    assert started["command"]["subprocess_args"] == ["cmd.exe","/d","/c","textgen.bat","--nowebui","--listen","--model","Qwen3-8B-Q6_K.gguf","--loader","llama.cpp"]
    assert health.calls == ["http://127.0.0.1:5000/v1/models"]


def test_textgen_batch_health_failure_remains_lifecycle_failure(tmp_path):
    _write(tmp_path, _textgen_batch_manifest()); rediscover(tmp_path)
    res=request("load_model","textgen",actor="alfred",approved_by="steward",root=tmp_path,model="Qwen3-8B-Q6_K.gguf",dry_run=False,runner=_Runner(),health_checker=_Health(False,"connection_refused"))
    assert res["result"] == "health_failed"
    state=json.loads((tmp_path/"runtime/ai_services/state.json").read_text())
    assert state["services"]["textgen"]["status"] == "health_failed"


def test_textgen_batch_model_validation_rejects_injection_characters(tmp_path):
    _write(tmp_path, _textgen_batch_manifest()); rediscover(tmp_path)
    for bad in ["../secret.gguf", "sub/model.gguf", "sub\\model.gguf", "x;calc.gguf", "x&calc.gguf", "x|calc.gguf", "x$(calc).gguf"]:
        res=request("load_model","textgen",actor="alfred",approved_by="steward",root=tmp_path,model=bad)
        assert res["policy"]["allowed"] is False

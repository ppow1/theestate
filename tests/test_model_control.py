import json
from pathlib import Path

from estate.model_control.discovery import rediscover_models, classify_capabilities
from estate.model_control.assignments import load_assignments, set_default, assign_actor
from estate.model_control.policy import evaluate_model_use
from estate.core.resident_interaction import process_chat
from estate.core.steward_command_center import generate_command_center, render_command_center_html


def seed_ai_services(tmp_path):
    p=tmp_path/'runtime/ai_services/registry.json'; p.parent.mkdir(parents=True)
    p.write_text(json.dumps({'version':'ai-services-registry-v1','services':[{'service_id':'ollama','display_name':'Ollama','service_type':'llm','default_endpoint':'http://127.0.0.1:11434','local_only':True,'models':[{'name':'qwen3:8b','size_bytes':1},{'name':'llama3.2-vision:11b','size_bytes':2}]}]}))
    (tmp_path/'runtime/ai_services/state.json').write_text(json.dumps({'services':{}}))


def test_model_discovery_registry_and_capabilities(tmp_path):
    seed_ai_services(tmp_path)
    reg=rediscover_models(tmp_path)
    ids={m['model_id'] for m in reg['models']}
    assert 'ollama:qwen3:8b' in ids
    assert 'ollama:llama3.2-vision:11b' in ids
    assert classify_capabilities('unknown-local-model') == ['text']
    assert 'vision' in classify_capabilities('llava:latest')


def test_assignments_policy_denials_and_audit(tmp_path):
    seed_ai_services(tmp_path); rediscover_models(tmp_path)
    set_default('text','ollama:qwen3:8b',root=tmp_path,approved_by='steward')
    assign_actor('alfred','text','ollama:qwen3:8b',root=tmp_path,approved_by='steward')
    assign_actor('chief_architect_5','code','ollama:qwen3:8b',root=tmp_path,approved_by='steward')
    data=load_assignments(tmp_path)
    assert data['estate_defaults']['preferred_text_model']=='ollama:qwen3:8b'
    assert data['residents']['alfred']['text']=='ollama:qwen3:8b'
    assert data['workers']['chief_architect_5']['code']=='ollama:qwen3:8b'
    assert evaluate_model_use('alfred','vision','ollama:qwen3:8b',root=tmp_path)['decision']=='denied'
    data['authority']['residents']['alfred']=['text']; (tmp_path/'runtime/model_control/assignments.json').write_text(json.dumps(data))
    assert 'actor_lacks_model_capability_authority' in evaluate_model_use('alfred','vision','ollama:llama3.2-vision:11b',root=tmp_path)['reasons']
    assert (tmp_path/'runtime/model_control/audit_log.jsonl').read_text()


def test_cli_office_and_alfred_model_control(tmp_path, monkeypatch, capsys):
    seed_ai_services(tmp_path); monkeypatch.chdir(tmp_path)
    from estate.cli.main import main
    main(['model-control','rediscover','--json']); out=capsys.readouterr().out; assert 'qwen3:8b' in out
    main(['model-control','set-default','--capability','text','--model','ollama:qwen3:8b','--approved-by','steward','--json'])
    main(['model-control','assign','--actor','alfred','--capability','text','--model','ollama:qwen3:8b','--approved-by','steward','--json'])
    main(['model-control','validate-assignments','--json']); assert 'allowed' in capsys.readouterr().out
    payload=generate_command_center(root=tmp_path, write=False)
    panel=json.dumps(payload['panels']['ai_services_models'])
    assert 'estate_model_control' in panel and 'ollama:qwen3:8b' in panel
    class Fake:
        provider='ollama'; endpoint='http://127.0.0.1:11434'; timeout=1
        def discover_models(self): return {'available':False,'provider':'ollama','endpoint':self.endpoint,'models':['qwen3:8b'],'discovery':'mock unavailable'}
    # process_chat uses real adapter for generation but records model-control selection in fallback metadata.
    res=process_chat('alfred','hello',root=tmp_path)
    assert res['turn']['llm']['assigned_model']=='ollama:qwen3:8b'
    assert res['turn']['llm']['selection_source']=='model_control_assignment'

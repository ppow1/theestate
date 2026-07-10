from estate.core.office_command_surface import ACTION_CONTROLS, VALID_OUTCOMES, controls_for_tab, execute_office_action


def test_payload_exposes_only_available_or_gated_controls():
    assert controls_for_tab('ai-services-models')
    for control in ACTION_CONTROLS:
        assert control['availability'] in {'available', 'gated'}
        if control['availability'] == 'available':
            assert control.get('handler')
        else:
            assert control.get('disabled_reason')


def test_blocked_actions_report_concrete_reason(tmp_path):
    result = execute_office_action('work_packages.validate_selected', root=tmp_path)
    assert result['outcome'] == 'blocked'
    assert 'Select a work package id' in result['steward_message']


def test_gated_controls_are_not_fake_operational(tmp_path):
    result = execute_office_action('ai_services.start_stop_load', root=tmp_path)
    assert result['outcome'] == 'blocked'
    assert 'approval workflow' in result['steward_message']


def test_refresh_assignment_queue_invokes_real_handler(tmp_path):
    (tmp_path / 'collaboration/work_packages/pending').mkdir(parents=True)
    (tmp_path / 'collaboration/work_packages/pending/WP-9999_SAMPLE.md').write_text('# Sample\n', encoding='utf-8')
    result = execute_office_action('work_packages.refresh_assignment_queue', root=tmp_path)
    assert result['outcome'] in VALID_OUTCOMES
    assert result['outcome'] == 'completed'
    assert 'runtime/work_packages/assignment_queue.json' in result['artifacts_written']
    assert (tmp_path / 'runtime/work_packages/assignment_queue.json').exists()


def test_refresh_notification_center_invokes_real_handler(tmp_path):
    result = execute_office_action('notifications.refresh_center', root=tmp_path)
    assert result['outcome'] == 'completed'
    assert result['artifacts_written']
    assert (tmp_path / 'runtime/notifications/operations_notification_center.json').exists()


def test_operational_activity_controls_write_evidence_and_validate_artifacts(tmp_path):
    evidence = tmp_path / 'runtime/example.json'
    evidence.parent.mkdir(parents=True)
    evidence.write_text('{"ok": true}', encoding='utf-8')

    refresh = execute_office_action('operational_activity.refresh', root=tmp_path)
    assert refresh['outcome'] == 'completed'
    assert (tmp_path / 'runtime/operations/status/office_operational_activity_payload.json').exists()

    ack = execute_office_action('operational_activity.acknowledge_attention', root=tmp_path, activity_id='act-1', acknowledged_by='Steward')
    assert ack['outcome'] == 'completed'
    assert (tmp_path / 'runtime/operations/status/attention_acknowledgements.json').exists()

    route = execute_office_action('operational_activity.route_to_workspace', root=tmp_path, activity_id='act-1', route_target='execution-control')
    assert route['outcome'] == 'completed'
    assert route['target_tab'] == 'execution-control'

    opened = execute_office_action('operational_activity.open_artifact', root=tmp_path, artifact_path='runtime/example.json')
    assert opened['outcome'] == 'completed'
    assert 'runtime/example.json' in opened['artifacts_read']

    filtered = execute_office_action('operational_activity.filter', root=tmp_path, state='Blocked', owner='Steward', priority='high', attention_required='true')
    assert filtered['outcome'] == 'completed'
    assert (tmp_path / 'runtime/operations/status/activity_filter.json').exists()
import json
from estate.core.office_command_surface import execute_office_action, controls_for_tab
from estate.core.global_search_command_palette import build_global_palette, search_global_palette, execute_registered_command
from estate.ai_services.discovery import rediscover

class Runner:
    def __init__(self): self.started=[]; self.stopped=[]
    def start(self, command, cwd=None, log_path=None): self.started.append(command); return {'pid': 1001, 'return_code': None}
    def stop(self, pid): self.stopped.append(pid); return {'stopped': True, 'pid': pid}
    def is_alive(self, pid): return True
    def return_code(self, pid): return None

class Health:
    def check(self, endpoint, **kwargs): return {'healthy': True, 'status': 'healthy', 'attempts': 1, 'pid_alive': True}

def manifest(root):
    d=root/'runtime/ai_services/implementations/open_webui'; d.mkdir(parents=True)
    (d/'service.manifest.json').write_text(json.dumps({'service_id':'open_webui','display_name':'Open WebUI','service_type':'local_interface','local_only':True,'host_policy':{'bind':'127.0.0.1','allow_public_bind':False},'default_endpoint':'http://127.0.0.1:8080','ports':[8080],'paths':{},'operations':{'status':{'api_template':'GET /'},'start':{'command_template':'python -m http.server 8080'},'stop':{'command_template':'stop'},'load_model':{'command_template':'load {model}'}},'approval':{'start':{'required':True},'stop':{'required':True},'load_model':{'required':True}}}))

def test_wp0520_ai_services_controls_use_canonical_handlers_and_block_unsupported(tmp_path):
    manifest(tmp_path); rediscover(tmp_path)
    runner=Runner(); health=Health()
    refresh=execute_office_action('ai_services.refresh_local_inventory', root=tmp_path)
    assert refresh['outcome']=='completed'
    start=execute_office_action('ai_services.start', root=tmp_path, service_id='open_webui', runner=runner, health_checker=health)
    assert start['outcome']=='completed'
    assert runner.started
    load=execute_office_action('ai_services.load_model', root=tmp_path, service_id='open_webui', model='qwen3.8b', runner=runner, health_checker=health)
    assert load['outcome']=='completed'
    unload=execute_office_action('ai_services.unload_model', root=tmp_path, service_id='open_webui', model='qwen3.8b')
    assert unload['outcome']=='blocked'
    inspect=execute_office_action('ai_services.inspect_state', root=tmp_path, service_id='open_webui')
    assert inspect['outcome']=='completed'
    route=execute_office_action('ai_services.launch_local_interface', root=tmp_path, service_id='open_webui')
    assert route['outcome']=='completed'
    assert (tmp_path/'runtime/ai_services/local_interface_routes.jsonl').exists()

def test_wp0520_search_and_palette_only_registered_safe_actions(tmp_path):
    (tmp_path/'collaboration/work_packages/pending').mkdir(parents=True)
    (tmp_path/'collaboration/work_packages/pending/WP-9999_Search_Target.md').write_text('# Search Target\nOffice artifact')
    palette=build_global_palette(tmp_path)
    assert any(c['id']=='ai_services.start' for c in palette['commands'])
    result=search_global_palette('Search Target', tmp_path, refresh=False)
    assert result['matches'][0]['action']['operation']=='open_artifact'
    assert result['matches'][0]['action']['target'].endswith('WP-9999_Search_Target.md')
    safe=execute_registered_command('ai_services.start')
    assert safe['ok'] and safe['operation']=='office_action'
    unsafe=execute_registered_command('shell.rm-rf')
    assert not unsafe['ok']

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

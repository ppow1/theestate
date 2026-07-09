from estate.core.operational_targets import OperationalTarget, default_validation_root

def test_target_registration_defaults_outside_repo():
    t=OperationalTarget('x','X','git_repository','Eng',capabilities=['git'],watch_state='enabled')
    d=t.to_dict()
    assert d['watch_enabled'] is True
    assert d['validation_root']==default_validation_root()
    assert 'theestate' not in d['validation_root'].lower()

def test_import_candidate_representation():
    t=OperationalTarget('cue-mastery','CueMastery','engineering_project','Engineering',watch_state='import_candidate')
    assert t.to_dict()['watch_enabled'] is False

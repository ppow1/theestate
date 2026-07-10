from estate.core.background_operations_extension_runtime import BackgroundOperationsExtensionRuntime
from estate.core.validation_reconciliation_runtime import write_path_audit

def test_background_extension_config_externalized(tmp_path):
    rt=BackgroundOperationsExtensionRuntime(tmp_path); rt.ensure_config()
    assert not (tmp_path/'config/background_operations/extensions.json').exists()
    assert 'runtime/background_operations/configuration/background_operations/extensions.json' in str(rt.config_path).replace('\\','/')

def test_write_path_audit_flags_checkout_config(tmp_path):
    audit=write_path_audit(tmp_path)
    assert audit['invalid_checkout_writes']==0

from estate.core.paths import ESTATE_ROOT
BASE = ESTATE_ROOT / "runtime" / "ai_services"
IMPLEMENTATIONS = BASE / "implementations"
REGISTRY = BASE / "registry.json"
STATE = BASE / "state.json"
AUDIT = BASE / "audit_log.jsonl"
REPORT_JSON = BASE / "WP-0131_ai_services_control_plane_report.json"
REPORT_MD = ESTATE_ROOT / "operations" / "ai_services" / "WP-0131_ai_services_control_plane_report.md"

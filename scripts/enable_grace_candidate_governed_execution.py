"""Enable the existing governed provider-effects gate for one candidate runtime."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", required=True)
    parser.add_argument("--candidate-root", required=True)
    args = parser.parse_args()
    runtime = args.runtime.rstrip("/")
    claims = {"iss": "estate-control", "sub": "ec219-engineering", "office": "Engineering", "authority_source": "EC-000219-candidate-readiness", "active": True}
    with urlopen(Request(runtime + "/v1/health", headers={"X-Estate-Claims": json.dumps(claims)}), timeout=10) as response:
        health = json.load(response)
    storage = str(health.get("storage", "")).replace("/", "\\").lower()
    expected = args.candidate_root.rstrip("\\/").replace("/", "\\").lower()
    if not storage.startswith(expected):
        raise SystemExit("candidate runtime storage is outside the requested candidate root")
    command = {"schema_version": "estate.grace-momentum-control.v1", "command_id": "ec219-provider-admit", "correlation_id": "ec219-readiness", "causation_id": "ec219-readiness", "idempotency_key": "ec219:provider:admit:comfyui", "timestamp": datetime.now(timezone.utc).isoformat(), "action": "provider.admit", "objective_id": "ec219-readiness", "adapter_id": "comfyui.local.image", "readiness_ref": "EC-000219-candidate-readiness", "locality": "loopback_http", "no_egress": True, "spend": False, "deterministic": True, "stop_capable": True, "rollback_capable": False}
    request = Request(runtime + "/v1/commands", data=json.dumps(command).encode(), headers={"Content-Type": "application/json", "X-Estate-Claims": json.dumps(claims)})
    with urlopen(request, timeout=10) as response:
        admission = json.load(response)
    observer = {**claims, "office": "Observer", "sub": "ec219-observer"}
    with urlopen(Request(runtime + "/v1/readiness", headers={"X-Estate-Claims": json.dumps(observer)}), timeout=10) as response:
        readiness = json.load(response)
    print(json.dumps({"health": health, "admission": admission, "readiness": readiness}, indent=2, sort_keys=True))
    return 0 if readiness.get("ready") is True and readiness.get("provider_effects_enabled") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())

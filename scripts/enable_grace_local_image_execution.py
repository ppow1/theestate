"""Admit the approved loopback ComfyUI adapter and verify production readiness."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", default="http://127.0.0.1:8766")
    args = parser.parse_args()
    claims = {"iss": "estate-control", "sub": "engineering-production", "office": "Engineering", "authority_source": "deployment/grace-local-image", "active": True}
    command = {"schema_version": "estate.grace-momentum-control.v1", "command_id": "deployment-admit-comfyui", "correlation_id": "deployment-admit-comfyui", "causation_id": "deployment-admit-comfyui", "idempotency_key": "deployment:admit:comfyui.local.image", "timestamp": datetime.now(timezone.utc).isoformat(), "action": "provider.admit", "objective_id": "grace-local-image-readiness", "adapter_id": "comfyui.local.image", "readiness_ref": "live-comfyui-loopback-8188", "locality": "loopback_http", "no_egress": True, "spend": False, "deterministic": True, "stop_capable": True, "rollback_capable": False}
    request = Request(args.runtime.rstrip("/") + "/v1/commands", data=json.dumps(command).encode(), headers={"Content-Type": "application/json", "X-Estate-Claims": json.dumps(claims)})
    with urlopen(request, timeout=10) as response:
        print(json.dumps(json.load(response), indent=2, sort_keys=True))
    readiness_request = Request(args.runtime.rstrip("/") + "/v1/readiness", headers={"X-Estate-Claims": json.dumps({**claims, "office": "Observer", "sub": "deployment-observer"})})
    with urlopen(readiness_request, timeout=10) as response:
        readiness = json.load(response)
    print(json.dumps(readiness, indent=2, sort_keys=True))
    if readiness.get("ready") is not True or readiness.get("provider_effects_enabled") is not True:
        raise SystemExit("Grace local image execution is not ready")


if __name__ == "__main__":
    main()

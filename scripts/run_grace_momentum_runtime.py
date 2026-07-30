"""Start the loopback Grace Momentum HTTP binding for local Open WebUI reads."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from estate.core.grace_momentum_service import GraceMomentumService, production_http_server


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="runtime/production/grace_momentum")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--mode", choices=("fixture", "shadow", "governed_local_test", "bounded_live", "disabled"), default=os.environ.get("ESTATE_GRACE_EXECUTION_MODE", "shadow"))
    args = parser.parse_args()
    service = GraceMomentumService(Path(args.root), mode=args.mode)
    server = production_http_server(service, args.host, args.port)
    print(f"Grace Momentum loopback runtime listening on http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

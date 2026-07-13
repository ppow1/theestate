#!/usr/bin/env python3
from estate.core.openwebui_resident_surface import run_validation
import json
print(json.dumps(run_validation(), indent=2, sort_keys=True))

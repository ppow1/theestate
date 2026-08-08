#!/usr/bin/env python3
"""Canonical compatibility entry point for living-diagnostics validation."""
import subprocess, sys
from pathlib import Path
raise SystemExit(subprocess.call([sys.executable,str(Path(__file__).with_name("estate_diagnostics.py")),"validate",*sys.argv[1:]]))

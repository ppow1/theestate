"""WP-4212 pending-definition matched runtime-canon recovery.

Conversation output is evidence, pending definitions are authority, and everything
rendered by this module is non-canonical review material.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from estate.core.conversation_archive_ingestion import _write_atomic, ingest

SCHEMA_VERSION = "estate.runtime-canon-recovery/v1"
GENERATOR_VERSION = "WP-4213/1.0"
GENERATED_AT = "1970-01-01T00:00:00Z"  # deliberately stable for reproducible evidence
NUMBERED = re.compile(r"\bWP[- _](\d{4})\b", re.I)
NAMED = re.compile(r"\b(?:(?:WP|CORE|OPS)-[A
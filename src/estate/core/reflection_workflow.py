from __future__ import annotations

import csv
import hashlib
import json
import shutil
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from estate.core.paths import ESTATE_ROOT

SCHEMA_VERSION = "estate-reflection-case-v1"
CASE_STATES = (
    "evaluation_requested
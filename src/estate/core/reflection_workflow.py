"""Durable lifecycle records for governed ChatGPT reflection workflows.

This module records deterministic workflow state and evidence. It does not assess
whether reflection is warranted, approve onboarding, confirm renewal, retire an
implementation, or create a conversation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from estate.core.paths import
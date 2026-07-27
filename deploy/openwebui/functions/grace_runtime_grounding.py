"""
title: Grace runtime grounding policy
id: grace_runtime_grounding
version: 1.0.0
description: Prevents ungrounded operational claims in the Grace model.
"""
from __future__ import annotations

import json
import re
from pydantic import BaseModel, Field


OPERATIONAL = re.compile(r"\b(objective|directive|readiness|availability|replay|checkpoint|dispatch|provider|reconciliation|validation|receipt|completion|blocker|responsible office|lawful action|schedule|operational state)\b", re.I)


class Valves(BaseModel):
    priority: int = Field(default=1)


class Filter:
    valves = Valves()

    def inlet(self, body: dict, __user__: dict | None = None) -> dict:
        messages = body.get("messages") if isinstance(body, dict) else None
        latest = ""
        if isinstance(messages, list):
            for message in reversed(messages):
                if isinstance(message, dict) and message.get("role") == "user":
                    content = message.get("content")
                    latest = content if isinstance(content, str) else json.dumps(content, sort_keys=True)
                    break
        metadata = body.setdefault("metadata", {}) if isinstance(body, dict) else {}
        if OPERATIONAL.search(latest):
            metadata["estate_runtime_grounding_required"] = True
            messages.append({"role": "system", "content": "Grounding policy: this is an operational-state request. You MUST invoke the registered Grace read-only runtime tool in this response cycle. Use only its returned payload. If its status is not AUTHORITATIVE_RESULT or NO_RECORD, state the exact failure status and do not invent IDs, checkpoints, schedules, office activity, handoffs, approvals, or lifecycle stages."})
        return body

    def outlet(self, body: dict, __user__: dict | None = None) -> dict:
        metadata = body.get("metadata", {}) if isinstance(body, dict) else {}
        if not metadata.get("estate_runtime_grounding_required"):
            return body
        messages = body.get("messages", []) if isinstance(body, dict) else []
        grounded = any(isinstance(message, dict) and message.get("role") == "tool" and any(status in str(message.get("content", "")) for status in ("AUTHORITATIVE_RESULT", "NO_RECORD", "RUNTIME_UNAVAILABLE", "OPERATION_UNAVAILABLE", "UNAUTHORIZED", "MALFORMED_RUNTIME_RESPONSE", "AMBIGUOUS_CORRELATION")) for message in messages)
        if not grounded:
            for message in reversed(messages):
                if isinstance(message, dict) and message.get("role") == "assistant":
                    message["content"] = "I cannot state operational runtime facts because no authoritative Grace runtime operation was completed in this response cycle."
                    break
        return body

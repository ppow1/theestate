"""
title: Grace runtime grounding policy
id: grace_runtime_grounding
version: 1.2.0
description: Prevents ungrounded operational claims while preserving direct conversation and execution routing.
"""
from __future__ import annotations

import json
import re
from pydantic import BaseModel, Field


OPERATIONAL = re.compile(
    r"\b(objective|directive|readiness|availability|replay|checkpoint|dispatch|provider|"
    r"reconciliation|validation|receipt|completion|blocker|responsible office|lawful action|"
    r"schedule|operational state)\b",
    re.I,
)

IMAGE_ACTION = re.compile(
    r"\b(generate|create|draw|render|make|produce|edit|modify|change|revise|redo|another)\b"
    r"[\s\S]{0,160}\b(image|picture|photo|photograph|portrait|headshot|visual|illustration|"
    r"tricycle|bicycle|bike)\b|"
    r"\b(image|picture|photo|photograph|portrait|headshot|visual|illustration)\b"
    r"[\s\S]{0,160}\b(generate|create|draw|render|make|produce|edit|modify|change|revise|redo)\b",
    re.I,
)

STATE_INSPECTION = re.compile(
    r"\b(what is|what's|show|return|report|check|inspect|status|state|was|has|did|last|current)\b"
    r"[\s\S]{0,120}\b(readiness|availability|objective|dispatch|provider|receipt|completion|"
    r"validation|operational state)\b",
    re.I,
)

# Informational and explanatory requests are conversation, not operational work orders.
# This includes questions about how Grace would approach a small task.  Grace should answer
# the substance directly and must not invent a ticket, handoff, dependency check, checkpoint,
# or future execution merely to demonstrate Estate governance.
DIRECT_INFORMATIONAL = re.compile(
    r"\b(how|what|why|explain|describe|show me|teach me|walk me through|approach)\b"
    r"[\s\S]{0,220}\b(code|program|javascript|python|html|css|sql|script|function|algorithm|"
    r"hello world|technical|software|computer)\b|"
    r"\b(code|program|javascript|python|html|css|sql|script|function|algorithm|hello world)\b"
    r"[\s\S]{0,220}\b(how|what|why|approach|example|explain|describe)\b",
    re.I,
)

RAW_OUTPUT = re.compile(r"\b(raw json|verbatim json|diagnostic output|full payload|full receipt)\b", re.I)


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
        if not isinstance(messages, list):
            return body

        image_action = bool(IMAGE_ACTION.search(latest))
        state_inspection = bool(STATE_INSPECTION.search(latest))
        if image_action and not state_inspection:
            metadata["estate_image_execution_request"] = True
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Image execution policy: this is an explicit image creation or revision request. "
                        "Treat the latest user message as the authoritative requested subject and changes. "
                        "Do not invoke the read-only Grace runtime bridge merely because the request mentions "
                        "an artifact, workflow, provider, validation, completion, dispatch, or receipt. Preserve "
                        "a named resident's approved visual canon when that resident is the subject; when the "
                        "user explicitly names a new subject or object, replace stale subject context completely. "
                        "After successful execution, answer conversationally with the result and artifact reference; "
                        "do not expose raw execution JSON unless the user explicitly requests diagnostic output."
                    ),
                }
            )
            return body

        if DIRECT_INFORMATIONAL.search(latest) and not state_inspection:
            metadata["estate_direct_conversation"] = True
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Direct-conversation policy: answer the Steward's actual informational or explanatory "
                        "question directly. A hypothetical or small technical question is not automatically an "
                        "Estate work order. Do not create or promise a Dispatch ticket, provider call, dependency "
                        "check, checkpoint, closure, archive action, or future execution unless the user explicitly "
                        "asks you to perform the work and an actual tool operation occurs in this response cycle. "
                        "For a coding question, give the practical approach and a small code example when useful. "
                        "Keep Grace's voice, but do not bury the answer under governance ceremony."
                    ),
                }
            )
            return body

        if OPERATIONAL.search(latest):
            metadata["estate_runtime_grounding_required"] = True
            raw_requested = bool(RAW_OUTPUT.search(latest))
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Grounding policy: this is an operational-state request. You MUST invoke the registered "
                        "Grace read-only runtime tool in this response cycle. Use only its returned payload. If its "
                        "status is not AUTHORITATIVE_RESULT or NO_RECORD, state the exact failure status and do not "
                        "invent IDs, checkpoints, schedules, office activity, handoffs, approvals, or lifecycle "
                        "stages. "
                        + (
                            "The user explicitly requested raw diagnostic output, so the authoritative payload may be returned verbatim."
                            if raw_requested
                            else "Present the verified result as a concise conversational answer. Do not dump the raw JSON payload."
                        )
                    ),
                }
            )
        return body

    def outlet(self, body: dict, __user__: dict | None = None) -> dict:
        metadata = body.get("metadata", {}) if isinstance(body, dict) else {}
        if not metadata.get("estate_runtime_grounding_required"):
            return body
        messages = body.get("messages", []) if isinstance(body, dict) else []
        grounded = any(
            isinstance(message, dict)
            and message.get("role") == "tool"
            and any(
                status in str(message.get("content", ""))
                for status in (
                    "AUTHORITATIVE_RESULT",
                    "NO_RECORD",
                    "RUNTIME_UNAVAILABLE",
                    "OPERATION_UNAVAILABLE",
                    "UNAUTHORIZED",
                    "MALFORMED_RUNTIME_RESPONSE",
                    "AMBIGUOUS_CORRELATION",
                )
            )
            for message in messages
        )
        if not grounded:
            for message in reversed(messages):
                if isinstance(message, dict) and message.get("role") == "assistant":
                    message["content"] = "I cannot state operational runtime facts because no authoritative Grace runtime operation was completed in this response cycle."
                    break
        return body

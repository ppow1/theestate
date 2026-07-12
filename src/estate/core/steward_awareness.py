"""Adaptive Steward awareness runtime.

The runtime learns lightweight, local-only interaction preferences from durable
observations and produces communication/support recommendations for residents
without automating Steward decisions or modifying authority boundaries.
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from estate.core.paths import ESTATE_ROOT

OBSERVATIONS_PATH = Path("runtime/steward/awareness/interaction_observations.jsonl")
PROFILE_PATH = Path("runtime/steward/awareness/working_style_profile.json")
COMMUNICATION_PATH = Path("runtime/steward/awareness/context_aware_communication.json")
ADAPTATION_PATH = Path("runtime/steward/awareness/interaction_adaptation.json")
SUPPORT_PATH = Path("runtime/steward/awareness/support_behavior.json")
REVIEW_PATH = Path("runtime/steward/awareness/relationship_review.json")


def _root(root=None):
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except json.JSONDecodeError:
        return default


def _write_json(root, rel, payload):
    path = _root(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _read_jsonl(path):
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def record_steward_interaction(observation, root=None):
    """Append a Steward interaction observation for future learning."""
    r = _root(root)
    path = r / OBSERVATIONS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": "steward_awareness_observation.v1", "recorded_at": _now(), **dict(observation or {})}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return {"recorded": True, "path": str(OBSERVATIONS_PATH), "observation": payload}


def _observations(root):
    return _read_jsonl(_root(root) / OBSERVATIONS_PATH)


def _counter_choice(counter, default):
    return counter.most_common(1)[0][0] if counter else default


def learn_working_style(root=None, write=True):
    """WP-4103: infer Steward working-style preferences from observations."""
    rows = _observations(root)
    formats = Counter(str(r.get("preferred_format")) for r in rows if r.get("preferred_format"))
    cadence = Counter(str(r.get("cadence")) for r in rows if r.get("cadence"))
    detail = Counter(str(r.get("detail_level")) for r in rows if r.get("detail_level"))
    channels = Counter(str(r.get("channel")) for r in rows if r.get("channel"))
    quiet = Counter(str(r.get("quiet_hours")) for r in rows if r.get("quiet_hours"))
    profile = {
        "schema_version": "steward_working_style_profile.v1",
        "generated_at": _now(),
        "observation_count": len(rows),
        "confidence": "learned" if len(rows) >= 3 else "seeded_defaults",
        "preferences": {
            "preferred_format": _counter_choice(formats, "concise_markdown_summary"),
            "cadence": _counter_choice(cadence, "batch_non_urgent_updates"),
            "detail_level": _counter_choice(detail, "summary_with_drill_down"),
            "channel": _counter_choice(channels, "office_command_center"),
            "quiet_hours": _counter_choice(quiet, "respect_when_known"),
        },
        "signals": {"formats": dict(formats), "cadence": dict(cadence), "detail_level": dict(detail), "channels": dict(channels)},
        "authority_boundaries": ["advisory_profile_only", "no_automatic_steward_decisions", "local_runtime_artifacts_only"],
    }
    if write:
        _write_json(root, PROFILE_PATH, profile)
    return profile


def build_context_aware_communication(context=None, root=None, write=True):
    """WP-4104: shape communication guidance using current context and learned style."""
    context = dict(context or {})
    profile = _read_json(_root(root) / PROFILE_PATH, learn_working_style(root, write=write))
    urgency = str(context.get("urgency") or "normal").lower()
    interruption = urgency in {"critical", "urgent", "blocking"} or bool(context.get("requires_decision"))
    guidance = {
        "schema_version": "steward_context_aware_communication.v1",
        "generated_at": _now(),
        "context": context,
        "recommended_mode": "immediate_recall" if interruption else "batched_briefing",
        "message_shape": {
            "format": profile.get("preferences", {}).get("preferred_format", "concise_markdown_summary"),
            "detail_level": "decision_ready" if interruption else profile.get("preferences", {}).get("detail_level", "summary_with_drill_down"),
            "include": ["why_it_matters", "requested_action", "deadline", "evidence_links"],
            "avoid": ["duplicative_updates", "unbounded_context_dump", "authority_ambiguity"],
        },
        "rationale": "Urgent or decision-bearing contexts may interrupt; routine contexts are batched according to learned Steward style.",
    }
    if write:
        _write_json(root, COMMUNICATION_PATH, guidance)
    return guidance


def adapt_interaction(surface="command_center", context=None, root=None, write=True):
    """WP-4105: adapt interaction behavior by surface and context."""
    comms = build_context_aware_communication(context, root, write=write)
    adaptation = {
        "schema_version": "steward_interaction_adaptation.v1",
        "generated_at": _now(),
        "surface": surface,
        "adaptations": {
            "command_center": ["pin_decision_items", "collapse_routine_updates", "show_evidence_drilldowns"],
            "resident_chat": ["start_with_bottom_line", "offer_next_actions", "preserve_conversation_context"],
            "notification": ["use_thresholds", "dedupe_by_decision_key", "include_acknowledgement_state"],
        }.get(surface, ["start_with_bottom_line", "include_evidence_links"]),
        "communication_mode": comms["recommended_mode"],
        "constraints": ["no_dark_patterns", "no_pressure_for_non_urgent_items", "Steward remains final decision authority"],
    }
    if write:
        _write_json(root, ADAPTATION_PATH, adaptation)
    return adaptation


def recommend_support_behavior(signals=None, root=None, write=True):
    """WP-4106: recommend supportive resident behavior from Steward signals."""
    signals = dict(signals or {})
    load = str(signals.get("steward_load") or "normal").lower()
    behaviors = ["summarize_state", "prepare_options", "surface_blockers_with_recommendation"]
    if load in {"high", "overloaded", "fatigued"}:
        behaviors.extend(["batch_routine_items", "reduce_nonessential_questions", "pre_fill_decision_context"])
    support = {
        "schema_version": "steward_support_behavior.v1",
        "generated_at": _now(),
        "signals": signals,
        "recommended_behaviors": behaviors,
        "resident_guidance": "Be helpful by reducing cognitive load while preserving Steward agency and explicit approval boundaries.",
        "prohibited_behaviors": ["making_steward_decisions", "concealing_uncertainty", "escalating_without_reason"],
    }
    if write:
        _write_json(root, SUPPORT_PATH, support)
    return support


def build_relationship_review(root=None, write=True):
    """WP-4107: produce a long-term relationship review for Steward interactions."""
    rows = _observations(root)
    by_resident = defaultdict(int)
    sentiments = Counter()
    for row in rows:
        by_resident[str(row.get("resident") or "unknown")] += 1
        if row.get("sentiment"):
            sentiments[str(row["sentiment"])] += 1
    review = {
        "schema_version": "steward_relationship_review.v1",
        "generated_at": _now(),
        "review_period": "all_available_observations",
        "observation_count": len(rows),
        "resident_interaction_counts": dict(sorted(by_resident.items())),
        "relationship_health": "needs_more_signal" if len(rows) < 3 else ("stable" if sentiments.get("negative", 0) == 0 else "review_recommended"),
        "themes": ["clarity", "trust", "continuity", "respect_for_attention"],
        "recommendations": ["continue collecting explicit preference observations", "review support behavior monthly", "keep all adaptation advisory and reversible"],
        "authority_boundaries": ["review_is_advisory", "does_not_score_the_steward", "does_not_override_existing_governance"],
    }
    if write:
        _write_json(root, REVIEW_PATH, review)
    return review


def generate_steward_awareness_runtime(root=None, context=None, signals=None, surface="command_center", write=True):
    profile = learn_working_style(root, write=write)
    communication = build_context_aware_communication(context, root, write=write)
    adaptation = adapt_interaction(surface, context, root, write=write)
    support = recommend_support_behavior(signals, root, write=write)
    review = build_relationship_review(root, write=write)
    return {
        "available": True,
        "path": "; ".join(str(p) for p in [PROFILE_PATH, COMMUNICATION_PATH, ADAPTATION_PATH, SUPPORT_PATH, REVIEW_PATH]),
        "kind": "steward_awareness_runtime",
        "data": {"profile": profile, "communication": communication, "adaptation": adaptation, "support": support, "relationship_review": review},
    }

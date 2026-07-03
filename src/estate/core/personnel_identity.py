"""Conservative registry-backed personnel identity and mailbox resolver.

The resolver only reports destinations supported by Estate registry data or by
existing worker-routing names. Unknown and ambiguous inputs return warnings
instead of fabricated mailbox or personnel identities.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from estate.core.collaboration_ops import DEFAULT_QUEUE, DEFAULT_WORKER_RULES
from estate.core.mailbox_index import (
    _slug,
    functional_by_mailbox_id,
    load_functional_mailbox_registry,
    load_personnel_registry,
    mailbox_directory_name,
    personnel_by_employee_id,
    personnel_by_mailbox_id,
    registry_paths,
)
from estate.core.paths import ESTATE_ROOT


ALFRED_QUEUE_DISPLAY_NAME = "Alfred Routing Intake"
ALFRED_QUEUE_ALIASES = {"alfred.queue", "alfred.routing"}
WORKER_ALIASES = {
    "alfred.review": "worker.alfred_review",
}


def _root(root=None):
    if root:
        return Path(root)
    return ESTATE_ROOT if (ESTATE_ROOT / "README.md").exists() else Path.cwd()


def _read_json_list(path):
    if not path.exists():
        return []
    entries = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError(f"{path} must contain a JSON list")
    return entries


def load_residents_registry(root=None):
    return _read_json_list(registry_paths(root)["residents"])


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _result(actor, normalized_actor, destination_type=None, canonical_destination=None, employee=None, mailbox=None, resident=None, worker=None, warnings=None):
    warnings = [warning for warning in (warnings or []) if warning]
    return {
        "actor": actor,
        "normalized_actor": normalized_actor,
        "resolved": canonical_destination is not None,
        "destination_type": destination_type,
        "canonical_destination": canonical_destination,
        "employee_id": employee.get("employee_id") if employee else None,
        "mailbox_id": mailbox.get("mailbox_id") if mailbox else (employee.get("mailbox_id") if employee else None),
        "resident_id": resident.get("id") if resident else (employee.get("resident_id") if employee else None),
        "worker": worker,
        "display_name": (employee or mailbox or resident or {}).get("display_name") or (resident or {}).get("name") or worker,
        "warnings": warnings,
    }


def _mailbox_result(actor, normalized, mailbox, employee=None, resident=None, warnings=None):
    return _result(
        actor,
        normalized,
        destination_type="mailbox",
        canonical_destination=f"mailbox.{int(mailbox['mailbox_id'])}",
        employee=employee,
        mailbox=mailbox,
        resident=resident,
        warnings=warnings,
    )


def _employee_result(actor, normalized, employee, resident=None, warnings=None):
    mailbox_id = employee.get("mailbox_id")
    if mailbox_id is None:
        return _result(actor, normalized, employee=employee, resident=resident, warnings=[*(warnings or []), "employee has no mailbox_id in personnel registry"])
    return _result(
        actor,
        normalized,
        destination_type="personnel",
        canonical_destination=f"mailbox.{int(mailbox_id)}",
        employee=employee,
        mailbox={"mailbox_id": int(mailbox_id), "display_name": employee.get("display_name")},
        resident=resident,
        warnings=warnings,
    )


def _known_workers():
    workers = {DEFAULT_QUEUE, "worker.audit", "worker.implementation"}
    workers.update(rule.get("worker") for rule in DEFAULT_WORKER_RULES if rule.get("worker"))
    workers.update(WORKER_ALIASES)
    workers.update(WORKER_ALIASES.values())
    return {worker for worker in workers if worker}


def _resident_by_slug(residents):
    aliases = {}
    for resident in residents:
        name_slug = _slug(resident.get("name"))
        if name_slug:
            aliases.setdefault(name_slug, resident)
            aliases.setdefault(f"resident.{name_slug}", resident)
    return aliases


def _find_alfred_mailbox(mailboxes):
    for mailbox in mailboxes:
        if mailbox.get("display_name") == ALFRED_QUEUE_DISPLAY_NAME:
            return mailbox
    return None


def resolve_personnel_identity(actor, root=None):
    base = _root(root)
    personnel = load_personnel_registry(base)
    mailboxes = load_functional_mailbox_registry(base)
    residents = load_residents_registry(base)
    by_employee = personnel_by_employee_id(personnel)
    by_personnel_mailbox = personnel_by_mailbox_id(personnel)
    by_functional_mailbox = functional_by_mailbox_id(mailboxes)
    resident_aliases = _resident_by_slug(residents)
    normalized = str(actor or "").strip().lower()

    if not normalized:
        return _result(actor, normalized, warnings=["empty actor"])

    if normalized.startswith("employee."):
        value = normalized.removeprefix("employee.")
        try:
            employee_id = int(value)
        except ValueError:
            matches = [entry for entry in personnel if value in {_slug(entry.get("display_name")), _slug(entry.get("current_title"))}]
            if len(matches) == 1:
                return _employee_result(actor, normalized, matches[0], resident_aliases.get(_slug(matches[0].get("display_name"))))
            if len(matches) > 1:
                return _result(actor, normalized, warnings=[f"ambiguous employee alias: {actor}"])
            return _result(actor, normalized, warnings=[f"unresolved employee: {actor}"])
        employee = by_employee.get(employee_id)
        if not employee:
            return _result(actor, normalized, warnings=[f"employee_id {employee_id} is not in personnel registry"])
        return _employee_result(actor, normalized, employee, resident_aliases.get(_slug(employee.get("display_name"))))

    if normalized in ALFRED_QUEUE_ALIASES:
        alfred_mailbox = _find_alfred_mailbox(mailboxes)
        if alfred_mailbox:
            return _mailbox_result(actor, normalized, alfred_mailbox)
        return _result(actor, normalized, warnings=["Alfred Routing Intake mailbox is missing"])

    if normalized.startswith("mailbox."):
        value = normalized.removeprefix("mailbox.")
        try:
            mailbox_id = int(value)
        except ValueError:
            matches = [entry for entry in mailboxes if value in {_slug(entry.get("display_name")), _slug(entry.get("owning_office"))}]
            if len(matches) == 1:
                responsible = matches[0].get("responsible_employee_id")
                return _mailbox_result(actor, normalized, matches[0], by_employee.get(int(responsible)) if responsible is not None else None)
            if len(matches) > 1:
                return _result(actor, normalized, warnings=[f"ambiguous mailbox alias: {actor}"])
            return _result(actor, normalized, warnings=[f"unresolved mailbox: {actor}"])
        mailbox = by_functional_mailbox.get(mailbox_id)
        employee = by_personnel_mailbox.get(mailbox_id)
        if mailbox:
            responsible = mailbox.get("responsible_employee_id")
            return _mailbox_result(actor, normalized, mailbox, by_employee.get(int(responsible)) if responsible is not None else None)
        if employee:
            return _employee_result(actor, normalized, employee, resident_aliases.get(_slug(employee.get("display_name"))))
        return _result(actor, normalized, warnings=[f"mailbox_id {mailbox_id} is not in mailbox registries"])

    if normalized.startswith("office."):
        value = normalized.removeprefix("office.")
        matches = [entry for entry in personnel if value in {_slug(entry.get("display_name")), _slug(entry.get("current_title"))}]
        if len(matches) == 1:
            return _employee_result(actor, normalized, matches[0], resident_aliases.get(_slug(matches[0].get("display_name"))))
        office_matches = [entry for entry in mailboxes if entry.get("mailbox_type") == "office" and value in {_slug(entry.get("display_name")), _slug(entry.get("owning_office"))}]
        if len(office_matches) == 1:
            responsible = office_matches[0].get("responsible_employee_id")
            return _mailbox_result(actor, normalized, office_matches[0], by_employee.get(int(responsible)) if responsible is not None else None)
        if len(matches) + len(office_matches) > 1:
            return _result(actor, normalized, warnings=[f"ambiguous office alias: {actor}"])
        return _result(actor, normalized, warnings=[f"unresolved office: {actor}"])

    if normalized in _known_workers() or normalized.startswith("worker."):
        canonical = WORKER_ALIASES.get(normalized, normalized)
        warnings = [] if normalized in _known_workers() else [f"worker is not in known routing rules: {actor}"]
        return _result(actor, normalized, destination_type="worker", canonical_destination=canonical, worker=canonical, warnings=warnings)

    if normalized in resident_aliases:
        resident = resident_aliases[normalized]
        linked = [entry for entry in personnel if entry.get("resident_id") == resident.get("id") or _slug(entry.get("display_name")) == _slug(resident.get("name"))]
        if len(linked) == 1:
            return _employee_result(actor, normalized, linked[0], resident)
        if len(linked) > 1:
            return _result(actor, normalized, resident=resident, warnings=[f"ambiguous resident/personnel mapping: {actor}"])
        return _result(actor, normalized, resident=resident, warnings=[f"resident has no personnel mailbox mapping: {actor}"])

    return _result(actor, normalized, warnings=[f"unresolved actor: {actor}"])


def format_resolution(resolution):
    lines = ["Estate Personnel Identity Resolver", f"Actor: {resolution.get('actor')}"]
    lines.append(f"Resolved: {resolution.get('resolved')}")
    lines.append(f"Canonical destination: {resolution.get('canonical_destination') or 'unresolved'}")
    lines.append(f"Destination type: {resolution.get('destination_type') or 'unresolved'}")
    if resolution.get("employee_id") is not None:
        lines.append(f"Employee ID: {resolution['employee_id']}")
    if resolution.get("mailbox_id") is not None:
        lines.append(f"Mailbox ID: {mailbox_directory_name(resolution['mailbox_id'])}")
    if resolution.get("resident_id"):
        lines.append(f"Resident ID: {resolution['resident_id']}")
    if resolution.get("worker"):
        lines.append(f"Worker: {resolution['worker']}")
    for warning in resolution.get("warnings", []):
        lines.append(f"Warning: {warning}")
    return "\n".join(lines)


def resolver_metadata(root=None):
    paths = registry_paths(_root(root))
    return {
        "generated_at": _now(),
        "registry_sources": [
            str(paths["personnel"].relative_to(_root(root))).replace("\\", "/"),
            str(paths["mailboxes"].relative_to(_root(root))).replace("\\", "/"),
            str(paths["residents"].relative_to(_root(root))).replace("\\", "/"),
        ],
        "known_workers": sorted(_known_workers()),
    }

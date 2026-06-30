from estate.core.paths import RESIDENTS_DIR
from estate.core.ids import next_number, make_id
from estate.core.registry import load_registry, add_registry_object, write_object_file
from estate.core.ledger import create_change
from estate.core.time import now

def next_resident_id():
    items = load_registry("residents")
    text = "\n".join([item.get("id", "") for item in items])
    return make_id("RES", next_number("RES", text))

def register_resident(name, department, office, role, classification="Estate Internal"):
    RESIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    resident_id = next_resident_id()
    safe = name.lower().replace(" ", "_")

    obj = {
        "id": resident_id,
        "type": "resident",
        "name": name,
        "department": department,
        "office": office,
        "status": "Active",
        "classification": classification,
        "created": now(),
        "role": role,
        "canonical": f"estate://residents/{resident_id.lower()}",
        "palace": f"Estate / Residents / {name}"
    }

    add_registry_object("residents", obj)
    write_object_file(resident_id, obj)

    markdown = f"""# {name}

ID: {resident_id}
Name: {name}
Department: {department}
Office: {office}
Status: Active
Classification: {classification}
Created: {obj["created"]}
Canonical: {obj["canonical"]}
Palace: {obj["palace"]}

## Role

{role}

## Notes

Registered by Estate Core.
"""
    (RESIDENTS_DIR / f"{safe}.md").write_text(markdown, encoding="utf-8")

    ec_id = create_change(
        title=f"Registered Resident {name}",
        summary=f"Created resident record {resident_id} for {name}, serving as {office} in {department}."
    )

    return resident_id, ec_id

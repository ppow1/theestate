from pathlib import Path
from datetime import datetime

ROOT = Path(r"A:\theestate")

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def next_ec_id():
    ledger = ROOT / "estate_ledger" / "ledger.md"
    text = ledger.read_text(encoding="utf-8") if ledger.exists() else ""
    nums = []
    for line in text.splitlines():
        if line.startswith("## EC-"):
            try:
                nums.append(int(line.split("-")[1].split()[0]))
            except Exception:
                pass
    return f"EC-{(max(nums) + 1 if nums else 1):06d}"

def add_change(title, summary, status="Draft", classification="Estate Internal"):
    ec_id = next_ec_id()
    entry = f'''

## {ec_id} - {title}

Timestamp: {now()}
Location: A:\\theestate
Status: {status}
Classification: {classification}

Summary:
{summary}
'''
    ledger = ROOT / "estate_ledger" / "ledger.md"
    with ledger.open("a", encoding="utf-8") as f:
        f.write(entry)

    devlog = ROOT / "development" / "devlog.md"
    with devlog.open("a", encoding="utf-8") as f:
        f.write(f"\\n## {now()}\\n\\n{ec_id} - {title}\\n{summary}\\n")

    print(f"Created {ec_id}: {title}")

def create_resident(name, department, office, role, classification="Estate Internal"):
    safe = name.lower().replace(" ", "_")
    path = ROOT / "residents" / f"{safe}.md"

    content = f'''# {name}

ID: RES-TBD
Name: {name}
Department: {department}
Office: {office}
Status: Active
Classification: {classification}
Created: {now()}

## Role

{role}

## Notes

Pending full charter.
'''
    path.write_text(content, encoding="utf-8")

    add_change(
        title=f"Registered Resident {name}",
        summary=f"Created resident record for {name}, serving as {office} in {department}."
    )

def main():
    print("Estate Builder v0.1")
    print("1. New Estate Change")
    print("2. Register Resident")
    choice = input("Select: ").strip()

    if choice == "1":
        title = input("Title: ").strip()
        summary = input("Summary: ").strip()
        add_change(title, summary)

    elif choice == "2":
        name = input("Resident name: ").strip()
        department = input("Department: ").strip()
        office = input("Office: ").strip()
        role = input("Role: ").strip()
        create_resident(name, department, office, role)

    else:
        print("No action.")

if __name__ == "__main__":
    main()

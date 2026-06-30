from estate.core.paths import LEDGER_PATH, DEVLOG_PATH
from estate.core.ids import next_number, make_id
from estate.core.time import now

def _read(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""

def _append(path, text):
    with path.open("a", encoding="utf-8") as f:
        f.write(text)

def next_ec_id():
    text = _read(LEDGER_PATH)
    return make_id("EC", next_number("EC", text))

def create_change(title, summary, status="Draft", classification="Estate Internal", location=r"A:\theestate"):
    ec_id = next_ec_id()
    timestamp = now()

    ledger_entry = f"""

## {ec_id} - {title}

Timestamp: {timestamp}
Location: {location}
Status: {status}
Classification: {classification}

Summary:
{summary}
"""
    _append(LEDGER_PATH, ledger_entry)

    devlog_entry = f"""

## {timestamp}

{ec_id} - {title}

{summary}
"""
    _append(DEVLOG_PATH, devlog_entry)

    return ec_id

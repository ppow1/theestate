import json
import re
import subprocess
from pathlib import Path
from estate.core.paths import ESTATE_ROOT, LEDGER_PATH, DEVLOG_PATH

def _run(cmd):
    try:
        result = subprocess.run(cmd, cwd=str(ESTATE_ROOT), capture_output=True, text=True, shell=True)
        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }
    except Exception as e:
        return {
            "ok": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e)
        }

def _latest_ec_from_text(text):
    matches = re.findall(r"EC-\d{6}", text)
    return matches[-1] if matches else None

def _latest_git_ec():
    result = _run("git log -1 --pretty=%s")
    if not result["ok"]:
        return None, result
    return _latest_ec_from_text(result["stdout"]), result

def _latest_ledger_ec():
    text = LEDGER_PATH.read_text(encoding="utf-8") if LEDGER_PATH.exists() else ""
    return _latest_ec_from_text(text)

def _json_ok(path):
    try:
        json.loads(Path(path).read_text(encoding="utf-8"))
        return True, ""
    except Exception as e:
        return False, str(e)


def _required_paths_check():
    required = [
        "data/registry/residents.json",
        "data/registry/services.json",
        "data/registry/capabilities.json",
        "data/registry/providers.json",
        "observations/ai_environment_latest.json",
        "estate_ledger/ledger.md",
        "development/devlog.md",
        "estate.bat",
    ]
    missing = [path for path in required if not (ESTATE_ROOT / path).exists()]
    return {
        "name": "estate:required_paths",
        "ok": not missing,
        "detail": f"{len(required)} present" if not missing else ", ".join(missing),
    }

def _registry_shape_check(path, collection_key):
    full_path = ESTATE_ROOT / path
    try:
        data = json.loads(full_path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"name": f"registry_shape:{path}", "ok": False, "detail": str(e)}

    if isinstance(data, list):
        items = data
        shape = "list"
    elif isinstance(data, dict):
        if collection_key in data:
            items = data[collection_key]
            shape = f"object.{collection_key}"
        elif "items" in data:
            items = data["items"]
            shape = "object.items"
        else:
            return {
                "name": f"registry_shape:{path}",
                "ok": False,
                "detail": f"object missing {collection_key} or items collection",
            }
    else:
        return {"name": f"registry_shape:{path}", "ok": False, "detail": "registry root is not a list or object"}

    if not isinstance(items, list):
        return {"name": f"registry_shape:{path}", "ok": False, "detail": "registry collection is not a list"}

    seen = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            return {"name": f"registry_shape:{path}", "ok": False, "detail": f"item[{index}] is not an object"}
        item_id = item.get("id")
        if not item_id:
            return {"name": f"registry_shape:{path}", "ok": False, "detail": f"item[{index}] missing id"}
        if item_id in seen:
            return {"name": f"registry_shape:{path}", "ok": False, "detail": f"duplicate id: {item_id}"}
        seen.add(item_id)

    return {"name": f"registry_shape:{path}", "ok": True, "detail": f"{len(items)} records ({shape})"}


def _observation_history_check():
    observations = ESTATE_ROOT / "observations"
    latest = observations / "ai_environment_latest.json"
    history = [
        path for path in observations.glob("ai_environment_*.json")
        if not path.name.endswith("_latest.json")
    ]
    if not latest.exists():
        return {"name": "observations:latest_present", "ok": False, "detail": "missing latest observation"}
    if not history:
        return {"name": "observations:history_present", "ok": False, "detail": "no timestamped observation history"}
    return {"name": "observations:history_present", "ok": True, "detail": f"{len(history)} historical observations"}

def _latest_ledger_ec_in_devlog_check():
    ledger = LEDGER_PATH.read_text(encoding="utf-8", errors="replace") if LEDGER_PATH.exists() else ""
    devlog = DEVLOG_PATH.read_text(encoding="utf-8", errors="replace") if DEVLOG_PATH.exists() else ""
    latest = _latest_ec_from_text(ledger)
    if not latest:
        return {"name": "history:latest_ledger_ec_in_devlog", "ok": False, "detail": "no Estate Change found in ledger"}
    return {
        "name": "history:latest_ledger_ec_in_devlog",
        "ok": latest in devlog,
        "detail": latest if latest in devlog else f"{latest} missing from devlog",
    }


def _syntax_checks():
    checks = []
    py_files = [
        "src/estate/cli/main.py",
        "src/estate/core/discovery.py",
        "src/estate/core/provider_sync.py",
    ]

    for file in py_files:
        result = _run(f"python -m py_compile {file}")
        checks.append({
            "name": f"syntax:{file}",
            "ok": result["ok"],
            "detail": result["stderr"] or result["stdout"],
        })

    return checks


def _runtime_checks():
    checks = []
    for command in [".\\estate.bat status", ".\\estate.bat discovery-report"]:
        result = _run(command)
        detail = result["stderr"] or result["stdout"].splitlines()[0] if result["stdout"] else ""
        checks.append({
            "name": f"runtime:{command}",
            "ok": result["ok"],
            "detail": detail,
        })

    checks.append(_cli_inventory_check())

    return checks



def _cli_inventory_check():
    result = _run(".\\estate.bat --help")
    required = [
        "status",
        "list",
        "services",
        "capabilities",
        "providers",
        "discover-ai",
        "discovery-report",
        "sync-ollama",
        "audit",
    ]

    if not result["ok"]:
        return {
            "name": "runtime:cli_inventory",
            "ok": False,
            "detail": result["stderr"] or result["stdout"],
        }

    missing = [command for command in required if command not in result["stdout"]]
    return {
        "name": "runtime:cli_inventory",
        "ok": not missing,
        "detail": f"{len(required)} commands present" if not missing else "missing: " + ", ".join(missing),
    }


def _json_checks():
    checks = []
    for path in [
        "data/registry/residents.json",
        "data/registry/services.json",
        "data/registry/capabilities.json",
        "data/registry/providers.json",
        "observations/ai_environment_latest.json",
    ]:
        ok, detail = _json_ok(ESTATE_ROOT / path)
        checks.append({
            "name": f"json:{path}",
            "ok": ok,
            "detail": detail,
        })

    return checks


def _registry_checks():
    checks = [_required_paths_check()]

    for path, collection_key in [
        ("data/registry/residents.json", "residents"),
        ("data/registry/services.json", "services"),
        ("data/registry/capabilities.json", "capabilities"),
        ("data/registry/providers.json", "providers"),
    ]:
        checks.append(_registry_shape_check(path, collection_key))

    return checks


def _observation_checks():
    return [
        _observation_history_check(),
    ]


def _history_checks():
    git_ec, git_result = _latest_git_ec()
    ledger_ec = _latest_ledger_ec()

    return [
        _latest_ledger_ec_in_devlog_check(),
        {
            "name": "history:latest_git_ec_matches_latest_ledger_ec",
            "ok": git_ec == ledger_ec,
            "detail": f"git={git_ec} ledger={ledger_ec}",
        },
    ]


def _git_checks():
    git_status = _run("git status --porcelain")
    return [
        {
            "name": "git:working_tree_clean",
            "ok": git_status["ok"] and git_status["stdout"] == "",
            "detail": git_status["stdout"],
        }
    ]


def run_audit():
    checks = []
    checks.extend(_syntax_checks())
    checks.extend(_runtime_checks())
    checks.extend(_json_checks())
    checks.extend(_registry_checks())
    checks.extend(_observation_checks())
    checks.extend(_history_checks())
    checks.extend(_git_checks())

    passed = sum(1 for check in checks if check["ok"])
    failed = len(checks) - passed

    return {
        "passed": passed,
        "failed": failed,
        "checks": checks,
    }


def _check_group(name):
    if ":" in name:
        return name.split(":", 1)[0]
    return "estate"


def print_audit_report():
    report = run_audit()
    print("=========================================")
    print("Estate Audit Report")
    print("=========================================")
    print(f"Passed: {report['passed']}")
    print(f"Failed: {report['failed']}")
    print("")

    current_group = None
    for check in report["checks"]:
        group = _check_group(check["name"])
        if group != current_group:
            current_group = group
            print(f"[{current_group}]")

        mark = "PASS" if check["ok"] else "FAIL"
        print(f"{mark} | {check['name']}")
        if check["detail"]:
            print(f"     {check['detail']}")

    return report

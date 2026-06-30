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

def run_audit():
    checks = []

    py_files = [
        "src/estate/cli/main.py",
        "src/estate/core/discovery.py",
        "src/estate/core/provider_sync.py"
    ]

    for file in py_files:
        result = _run(f"python -m py_compile {file}")
        checks.append({
            "name": f"syntax:{file}",
            "ok": result["ok"],
            "detail": result["stderr"] or result["stdout"]
        })

    for command in [".\\estate.bat status", ".\\estate.bat discovery-report"]:
        result = _run(command)
        checks.append({
            "name": f"runtime:{command}",
            "ok": result["ok"],
            "detail": result["stderr"] or result["stdout"].splitlines()[0] if result["stdout"] else ""
        })

    for path in [
        "data/registry/residents.json",
        "data/registry/services.json",
        "data/registry/capabilities.json",
        "data/registry/providers.json",
        "observations/ai_environment_latest.json"
    ]:
        ok, detail = _json_ok(ESTATE_ROOT / path)
        checks.append({
            "name": f"json:{path}",
            "ok": ok,
            "detail": detail
        })

    git_status = _run("git status --porcelain")
    checks.append({
        "name": "git:working_tree_clean",
        "ok": git_status["ok"] and git_status["stdout"] == "",
        "detail": git_status["stdout"]
    })

    git_ec, git_result = _latest_git_ec()
    ledger_ec = _latest_ledger_ec()
    checks.append({
        "name": "history:latest_git_ec_matches_latest_ledger_ec",
        "ok": git_ec == ledger_ec,
        "detail": f"git={git_ec} ledger={ledger_ec}"
    })

    passed = sum(1 for check in checks if check["ok"])
    failed = len(checks) - passed

    return {
        "passed": passed,
        "failed": failed,
        "checks": checks
    }

def print_audit_report():
    report = run_audit()
    print("=========================================")
    print("Estate Audit Report")
    print("=========================================")
    print(f"Passed: {report['passed']}")
    print(f"Failed: {report['failed']}")
    print("")
    for check in report["checks"]:
        mark = "PASS" if check["ok"] else "FAIL"
        print(f"{mark} | {check['name']}")
        if check["detail"]:
            print(f"     {check['detail']}")
    return report

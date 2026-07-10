from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Sequence
from estate.core.historian import create_event, correct_event, generate_timeline, historical_query, inspect_source, summarize

def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding='utf-8'))

def run(argv: Sequence[str] | None = None) -> dict:
    p = argparse.ArgumentParser(prog='estate-historian')
    p.add_argument('--root'); p.add_argument('--json', action='store_true')
    sub = p.add_subparsers(dest='action', required=True)
    q=sub.add_parser('event-create'); q.add_argument('--file', required=True)
    q=sub.add_parser('event-correct'); q.add_argument('--event-id', required=True); q.add_argument('--file', required=True); q.add_argument('--reason', required=True)
    q=sub.add_parser('timeline');
    for f in ('date','office','project','resident','artifact_type','significance'): q.add_argument(f'--{f.replace("_","-")}')
    q=sub.add_parser('source-inspect'); q.add_argument('--path', required=True)
    q=sub.add_parser('query'); q.add_argument('query'); q.add_argument('--office'); q.add_argument('--project'); q.add_argument('--resident'); q.add_argument('--artifact-type'); q.add_argument('--significance'); q.add_argument('--summary', action='store_true')
    a=p.parse_args(argv); root=Path(a.root).resolve() if a.root else None
    if a.action == 'event-create':
        payload=_load(a.file); result={'kind':'event_created','event':create_event(root=root, **payload)}
    elif a.action == 'event-correct':
        result={'kind':'event_corrected','event':correct_event(a.event_id, _load(a.file), a.reason, root=root)}
    elif a.action == 'timeline':
        result={'kind':'timeline','timeline':generate_timeline(root=root, date=a.date, office=a.office, project=a.project, resident=a.resident, artifact_type=a.artifact_type, significance=a.significance)}
    elif a.action == 'source-inspect':
        result={'kind':'source','source':inspect_source(a.path, root=root)}
    elif a.action == 'query':
        result=historical_query(a.query, root=root, office=a.office, project=a.project, resident=a.resident, artifact_type=a.artifact_type, significance=a.significance); result['kind']='query'
        if a.summary: result['summary']=summarize(result['events'])
    else: raise ValueError(a.action)
    print(json.dumps(result, indent=2, sort_keys=True) if a.json else result)
    return result

def main() -> None:
    try: run()
    except (OSError, ValueError, json.JSONDecodeError) as exc: raise SystemExit(f'Historian command failed: {exc}') from exc
if __name__ == '__main__': main()

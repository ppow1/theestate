import json
from .discovery import rediscover_models
from .registry import load_registry
from .assignments import load_assignments, set_default, assign_actor, resolve_assignment
from .policy import evaluate_model_use

def handle(args):
    action=args.model_control_action
    if action=='rediscover': payload=rediscover_models(fetch_runtime=getattr(args,'fetch_runtime',False))
    elif action=='list-models': payload=load_registry()
    elif action=='assignments': payload=load_assignments()
    elif action=='set-default': payload=set_default(args.capability,args.model,approved_by=args.approved_by)
    elif action=='assign': payload=assign_actor(args.actor,args.capability,args.model,approved_by=args.approved_by)
    elif action=='validate-assignments':
        reg=load_registry(); data=load_assignments(); rows=[]
        for actor, caps in {**data.get('residents',{}), **data.get('workers',{})}.items():
            for cap, model in caps.items():
                if cap.startswith('fallback'): continue
                resolved=resolve_assignment(actor, cap); rows.append(evaluate_model_use(actor, cap, resolved.get('model_id'), registry=reg))
        payload={'ok':all(r['allowed'] for r in rows),'results':rows}
    else: payload={'error':'unknown_action'}
    print(json.dumps(payload, indent=2, sort_keys=True))

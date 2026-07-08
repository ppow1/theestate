from .registry import find_model
from .assignments import load_assignments

def _actor_allowed(assignments, actor, capability):
    auth=assignments.get('authority') or {}; pool='residents' if actor in (assignments.get('residents') or {}) else 'workers'
    allowed=(auth.get(pool) or {}).get(actor)
    return allowed is None or capability in allowed

def evaluate_model_use(actor, capability, model_id, root=None, registry=None):
    assignments=load_assignments(root); model=find_model(model_id, root, registry) if model_id else None; reasons=[]
    if not model: reasons.append('model_not_found')
    else:
        caps=model.get('capabilities') or ['unknown']
        if capability not in caps and not (capability=='text' and 'text' in caps): reasons.append(f'model_lacks_{capability}_capability')
        if model.get('cloud_allowed'): reasons.append('cloud_models_disallowed_by_default')
    if not _actor_allowed(assignments, actor, capability): reasons.append('actor_lacks_model_capability_authority')
    return {'actor':actor,'requested_capability':capability,'requested_model':model_id,'decision':'denied' if reasons else 'allowed','allowed':not reasons,'reason':'; '.join(reasons) if reasons else 'allowed','reasons':reasons,'authority':'steward_policy'}

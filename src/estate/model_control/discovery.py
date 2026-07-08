import json, urllib.request
from .registry import now, save_registry, write_diagnostics
try:
    from estate.ai_services.discovery import load_registry as load_ai_registry
except Exception: load_ai_registry=None

VISION_HINTS=('vision','llava','bakllava','moondream','qwen-vl','qwen2-vl','qwen2.5vl','minicpm-v','clip','mmproj')
CODE_HINTS=('code','coder','codellama','deepseek-coder')
EMBED_HINTS=('embed','embedding','nomic-embed')

def classify_capabilities(name, metadata=None):
    text=(name+' '+json.dumps(metadata or {}, sort_keys=True)).lower(); caps=[]
    if any(h in text for h in VISION_HINTS): caps.append('vision')
    if any(h in text for h in CODE_HINTS): caps.append('code')
    if any(h in text for h in EMBED_HINTS): caps.append('embedding')
    if 'tool' in text or 'function' in text: caps.append('tools')
    if 'whisper' in text or 'transcrib' in text: caps.append('audio/transcription')
    if 'diffusion' in text or 'imagegen' in text or 'stable-diffusion' in text: caps.append('image generation')
    if not caps and name: caps.append('text')
    return caps or ['unknown']

def confidence(name, meta=None): return 'inferred' if classify_capabilities(name, meta)!=['unknown'] else 'unknown'

def _ollama_tags(endpoint, timeout=2):
    with urllib.request.urlopen(endpoint.rstrip('/')+'/api/tags', timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8')).get('models') or []

def _from_service(svc, fetch_runtime=False):
    sid=svc.get('service_id'); provider=sid or svc.get('service_type') or 'unknown'; endpoint=svc.get('default_endpoint')
    rows=[]
    if fetch_runtime and sid=='ollama' and endpoint:
        try:
            for item in _ollama_tags(endpoint):
                name=item.get('name') or item.get('model');
                if name: rows.append((name,item))
        except Exception: pass
    for model in (svc.get('models') or svc.get('declared_models') or []):
        name=model.get('name') if isinstance(model,dict) else str(model); rows.append((name, model if isinstance(model,dict) else {}))
    seen=set(); out=[]
    for name,meta in rows:
        if not name or name in seen: continue
        seen.add(name); caps=classify_capabilities(name, meta)
        out.append({'model_id':f'{provider}:{name}','provider':provider,'service_id':sid,'model_name':name,'endpoint':endpoint,'capabilities':caps,'capability_confidence':confidence(name,meta),'context_length':meta.get('context_length') or meta.get('details',{}).get('context_length'),'size_bytes':meta.get('size') or meta.get('size_bytes'),'discovered_at':now(),'available':True,'local_only':svc.get('local_only', True),'cloud_allowed':False})
    return out

def rediscover_models(root=None, *, fetch_runtime=False):
    root = root or __import__("pathlib").Path.cwd()
    ai = load_ai_registry(root) if load_ai_registry else {'services':[]}
    models=[]
    for svc in ai.get('services',[]): models.extend(_from_service(svc, fetch_runtime=fetch_runtime))
    reg={'version':'estate-model-registry-v1','generated_at':now(),'source':'ai_services_control_plane','models':models}
    save_registry(reg, root); write_diagnostics({'generated_at':now(),'service_count':len(ai.get('services',[])),'model_count':len(models),'fetch_runtime':fetch_runtime}, root)
    return reg

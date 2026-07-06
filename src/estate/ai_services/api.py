from wsgiref.simple_server import make_server
from urllib.parse import parse_qs
import json
from .control import status, request
from .discovery import rediscover

def app(environ, start_response):
    path=environ.get('PATH_INFO',''); method=environ.get('REQUEST_METHOD','GET')
    code='200 OK'; payload={}
    parts=[p for p in path.split('/') if p]
    try:
        if path=='/ai-services/status': payload=status()
        elif path=='/ai-services/services': payload=status()['registry']
        elif len(parts)==3 and parts[:2]==['ai-services','services']:
            payload=next((s for s in status()['registry']['services'] if s['service_id']==parts[2]), {})
        elif method=='POST' and path=='/ai-services/rediscover': payload=rediscover(actor='alfred')
        elif method=='POST' and len(parts)==4 and parts[:2]==['ai-services','services']:
            q=parse_qs(environ.get('QUERY_STRING','')); payload=request(parts[3], parts[2], actor='alfred', approved_by=q.get('approved_by',[None])[0], dry_run=(q.get('dry_run',['true'])[0].lower()!='false'), health_timeout_seconds=float(q.get('health_timeout_seconds',[30])[0]), health_interval_seconds=float(q.get('health_interval_seconds',[2])[0]))
        elif method=='POST' and len(parts)==5 and parts[:2]==['ai-services','services'] and parts[3]=='models' and parts[4]=='load':
            q=parse_qs(environ.get('QUERY_STRING','')); payload=request('load_model', parts[2], actor='alfred', approved_by=q.get('approved_by',[None])[0], model=q.get('model',[None])[0], dry_run=(q.get('dry_run',['true'])[0].lower()!='false'), health_timeout_seconds=float(q.get('health_timeout_seconds',[30])[0]), health_interval_seconds=float(q.get('health_interval_seconds',[2])[0]))
        else: code='404 Not Found'; payload={'error':'not_found'}
    except Exception as e: code='500 Internal Server Error'; payload={'error':str(e)}
    body=json.dumps(payload, indent=2, sort_keys=True).encode(); start_response(code,[('Content-Type','application/json'),('Content-Length',str(len(body)))]) ; return [body]

def serve(host='127.0.0.1', port=8766):
    if host not in {'127.0.0.1','localhost','::1'}: raise ValueError('AI services API must bind loopback only')
    return make_server(host, port, app)

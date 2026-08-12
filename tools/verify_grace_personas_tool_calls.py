import json
import urllib.request

tools=[{"type":"function","function":{"name":"estate-comms8-live_estate_comms8_create_reasoning_request","parameters":{"type":"object"}}}]
prompt='Call estate-comms8-live_estate_comms8_create_reasoning_request with workflow_id="persona-probe", objective="probe", input_data={}, idempotency_key="persona-probe-1".'
rows=[]
for model in ('estate/grace','estate/grace-grounded-test'):
    body={"model":model,"messages":[{"role":"user","content":prompt}],"tools":tools,"stream":False}
    req=urllib.request.Request('http://127.0.0.1:11435/v1/chat/completions',json.dumps(body).encode(),{'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=20) as response:
        value=json.loads(response.read())
    call=value.get('choices',[{}])[0].get('message',{}).get('tool_calls',[])
    rows.append({'model':model,'tool_call_count':len(call),'tool_name':call[0]['function']['name'] if call else None,'mcp_invocation':value.get('estate',{}).get('mcp_invocation')})
print(json.dumps(rows,indent=2))

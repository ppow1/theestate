from estate.core.resident_gateway import models_payload, chat_completion


def test_models_expose_alfred_and_helen_only():
    ids = {m['id'] for m in models_payload()['data']}
    assert {'estate/alfred', 'estate/helen'} <= ids
    assert 'estate/grace' not in ids


def test_chat_completion_maps_helen_and_returns_openai_envelope(tmp_path):
    code, body = chat_completion({'model':'estate/helen','messages':[{'role':'user','content':'Who are you?'}], 'stream': False}, root=tmp_path)
    assert code == 200
    assert body['object'] == 'chat.completion'
    assert body['choices'][0]['message']['role'] == 'assistant'
    assert body['estate']['resident_id'] == 'helen'
    assert body['estate']['privileged_action_executed'] is False


def test_chat_completion_rejects_unknown_and_stream(tmp_path):
    code, body = chat_completion({'model':'estate/grace','messages':[]}, root=tmp_path)
    assert code == 404 and body['error']['code'] == 'unsupported_model'
    code, body = chat_completion({'model':'estate/helen','messages':[], 'stream': True}, root=tmp_path)
    assert code == 400 and body['error']['code'] == 'streaming_unsupported'


def test_gateway_session_persistence(tmp_path):
    payload = {'model':'estate/helen','messages':[{'role':'user','content':'hello'}], 'metadata': {'session_id': 'gw-session'}}
    assert chat_completion(payload, root=tmp_path)[1]['estate']['session_id'] == 'gw-session'
    chat_completion(payload, root=tmp_path)
    import json
    data=json.loads((tmp_path/'runtime/resident_interactions/sessions/gw-session.json').read_text())
    assert len(data['turns']) == 2

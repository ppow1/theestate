from estate.core.resident_gateway import models_payload, chat_completion, chat_completion_stream


def test_models_expose_active_residents_include_commissioned_grace():
    ids = {m['id'] for m in models_payload()['data']}
    assert {'estate/alfred', 'estate/helen', 'estate/ingrid', 'estate/grace'} <= ids


def test_conference_room_supplies_canonical_identity_before_generation(monkeypatch, tmp_path):
    canonical = {
        "alfred": ("Alfred", "Manager of Administration", "working directly for the Steward"),
        "ingrid": ("Ingrid", "Manager of Security", ""),
        "helen": ("Helen", "Manager of Human Resources", ""),
        "grace": ("Grace", "Director of Operations", ""),
    }
    forbidden = ("Engineering", "Finance", "Steward Liaison", "Office of Operations")
    seen = {}

    def fake_compose(resident, **kwargs):
        name, office, reporting = canonical[resident]
        provider_ready = f"Identity: {name}; office: {office}; {reporting}"
        return {
            "schema_version": "resident_runtime_identity_composition.v1",
            "resident_id": resident,
            "surface_id": kwargs["surface_id"],
            "identity_version_or_source_hash": f"hash-{resident}",
            "included_context_layers": [],
            "source_artifacts": [{"source": "data/registry/residents.json"}],
            "provider_ready_context": provider_ready,
            "failed_closed": False,
        }

    def fake_process_chat(resident, user_message, **kwargs):
        composition = kwargs.get("identity_composition")
        assert composition is not None
        assert composition["surface_id"] == "conference-room-gateway"
        seen[resident] = composition
        content = composition["provider_ready_context"].removeprefix("Identity: ")
        return {"session_id": kwargs.get("session_id"), "turn": {"turn_id": "turn_0001", "resident_id": resident, "resident_display_name": canonical[resident][0], "resident_response": content, "identity_composition": composition, "llm": {"provider": "fake", "fallback_used": False}}}

    monkeypatch.setattr("estate.core.resident_gateway.compose_resident_identity", fake_compose)
    monkeypatch.setattr("estate.core.resident_gateway.process_chat", fake_process_chat)
    code, body = chat_completion({"model": "estate/conference-room", "messages": [{"role": "user", "content": "State your office."}], "metadata": {"resident_targets": list(canonical), "session_id": "identity-room"}}, root=tmp_path)

    assert code == 200
    assert set(seen) == set(canonical)
    outputs = {turn["resident_id"]: turn["content"] for turn in body["estate"]["resident_turns"]}
    for resident, (name, office, reporting) in canonical.items():
        assert name in outputs[resident]
        assert office in outputs[resident]
        if reporting:
            assert reporting in outputs[resident]
        assert not any(title in outputs[resident] for title in forbidden)


def test_chat_completion_maps_helen_and_returns_openai_envelope(tmp_path):
    code, body = chat_completion({'model':'estate/helen','messages':[{'role':'user','content':'Who are you?'}], 'stream': False}, root=tmp_path)
    assert code == 200
    assert body['object'] == 'chat.completion'
    assert body['choices'][0]['message']['role'] == 'assistant'
    assert body['estate']['resident_id'] == 'helen'
    assert body['estate']['privileged_action_executed'] is False


def test_chat_completion_maps_ingrid_and_returns_openai_envelope(tmp_path):
    code, body = chat_completion({'model':'estate/ingrid','messages':[{'role':'user','content':'Who are you?'}], 'stream': False}, root=tmp_path)
    assert code == 200
    assert body['object'] == 'chat.completion'
    assert body['estate']['resident_id'] == 'ingrid'
    assert 'Ingrid' in body['choices'][0]['message']['content']
    assert body['estate']['privileged_action_executed'] is False


def test_chat_completion_maps_commissioned_grace(tmp_path):
    code, body = chat_completion({'model':'estate/grace','messages':[{'role':'user','content':'Who are you?'}]}, root=tmp_path)
    assert code == 200
    assert body['estate']['resident_id'] == 'grace'
    assert body['estate']['identity_hash']
    assert body['estate']['identity_schema_version']
    assert body['estate']['resident_package']['resident_id'] == 'grace'
    assert body['estate']['resident_package']['identity_source_hash'] == body['estate']['identity_hash']
    assert body['choices'][0]['message']['content'].strip()


def test_chat_completion_rejects_unknown_and_stream(tmp_path):
    code, body = chat_completion({'model':'estate/unknown','messages':[]}, root=tmp_path)
    assert code == 404 and body['error']['code'] == 'unsupported_model'
    code, body = chat_completion({'model':'estate/helen','messages':[], 'stream': True}, root=tmp_path)
    assert code == 400
    assert body['error']['code'] == 'missing_user_message'


def test_chat_completion_stream_returns_openai_sse_chunks(tmp_path):
    code, chunks = chat_completion_stream({'model':'estate/alfred','messages':[{'role':'user','content':'hello'}], 'stream': True}, root=tmp_path)
    chunks = list(chunks)
    assert code == 200
    assert chunks[0]['object'] == 'chat.completion.chunk'
    assert chunks[0]['choices'][0]['delta'] == {'role': 'assistant'}
    assert any(chunk['choices'][0]['delta'].get('content') for chunk in chunks)
    assert chunks[-1]['choices'][0]['delta'] == {}
    assert chunks[-1]['choices'][0]['finish_reason'] == 'stop'


def test_gateway_session_persistence(tmp_path):
    payload = {'model':'estate/helen','messages':[{'role':'user','content':'hello'}], 'metadata': {'session_id': 'gw-session'}}
    assert chat_completion(payload, root=tmp_path)[1]['estate']['session_id'] == 'gw-session'
    chat_completion(payload, root=tmp_path)
    import json
    data=json.loads((tmp_path/'runtime/resident_interactions/sessions/gw-session.json').read_text())
    assert len(data['turns']) == 2


def test_latest_user_message_selection_excludes_system_and_assistant(monkeypatch, tmp_path):
    calls = []
    def fake_process_chat(resident, user_message, **kwargs):
        calls.append((resident, user_message, kwargs))
        return {"session_id": kwargs.get("session_id") or "s1", "turn": {"turn_id":"turn_0001", "resident_id": resident, "resident_response":"ok", "llm":{"provider":"fake", "fallback_used":False}}}
    monkeypatch.setattr("estate.core.resident_gateway.process_chat", fake_process_chat)

    code, body = chat_completion({
        "model":"estate/helen",
        "messages":[
            {"role":"system", "content":"System prompt that must not be user text."},
            {"role":"user", "content":"Introduce yourself."},
            {"role":"assistant", "content":"I am Helen..."},
            {"role":"user", "content":"Approve a budget."},
        ],
    }, root=tmp_path)

    assert code == 200
    assert calls[0][0] == "helen"
    assert calls[0][1] == "Approve a budget."
    assert body["choices"][0]["message"]["content"] == "ok"


def test_missing_user_message_returns_invalid_request(tmp_path):
    code, body = chat_completion({"model":"estate/helen", "messages":[{"role":"system", "content":"Only system."}]}, root=tmp_path)
    assert code == 400
    assert body["error"]["code"] == "missing_user_message"


def test_multiturn_helen_supervision_uses_latest_user_message(monkeypatch, tmp_path):
    calls = []
    def fake_process_chat(resident, user_message, **kwargs):
        calls.append(user_message)
        return {"session_id":"s1", "turn":{"turn_id":"turn_0001", "resident_id":resident, "resident_response":f"answer: {user_message}", "llm":{}}}
    monkeypatch.setattr("estate.core.resident_gateway.process_chat", fake_process_chat)

    code, body = chat_completion({"model":"estate/helen", "messages":[
        {"role":"user", "content":"Introduce yourself."},
        {"role":"assistant", "content":"I am Helen..."},
        {"role":"user", "content":"Can you supervise engineering workers?"},
    ]}, root=tmp_path)

    assert code == 200
    assert calls == ["Can you supervise engineering workers?"]
    assert "Can you supervise engineering workers?" in body["choices"][0]["message"]["content"]


def test_multiturn_grace_hiring_uses_latest_user_message(monkeypatch, tmp_path):
    calls = []
    def fake_process_chat(resident, user_message, **kwargs):
        calls.append((resident, user_message))
        return {"session_id":"s1", "turn":{"turn_id":"turn_0001", "resident_id":resident, "resident_response":f"answer: {user_message}", "llm":{}}}
    monkeypatch.setattr("estate.core.resident_gateway.process_chat", fake_process_chat)

    code, body = chat_completion({"model":"estate/grace", "messages":[
        {"role":"user", "content":"Introduce yourself."},
        {"role":"assistant", "content":"I am Grace..."},
        {"role":"user", "content":"Hire three engineers."},
    ]}, root=tmp_path)

    assert code == 200
    assert calls == [("grace", "Hire three engineers.")]
    assert "Hire three engineers." in body["choices"][0]["message"]["content"]


def test_session_id_extraction_supports_openwebui_metadata(monkeypatch, tmp_path):
    seen = []
    def fake_process_chat(resident, user_message, **kwargs):
        seen.append(kwargs.get("session_id"))
        return {"session_id":kwargs.get("session_id"), "turn":{"turn_id":"turn_0001", "resident_id":resident, "resident_response":"ok", "llm":{}}}
    monkeypatch.setattr("estate.core.resident_gateway.process_chat", fake_process_chat)

    code, body = chat_completion({"model":"estate/helen", "metadata":{"chat_id":"chat-123"}, "messages":[{"role":"user", "content":"Hello"}]}, root=tmp_path)

    assert code == 200
    assert seen == ["chat-123"]
    assert body["estate"]["session_id"] == "chat-123"


def test_stream_chunks_include_content_final_stop_and_done_framing(monkeypatch, tmp_path):
    def fake_process_chat(resident, user_message, **kwargs):
        return {"session_id":"s1", "turn":{"turn_id":"turn_0001", "resident_id":resident, "resident_response":"streamed response", "llm":{}}}
    monkeypatch.setattr("estate.core.resident_gateway.process_chat", fake_process_chat)

    code, chunks = chat_completion_stream({"model":"estate/helen", "stream": True, "messages":[{"role":"user", "content":"Hello"}]}, root=tmp_path)
    chunks = list(chunks)

    assert code == 200
    assert chunks[0]["choices"][0]["delta"] == {"role":"assistant"}
    assert any(chunk["choices"][0]["delta"].get("content") for chunk in chunks)
    assert chunks[-1]["choices"][0]["finish_reason"] == "stop"

    import io, json as jsonlib
    from estate.core.resident_gateway import Handler
    class FakeHandler:
        wfile = io.BytesIO()
        headers = []
        close_connection = False
        def send_response(self, code): self.code = code
        def send_header(self, key, value): self.headers.append((key, value))
        def end_headers(self): pass
    fake = FakeHandler()
    Handler._send_sse(fake, chunks)
    payload = fake.wfile.getvalue().decode("utf-8")
    assert payload.rstrip().endswith("data: [DONE]")
    events = [line.removeprefix("data: ") for line in payload.splitlines() if line.startswith("data: {")]
    decoded = [jsonlib.loads(event) for event in events]
    assert decoded[-1]["choices"][0]["finish_reason"] == "stop"
    assert ("Connection", "close") in fake.headers
    assert fake.close_connection is True

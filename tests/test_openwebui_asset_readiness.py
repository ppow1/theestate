from tools.openwebui_asset_readiness import CRITICAL_ASSETS, probe


def test_critical_asset_probe_fails_closed_when_assets_are_missing(monkeypatch):
    calls = []

    class Response:
        status = 200
        headers = {"Content-Type": "text/html"}

        def read(self, _size):
            return b"<html></html>"

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def fake_urlopen(request, timeout):
        calls.append(request.full_url)
        if request.full_url.endswith(CRITICAL_ASSETS[1]):
            from urllib.error import HTTPError

            raise HTTPError(request.full_url, 404, "missing", {}, None)
        return Response()

    monkeypatch.setattr("tools.openwebui_asset_readiness.urlopen", fake_urlopen)
    result = probe("http://127.0.0.1:8080")
    assert result["status"] == "OPENWEBUI_NOT_READY"
    assert result["assets"][1]["status"] == 404
    assert len(calls) == 1 + len(CRITICAL_ASSETS)

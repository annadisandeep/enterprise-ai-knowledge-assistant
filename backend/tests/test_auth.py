def test_health_is_public_even_with_api_key(make_client):
    client = make_client(api_key="s3cret")
    assert client.get("/api/health").status_code == 200


def test_protected_endpoint_requires_key(make_client):
    client = make_client(api_key="s3cret")
    assert client.get("/api/documents").status_code == 401


def test_wrong_key_is_rejected(make_client):
    client = make_client(api_key="s3cret")
    resp = client.get("/api/documents", headers={"X-API-Key": "wrong"})
    assert resp.status_code == 401


def test_correct_key_is_accepted(make_client):
    client = make_client(api_key="s3cret")
    resp = client.get("/api/documents", headers={"X-API-Key": "s3cret"})
    assert resp.status_code == 200


def test_chat_requires_key(make_client):
    client = make_client(api_key="s3cret")
    resp = client.post("/api/chat", json={"question": "hello?"})
    assert resp.status_code == 401


def test_auth_disabled_when_no_key_configured(make_client):
    client = make_client(api_key="")
    assert client.get("/api/documents").status_code == 200

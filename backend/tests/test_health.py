def test_health_endpoint_reports_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["embedding_backend"] == "hashing"
    assert body["llm_provider"] == "mock"
    assert body["document_count"] == 0


def test_root_liveness(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

LONG_TEXT = (
    "Acme remote work policy. Employees may work remotely three days per week. "
    "The furniture stipend is three hundred dollars. "
) * 5


def _upload(client, name="policy.txt", content=None, ctype="text/plain"):
    content = content if content is not None else LONG_TEXT.encode()
    return client.post("/api/documents", files={"file": (name, content, ctype)})


def test_upload_lists_and_counts(client):
    resp = _upload(client)
    assert resp.status_code == 201, resp.text
    doc = resp.json()["document"]
    assert doc["filename"] == "policy.txt"
    assert doc["chunk_count"] >= 1
    assert len(doc["sha256"]) == 64

    listing = client.get("/api/documents").json()
    assert listing["total"] == 1
    assert listing["documents"][0]["id"] == doc["id"]

    health = client.get("/api/health").json()
    assert health["document_count"] == 1


def test_duplicate_upload_is_rejected(client):
    assert _upload(client).status_code == 201
    dup = _upload(client)
    assert dup.status_code == 409
    assert "already uploaded" in dup.json()["detail"]


def test_unsupported_type_rejected(client):
    resp = _upload(client, name="x.exe", content=b"MZbinary", ctype="application/octet-stream")
    assert resp.status_code == 422


def test_empty_file_rejected(client):
    resp = _upload(client, content=b"")
    assert resp.status_code == 422


def test_delete_document_removes_it(client):
    doc = _upload(client).json()["document"]
    delete = client.delete(f"/api/documents/{doc['id']}")
    assert delete.status_code == 200
    assert delete.json()["id"] == doc["id"]
    assert client.get("/api/documents").json()["total"] == 0


def test_delete_missing_document_returns_404(client):
    assert client.delete("/api/documents/does-not-exist").status_code == 404

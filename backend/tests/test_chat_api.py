from app.services.llm_provider import (
    LLMQuotaError,
    LLMTimeoutError,
    LLMUpstreamError,
    MockLLMProvider,
)

DOC = (
    "Acme remote work policy. Eligible employees may work remotely three days per "
    "week. New hires must work on site during their first ninety days. The home "
    "office furniture stipend is three hundred dollars."
)


def _seed(client, text=DOC, name="policy.txt"):
    resp = client.post("/api/documents", files={"file": (name, text.encode(), "text/plain")})
    assert resp.status_code == 201, resp.text


def _override_llm(client, provider):
    client.app.state.container._build_llm = lambda: provider
    client.app.state.container._rag = None


def test_chat_returns_grounded_answer_with_citations(client):
    _seed(client)
    resp = client.post("/api/chat", json={"question": "How many days can I work remotely?"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["grounded"] is True
    assert body["citations"]
    assert body["citations"][0]["filename"] == "policy.txt"


def test_chat_fallback_when_no_relevant_document(client):
    _seed(client)
    resp = client.post(
        "/api/chat", json={"question": "zzqq flibbertigibbet quantum wombat"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["used_fallback"] is True
    assert body["grounded"] is False
    assert body["citations"] == []


def test_chat_missing_credentials_returns_503(make_client):
    client = make_client(llm_provider="gemini", gemini_api_key="")
    _seed(client)
    resp = client.post("/api/chat", json={"question": "How many remote days?"})
    assert resp.status_code == 503


def test_chat_llm_upstream_failure_returns_502(client):
    _seed(client)
    _override_llm(client, MockLLMProvider(error=LLMUpstreamError("provider down")))
    resp = client.post("/api/chat", json={"question": "How many remote days?"})
    assert resp.status_code == 502


def test_chat_llm_quota_returns_429(client):
    _seed(client)
    _override_llm(client, MockLLMProvider(error=LLMQuotaError("rate limited")))
    resp = client.post("/api/chat", json={"question": "How many remote days?"})
    assert resp.status_code == 429


def test_chat_llm_timeout_returns_504(client):
    _seed(client)
    _override_llm(client, MockLLMProvider(error=LLMTimeoutError("too slow")))
    resp = client.post("/api/chat", json={"question": "How many remote days?"})
    assert resp.status_code == 504


def test_chat_validates_empty_question(client):
    resp = client.post("/api/chat", json={"question": ""})
    assert resp.status_code == 422

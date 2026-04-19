async def test_chat_returns_sse(test_client):
    session = (await test_client.post("/api/sessions", json={})).json()
    resp = await test_client.post("/api/chat", json={"session_id": session["id"], "message": "Hello"})
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]


async def test_chat_saves_turns(test_client):
    session = (await test_client.post("/api/sessions", json={})).json()
    # Consume the full SSE response
    await test_client.post("/api/chat", json={"session_id": session["id"], "message": "Hello"})

    detail = (await test_client.get(f"/api/sessions/{session['id']}")).json()
    turns = detail["turns"]
    assert len(turns) == 2
    assert turns[0]["role"] == "user"
    assert turns[0]["content"] == "Hello"
    assert turns[1]["role"] == "assistant"


async def test_chat_sets_title_from_first_message(test_client):
    session = (await test_client.post("/api/sessions", json={})).json()
    await test_client.post("/api/chat", json={"session_id": session["id"], "message": "Tell me about blood tests"})

    detail = (await test_client.get(f"/api/sessions/{session['id']}")).json()
    assert detail["title"] == "Tell me about blood tests"


async def test_chat_truncates_long_title(test_client):
    session = (await test_client.post("/api/sessions", json={})).json()
    long_msg = "A" * 100
    await test_client.post("/api/chat", json={"session_id": session["id"], "message": long_msg})

    detail = (await test_client.get(f"/api/sessions/{session['id']}")).json()
    assert detail["title"] == "A" * 50 + "..."


async def test_chat_not_found(test_client):
    resp = await test_client.post("/api/chat", json={"session_id": "nonexistent", "message": "Hi"})
    assert resp.status_code == 404

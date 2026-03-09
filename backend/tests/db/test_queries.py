from db.queries.sessions import (
    create_session,
    create_turn,
    get_session,
    get_turn_count,
    get_turns,
    list_sessions,
    update_session_model,
    update_session_title,
)


def test_create_session(db):
    session = create_session(db)
    assert session["id"] is not None
    assert session["title"] == "New Chat"
    assert session["model"] == "mock:default"


def test_create_session_with_model(db):
    session = create_session(db, model="openai:gpt-4o")
    assert session["model"] == "openai:gpt-4o"


def test_get_session(db):
    created = create_session(db)
    fetched = get_session(db, created["id"])
    assert fetched is not None
    assert fetched["id"] == created["id"]


def test_get_session_not_found(db):
    assert get_session(db, "nonexistent") is None


def test_list_sessions_desc_order(db):
    s1 = create_session(db)
    s2 = create_session(db)
    sessions = list_sessions(db)
    assert len(sessions) == 2
    # Most recent first
    assert sessions[0]["id"] == s2["id"]
    assert sessions[1]["id"] == s1["id"]


def test_update_session_title(db):
    session = create_session(db)
    update_session_title(db, session["id"], "Updated Title")
    fetched = get_session(db, session["id"])
    assert fetched["title"] == "Updated Title"


def test_update_session_model(db):
    session = create_session(db)
    update_session_model(db, session["id"], "claude:claude-sonnet")
    fetched = get_session(db, session["id"])
    assert fetched["model"] == "claude:claude-sonnet"


def test_create_and_get_turns(db):
    session = create_session(db)
    create_turn(db, session["id"], "user", "Hello", 0)
    create_turn(db, session["id"], "assistant", "Hi there", 1)

    turns = get_turns(db, session["id"])
    assert len(turns) == 2
    assert turns[0]["role"] == "user"
    assert turns[0]["content"] == "Hello"
    assert turns[1]["role"] == "assistant"
    assert turns[1]["turn_number"] == 1


def test_get_turn_count(db):
    session = create_session(db)
    assert get_turn_count(db, session["id"]) == 0
    create_turn(db, session["id"], "user", "Hello", 0)
    assert get_turn_count(db, session["id"]) == 1
    create_turn(db, session["id"], "assistant", "Hi", 1)
    assert get_turn_count(db, session["id"]) == 2

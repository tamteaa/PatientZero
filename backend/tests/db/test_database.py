from db.database import Database


def test_init_creates_tables(db):
    tables = db.fetch_all(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    names = [t["name"] for t in tables]
    assert "sessions" in names
    assert "turns" in names


def test_execute_and_fetch_one(db):
    db.execute("INSERT INTO sessions (id) VALUES (?)", ("test-1",))
    row = db.fetch_one("SELECT * FROM sessions WHERE id = ?", ("test-1",))
    assert row is not None
    assert row["id"] == "test-1"
    assert row["title"] == "New Chat"


def test_fetch_one_returns_none(db):
    row = db.fetch_one("SELECT * FROM sessions WHERE id = ?", ("nonexistent",))
    assert row is None


def test_fetch_all(db):
    db.execute("INSERT INTO sessions (id) VALUES (?)", ("a",))
    db.execute("INSERT INTO sessions (id) VALUES (?)", ("b",))
    rows = db.fetch_all("SELECT * FROM sessions")
    assert len(rows) == 2


def test_close_and_reconnect(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.init()
    db.execute("INSERT INTO sessions (id) VALUES (?)", ("x",))
    db.close()

    # Reconnect
    row = db.fetch_one("SELECT * FROM sessions WHERE id = ?", ("x",))
    assert row is not None
    assert row["id"] == "x"
    db.close()

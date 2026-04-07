CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    title TEXT DEFAULT 'New Chat',
    model TEXT DEFAULT 'mock:default',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    turn_number INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS simulations (
    id TEXT PRIMARY KEY,
    persona_name TEXT NOT NULL,
    scenario_name TEXT NOT NULL,
    model TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'running',
    config_json TEXT NOT NULL,
    duration_ms REAL,
    created_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS simulation_turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    simulation_id TEXT NOT NULL REFERENCES simulations(id),
    turn_number INTEGER NOT NULL,
    role TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    content TEXT NOT NULL,
    duration_ms REAL NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    simulation_id TEXT NOT NULL REFERENCES simulations(id),
    model TEXT NOT NULL,
    comprehension_score REAL,
    factual_recall REAL,
    applied_reasoning REAL,
    explanation_quality REAL,
    interaction_quality REAL,
    confidence_comprehension_gap TEXT,
    justification TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

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

CREATE TABLE IF NOT EXISTS experiments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    patient_distribution_json TEXT NOT NULL,
    doctor_distribution_json TEXT NOT NULL,
    current_optimization_target_id TEXT,
    sampling_seed INTEGER,
    sample_draw_index INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS optimization_targets (
    id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    prompts_json TEXT NOT NULL,
    parent_id TEXT REFERENCES optimization_targets(id),
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_opt_targets_experiment ON optimization_targets(experiment_id);

CREATE TABLE IF NOT EXISTS simulations (
    id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    persona_name TEXT NOT NULL,
    scenario_name TEXT NOT NULL,
    model TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'running',
    config_json TEXT NOT NULL,
    duration_ms REAL,
    created_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT,
    optimization_target_id TEXT REFERENCES optimization_targets(id)
);

CREATE INDEX IF NOT EXISTS idx_simulations_experiment ON simulations(experiment_id);
CREATE INDEX IF NOT EXISTS idx_simulations_optimization_target ON simulations(optimization_target_id);

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
    judge_results_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT DEFAULT (datetime('now'))
);

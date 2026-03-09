# Database Plan

## Overview
- SQLite with raw queries
- `backend/db/database.py` — Database class handles connection, init, schema migrations
- `backend/db/schema.sql` — All table definitions
- `backend/db/queries/` — Query functions grouped by domain

## Database Class

```python
class Database:
    def __init__(self, db_path: str = "patientzero.db"):
        ...

    def connect(self) -> sqlite3.Connection:
        """Get a connection (row_factory = sqlite3.Row)"""

    def init(self):
        """Run schema.sql to create tables if not exist"""

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a single query"""

    def fetch_one(self, query: str, params: tuple = ()) -> dict | None:
        """Execute and return one row as dict"""

    def fetch_all(self, query: str, params: tuple = ()) -> list[dict]:
        """Execute and return all rows as dicts"""

    def close(self):
        """Close connection"""
```

## Schema

### personas
| Column | Type | Notes |
|--------|------|-------|
| id | TEXT PK | e.g. "persona_01" |
| name | TEXT | e.g. "Maria, 62, retired teacher" |
| literacy_level | TEXT | low / marginal / adequate |
| anxiety | TEXT | low / medium / high |
| prior_knowledge | INTEGER | 0 or 1 |
| communication_style | TEXT | passive / engaged / assertive |
| age | INTEGER | |
| education | TEXT | |
| backstory | TEXT | Short background |
| system_prompt | TEXT | Full prompt for Patient Agent |

### scenarios
| Column | Type | Notes |
|--------|------|-------|
| id | TEXT PK | cbc_blood_test / pre_diabetes / medication |
| title | TEXT | |
| description | TEXT | |
| patient_context | TEXT | |
| lab_data | TEXT | JSON blob |
| clinical_prompt | TEXT | Explainer system prompt (clinical) |
| analogy_prompt | TEXT | Explainer system prompt (analogy) |

### quiz_questions
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| scenario_id | TEXT FK | → scenarios.id |
| question_text | TEXT | |
| question_type | TEXT | factual / reasoning |
| answer_key | TEXT | Correct answer + criteria |
| weight | REAL | 0.6 for factual, 0.4 for reasoning |

### sessions
| Column | Type | Notes |
|--------|------|-------|
| id | TEXT PK | UUID |
| persona_id | TEXT FK | → personas.id |
| scenario_id | TEXT FK | → scenarios.id |
| explanation_style | TEXT | clinical / analogy |
| interaction_mode | TEXT | static / dialog |
| status | TEXT | pending / running / completed / failed |
| total_turns | INTEGER | |
| clarification_requests | INTEGER | |
| confusion_signals | INTEGER | |
| explainer_adaptations | INTEGER | |
| created_at | TEXT | ISO timestamp |
| completed_at | TEXT | ISO timestamp |

### turns
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| session_id | TEXT FK | → sessions.id |
| role | TEXT | explainer / patient |
| content | TEXT | Message content |
| turn_number | INTEGER | |
| created_at | TEXT | ISO timestamp |

### quiz_responses
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| session_id | TEXT FK | → sessions.id |
| question_id | INTEGER FK | → quiz_questions.id |
| response_text | TEXT | Patient's answer |
| reasoning | TEXT | Patient's reasoning (in character) |

### scores
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| session_id | TEXT FK | → sessions.id |
| comprehension_score | REAL | 0–100 composite |
| factual_recall | REAL | 0–100 |
| applied_reasoning | REAL | 0–100 |
| explanation_quality | REAL | 1–5 |
| interaction_quality | REAL | 1–5, NULL for static |
| patient_confidence | REAL | 0–100 self-reported |
| patient_satisfaction | REAL | 1–5 (Explanation Satisfaction Scale) |
| pemat_score | REAL | 0–100 |
| confidence_comprehension_gap | REAL | |confidence - comprehension| |
| justification | TEXT | Judge's written reasoning |
| created_at | TEXT | ISO timestamp |

### participants (validation study)
| Column | Type | Notes |
|--------|------|-------|
| id | TEXT PK | UUID |
| nvs_score | INTEGER | 0–6 |
| literacy_level | TEXT | low / marginal / adequate |
| age | INTEGER | |
| education | TEXT | |
| created_at | TEXT | ISO timestamp |

### participant_sessions
| Column | Type | Notes |
|--------|------|-------|
| id | TEXT PK | UUID |
| participant_id | TEXT FK | → participants.id |
| scenario_id | TEXT FK | → scenarios.id |
| explanation_style | TEXT | |
| interaction_mode | TEXT | |
| status | TEXT | |
| created_at | TEXT | |

### participant_responses
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| participant_session_id | TEXT FK | → participant_sessions.id |
| question_id | INTEGER FK | → quiz_questions.id |
| response_text | TEXT | |
| confidence | REAL | 0–100 |
| satisfaction | REAL | 1–5 |

## Query Files

Each file in `db/queries/` exports functions that take a `Database` instance:

- **sessions.py**: `create_session()`, `get_session()`, `list_sessions()`, `update_session_status()`, `get_sessions_by_condition()`
- **personas.py**: `get_persona()`, `list_personas()`, `create_persona()`
- **scenarios.py**: `get_scenario()`, `list_scenarios()`
- **scores.py**: `save_score()`, `get_score_by_session()`, `get_scores_by_condition()`, `get_all_scores()`
- **participants.py**: `create_participant()`, `save_participant_response()`, `get_participant_results()`

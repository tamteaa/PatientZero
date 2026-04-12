"""
Base class for all repositories.

Rules every repo must follow:
  1. One class per aggregate root. Declare `TABLE` on the subclass.
  2. Every read/write on experiment-owned data takes `experiment_id` first,
     except `*_by_id` lookups. Global reads live only on ExperimentRepository
     or explicitly-named global helpers.
  3. No raw SQL outside `core/repositories/`. Services call repo methods.
  4. Multi-statement writes run inside `with repo.transaction():`.
  5. Repos return domain dataclasses. Row→dataclass hydration stays private.
"""

from contextlib import contextmanager

from core.db.database import Database


class BaseRepository:
    TABLE: str = ""

    def __init__(self, db: Database):
        self.db = db

    @contextmanager
    def transaction(self):
        """
        Run a block of writes atomically. sqlite3.Connection is itself a
        context manager that BEGINs on entry, COMMITs on clean exit, and
        ROLLBACKs on exception.
        """
        with self.db.conn:
            yield

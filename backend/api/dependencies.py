from core.config.settings import DB_PATH
from core.db.database import Database
from core.repositories import RepoSet
from core.logger import SimulationLogger

db = Database(DB_PATH)
repos = RepoSet.for_db(db)
logger = SimulationLogger()

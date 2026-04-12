from patientzero.config.settings import DB_PATH
from patientzero.db.database import Database
from patientzero.repositories import RepoSet
from patientzero.logger import SimulationLogger

db = Database(DB_PATH)
repos = RepoSet.for_db(db)
logger = SimulationLogger()

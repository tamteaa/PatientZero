from core.config.settings import DB_PATH
from core.db.database import Database
from core.services.logger import SimulationLogger
from core.services.simulation import SimulationService

db = Database(DB_PATH)
logger = SimulationLogger()
simulation_service = SimulationService(db, logger)

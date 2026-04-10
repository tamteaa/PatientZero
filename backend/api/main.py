from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config.settings import FRONTEND_URL
from core.db.queries.experiments import create_experiment, list_experiments
from backend.api.dependencies import db
from backend.api.routes.analysis import router as analysis_router
from backend.api.routes.chat import router as chat_router
from backend.api.routes.distributions import router as distributions_router
from backend.api.routes.experiments import router as experiments_router
from backend.api.routes.settings import router as settings_router
from backend.api.routes.simulate import router as simulate_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
    # Seed a default experiment so the app is usable on first run.
    if not list_experiments(db):
        create_experiment(db, name="Default")
    yield
    db.close()


app = FastAPI(title="PatientZero", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")
app.include_router(simulate_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(experiments_router, prefix="/api")
app.include_router(distributions_router, prefix="/api")

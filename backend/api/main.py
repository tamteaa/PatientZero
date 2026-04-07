from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config.settings import FRONTEND_URL
from backend.api.dependencies import db
from backend.api.routes.analysis import router as analysis_router
from backend.api.routes.chat import router as chat_router
from backend.api.routes.simulate import router as simulate_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
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

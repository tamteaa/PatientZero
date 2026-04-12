import logging
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger("patientzero.api")

from patientzero import Experiment
from patientzero.config.settings import FRONTEND_URL
from patientzero.examples.medical.config import MEDICAL_EXAMPLE_CONFIG
from backend.api.dependencies import db, repos
from backend.api.routes.agents import router as agents_router
from backend.api.routes.analysis import router as analysis_router
from backend.api.routes.chat import router as chat_router
from backend.api.routes.distributions import router as distributions_router
from backend.api.routes.experiments import router as experiments_router
from backend.api.routes.settings import router as settings_router
from backend.api.routes.simulate import router as simulate_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
    if not repos.experiments.list_all():
        Experiment(MEDICAL_EXAMPLE_CONFIG, db)
    yield
    db.close()


app = FastAPI(title="PatientZero", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code >= 400:
        print(
            f"\033[33m[{exc.status_code}]\033[0m {request.method} {request.url.path} "
            f"→ {exc.detail}",
            flush=True,
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(
        f"\033[33m[422]\033[0m {request.method} {request.url.path} → validation error:\n"
        f"  {exc.errors()}",
        flush=True,
    )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    print(
        f"\033[31m[500]\033[0m {request.method} {request.url.path} → {type(exc).__name__}: {exc}",
        flush=True,
    )
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": f"{type(exc).__name__}: {exc}"})


app.include_router(chat_router, prefix="/api")
app.include_router(simulate_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(experiments_router, prefix="/api")
app.include_router(distributions_router, prefix="/api")
app.include_router(agents_router, prefix="/api")

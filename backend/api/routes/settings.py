from dataclasses import asdict

from fastapi import APIRouter

from patientzero.config.settings import APP_SETTINGS

router = APIRouter()


@router.get("/settings")
def get_settings():
    return asdict(APP_SETTINGS)

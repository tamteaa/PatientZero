from dataclasses import asdict

from fastapi import APIRouter

from core.config.doctor_distribution import US_BASELINE_DOCTOR
from core.config.patient_distribution import AGE_BUCKET_RANGES, US_ADULT_BASELINE

router = APIRouter()


@router.get("/distributions/patient")
def get_patient_distribution():
    return {
        "distribution": asdict(US_ADULT_BASELINE),
        "age_bucket_ranges": AGE_BUCKET_RANGES,
    }


@router.get("/distributions/doctor")
def get_doctor_distribution():
    return {"distribution": asdict(US_BASELINE_DOCTOR)}

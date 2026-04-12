from enum import Enum


class Role(str, Enum):
    DOCTOR = "doctor"
    PATIENT = "patient"

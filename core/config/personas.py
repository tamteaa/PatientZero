from core.types import AgentProfile, Role

PATIENT_PROFILES = [
    AgentProfile(
        name="Maria Santos",
        role=Role.PATIENT,
        traits={"age": "62", "education": "High school", "literacy": "low", "anxiety": "high", "tendency": "agrees even when confused"},
        backstory="Retired cafeteria worker, 30 years in a school kitchen.",
    ),
    AgentProfile(
        name="James Thompson",
        role=Role.PATIENT,
        traits={"age": "45", "education": "MBA", "literacy": "high", "anxiety": "low", "tendency": "prefers data over reassurance"},
        backstory="Finance executive at a mid-size firm.",
    ),
    AgentProfile(
        name="Sofia Rodriguez",
        role=Role.PATIENT,
        traits={"age": "28", "education": "Community college", "literacy": "moderate", "anxiety": "high", "tendency": "asks many questions but gets overwhelmed easily"},
        backstory="Single mother of two young children.",
    ),
]

DOCTOR_PROFILES = [
    AgentProfile(
        name="Dr. Sarah Chen",
        role=Role.DOCTOR,
        traits={"empathy": "high", "verbosity": "moderate"},
        backstory="Family medicine physician, 15 years experience.",
    ),
    AgentProfile(
        name="Dr. Michael Torres",
        role=Role.DOCTOR,
        traits={"empathy": "low", "verbosity": "terse", "tendency": "rushes through explanations"},
        backstory="Internist at a high-volume urban clinic.",
    ),
]

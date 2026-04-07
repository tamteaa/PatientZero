"""
Profile generators for patient and doctor agents.

Sampling strategy: traits are correlated, not independent.
The patient causal chain: age_bucket → education → literacy → tendency
                          age_bucket → anxiety
This mirrors NAAL (health literacy) and NHIS (health anxiety) distributions.

The doctor causal chain: setting → time_pressure → verbosity
                         empathy (independent) → comprehension_checking
This mirrors RIAS/CAHPS distributions of physician communication styles.
"""

import random
from abc import ABC, abstractmethod

from core.types import AgentProfile, Role

# ── Names by demographic group (approximate US diversity) ─────────────────────

_NAMES_BY_GROUP: dict[str, list[str]] = {
    "hispanic": [
        "Maria Santos", "Carlos Ruiz", "Sofia Rodriguez", "Miguel Torres",
        "Ana Gutierrez", "Luis Hernandez", "Rosa Morales", "Jorge Vazquez",
    ],
    "black": [
        "Darnell Washington", "Keisha Johnson", "Marcus Brown", "Latoya Davis",
        "Jamal Williams", "Tamika Robinson", "DeShawn Harris", "Monique Jackson",
    ],
    "white": [
        "James Mitchell", "Linda Park", "Frank Davis", "Sarah Thompson",
        "Robert Chen", "Emily Anderson", "George Wallace", "Nancy Miller",
    ],
    "asian": [
        "Wei Zhang", "Priya Sharma", "David Kim", "Yuki Tanaka",
        "Nina Patel", "Kevin Nguyen", "Mei Lin", "Raj Krishnamurthy",
    ],
}

# US Census approximate race/ethnicity distribution
_GROUP_WEIGHTS = {"hispanic": 0.19, "black": 0.13, "white": 0.59, "asian": 0.06}

# ── Age distributions (US adult population, 18+) ─────────────────────────────

_AGE_BUCKETS = [
    ("young",  18, 35, 0.28),   # 18-35
    ("middle", 36, 55, 0.35),   # 36-55
    ("older",  56, 75, 0.25),   # 56-75
    ("senior", 76, 89, 0.12),   # 76+
]

# ── Education distributions by age bucket (Census ACS) ───────────────────────
# lower education levels more prevalent in older cohorts

_EDUCATION_BY_AGE: dict[str, list[tuple[str, float]]] = {
    "young":  [("less than high school", 0.08), ("high school diploma", 0.28),
               ("some college", 0.30), ("bachelor's degree", 0.24), ("graduate degree", 0.10)],
    "middle": [("less than high school", 0.10), ("high school diploma", 0.28),
               ("some college", 0.26), ("bachelor's degree", 0.24), ("graduate degree", 0.12)],
    "older":  [("less than high school", 0.14), ("high school diploma", 0.32),
               ("some college", 0.22), ("bachelor's degree", 0.20), ("graduate degree", 0.12)],
    "senior": [("less than high school", 0.22), ("high school diploma", 0.38),
               ("some college", 0.18), ("bachelor's degree", 0.14), ("graduate degree", 0.08)],
}

# ── Health literacy by education (NAAL data) ─────────────────────────────────
# NAAL: ~36% of US adults below basic/basic, ~53% intermediate, ~12% proficient

_LITERACY_BY_EDUCATION: dict[str, list[tuple[str, float]]] = {
    "less than high school": [("low", 0.75), ("moderate", 0.22), ("high", 0.03)],
    "high school diploma":   [("low", 0.40), ("moderate", 0.48), ("high", 0.12)],
    "some college":          [("low", 0.20), ("moderate", 0.55), ("high", 0.25)],
    "bachelor's degree":     [("low", 0.08), ("moderate", 0.42), ("high", 0.50)],
    "graduate degree":       [("low", 0.03), ("moderate", 0.27), ("high", 0.70)],
}

# ── Anxiety by age bucket (NHIS health worry data) ───────────────────────────

_ANXIETY_BY_AGE: dict[str, list[tuple[str, float]]] = {
    "young":  [("low", 0.35), ("moderate", 0.45), ("high", 0.20)],
    "middle": [("low", 0.30), ("moderate", 0.42), ("high", 0.28)],
    "older":  [("low", 0.25), ("moderate", 0.38), ("high", 0.37)],
    "senior": [("low", 0.20), ("moderate", 0.35), ("high", 0.45)],
}

# ── Behavioral tendency by literacy ──────────────────────────────────────────
# Health psychology: agreement bias ↑ with low literacy; assertiveness ↑ with high literacy

_TENDENCY_BY_LITERACY: dict[str, list[tuple[str, float]]] = {
    "low":      [("agrees even when confused", 0.50), ("asks few questions", 0.30),
                 ("defers to authority", 0.20)],
    "moderate": [("asks clarifying questions", 0.40), ("agrees mostly but pushes back sometimes", 0.35),
                 ("follows along but misses nuance", 0.25)],
    "high":     [("asks direct targeted questions", 0.45), ("challenges assumptions", 0.30),
                 ("wants data and specifics", 0.25)],
}

# ── Doctor distributions (RIAS/CAHPS calibrated) ─────────────────────────────

_DOCTOR_SETTINGS = [
    ("primary care", 0.45),
    ("hospital medicine", 0.20),
    ("emergency medicine", 0.15),
    ("specialty clinic", 0.20),
]

_TIME_PRESSURE_BY_SETTING: dict[str, list[tuple[str, float]]] = {
    "primary care":      [("low", 0.30), ("moderate", 0.50), ("high", 0.20)],
    "hospital medicine": [("low", 0.20), ("moderate", 0.40), ("high", 0.40)],
    "emergency medicine":[("low", 0.05), ("moderate", 0.25), ("high", 0.70)],
    "specialty clinic":  [("low", 0.40), ("moderate", 0.45), ("high", 0.15)],
}

_VERBOSITY_BY_TIME_PRESSURE: dict[str, list[tuple[str, float]]] = {
    "low":      [("terse", 0.10), ("moderate", 0.40), ("thorough", 0.50)],
    "moderate": [("terse", 0.25), ("moderate", 0.55), ("thorough", 0.20)],
    "high":     [("terse", 0.60), ("moderate", 0.35), ("thorough", 0.05)],
}

# CAHPS: empathy distribution from patient-reported measures
_EMPATHY_DIST = [("low", 0.20), ("moderate", 0.45), ("high", 0.35)]

# Comprehension checking correlates with empathy (RIAS data)
_COMPREHENSION_CHECK_BY_EMPATHY: dict[str, list[tuple[str, float]]] = {
    "low":      [("rarely", 0.60), ("sometimes", 0.35), ("always", 0.05)],
    "moderate": [("rarely", 0.20), ("sometimes", 0.55), ("always", 0.25)],
    "high":     [("rarely", 0.05), ("sometimes", 0.35), ("always", 0.60)],
}

_DOCTOR_NAMES = [
    "Dr. Sarah Chen", "Dr. Michael Torres", "Dr. Emily Park",
    "Dr. James Wilson", "Dr. Priya Patel", "Dr. David Kim",
    "Dr. Rachel Martinez", "Dr. Robert Thompson", "Dr. Aisha Johnson",
    "Dr. William Nguyen",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def _weighted_choice(options: list[tuple[str, float]]) -> str:
    values, weights = zip(*options)
    return random.choices(list(values), weights=list(weights), k=1)[0]


# ── Abstract base ─────────────────────────────────────────────────────────────

class ProfileGenerator(ABC):
    @abstractmethod
    def generate(self, n: int = 1) -> list[AgentProfile]:
        """Generate n profiles."""


# ── Patient generator ────────────────────────────────────────────────────────

class StaticPatientGenerator(ProfileGenerator):
    """
    Samples patient profiles from correlated demographic distributions.

    Causal chain:
        age_bucket → education → literacy → tendency
        age_bucket → anxiety
        group → name

    Calibrated to NAAL (literacy), Census ACS (demographics), NHIS (anxiety).
    """

    def __init__(self, used_names: set[str] | None = None):
        self._used_names: set[str] = used_names or set()

    def generate(self, n: int = 1, literacy: str | None = None, anxiety: str | None = None) -> list[AgentProfile]:
        return [self._generate_one(literacy=literacy, anxiety=anxiety) for _ in range(n)]

    def _generate_one(self, literacy: str | None = None, anxiety: str | None = None) -> AgentProfile:
        # 1. Age bucket
        bucket_data = [(label, lo, hi, w) for label, lo, hi, w in _AGE_BUCKETS]
        label, lo, hi, _ = random.choices(bucket_data, weights=[b[3] for b in bucket_data], k=1)[0]
        age = random.randint(lo, hi)

        # 2. Education (conditioned on age bucket)
        education = _weighted_choice(_EDUCATION_BY_AGE[label])

        # 3. Literacy — use constraint if given, else sample from education (NAAL)
        if literacy is None:
            literacy = _weighted_choice(_LITERACY_BY_EDUCATION[education])

        # 4. Anxiety — use constraint if given, else sample from age bucket (NHIS)
        if anxiety is None:
            anxiety = _weighted_choice(_ANXIETY_BY_AGE[label])

        # 5. Behavioral tendency (conditioned on final literacy)
        tendency = _weighted_choice(_TENDENCY_BY_LITERACY[literacy])

        # 6. Name (from demographic group)
        group = _weighted_choice(list(_GROUP_WEIGHTS.items()))
        name = self._pick_name(group)

        backstory = self._backstory(age, education, literacy, anxiety, tendency)

        return AgentProfile(
            name=name,
            role=Role.PATIENT,
            traits={
                "age": str(age),
                "education": education,
                "literacy": literacy,
                "anxiety": anxiety,
                "tendency": tendency,
            },
            backstory=backstory,
        )

    def _pick_name(self, group: str) -> str:
        pool = _NAMES_BY_GROUP.get(group, _NAMES_BY_GROUP["white"])
        available = [n for n in pool if n not in self._used_names]
        if not available:
            # Exhausted pool — allow repeats with suffix
            base = random.choice(pool)
            name = f"{base} Jr."
        else:
            name = random.choice(available)
        self._used_names.add(name)
        return name

    @staticmethod
    def _backstory(age: int, education: str, literacy: str,
                   anxiety: str, tendency: str) -> str:
        fragments = []

        if education in ("less than high school", "high school diploma"):
            fragments.append("Did not pursue higher education.")
        elif education in ("bachelor's degree", "graduate degree"):
            fragments.append("Completed a university degree.")

        if anxiety == "high":
            fragments.append("Tends to worry about health news and often fears the worst.")
        elif anxiety == "low":
            fragments.append("Generally calm about medical matters.")

        if literacy == "low":
            fragments.append("Finds medical terminology confusing.")
        elif literacy == "high":
            fragments.append("Comfortable reading and interpreting medical documents.")

        if tendency == "agrees even when confused":
            fragments.append("Often nods along to avoid seeming difficult, even when not fully understanding.")
        elif tendency == "asks direct targeted questions":
            fragments.append("Asks pointed questions and won't leave until satisfied with the answers.")

        return " ".join(fragments) if fragments else f"Patient, age {age}."


# ── Doctor generator ─────────────────────────────────────────────────────────

class StaticDoctorGenerator(ProfileGenerator):
    """
    Samples doctor profiles from communication style distributions.

    Causal chain:
        setting → time_pressure → verbosity
        empathy → comprehension_checking

    Calibrated to RIAS (interaction coding) and CAHPS (patient-reported measures).
    """

    def __init__(self, used_names: set[str] | None = None):
        self._used_names: set[str] = used_names or set()
        self._name_pool = list(_DOCTOR_NAMES)

    def generate(self, n: int = 1, empathy: str | None = None, verbosity: str | None = None) -> list[AgentProfile]:
        return [self._generate_one(empathy=empathy, verbosity=verbosity) for _ in range(n)]

    def _generate_one(self, empathy: str | None = None, verbosity: str | None = None) -> AgentProfile:
        # 1. Practice setting
        setting = _weighted_choice(_DOCTOR_SETTINGS)

        # 2. Time pressure (conditioned on setting)
        time_pressure = _weighted_choice(_TIME_PRESSURE_BY_SETTING[setting])

        # 3. Verbosity — use constraint if given, else sample from time pressure
        if verbosity is None:
            verbosity = _weighted_choice(_VERBOSITY_BY_TIME_PRESSURE[time_pressure])

        # 4. Empathy — use constraint if given, else sample from CAHPS distribution
        if empathy is None:
            empathy = _weighted_choice(_EMPATHY_DIST)

        # 5. Comprehension checking (conditioned on final empathy — RIAS)
        comp_check = _weighted_choice(_COMPREHENSION_CHECK_BY_EMPATHY[empathy])

        # 6. Name
        name = self._pick_name()

        backstory = (
            f"{setting.capitalize()} physician. "
            f"{'Under time pressure, keeps explanations concise.' if time_pressure == 'high' else 'Has adequate time for patient conversations.'} "
            f"{'Highly empathetic, attuned to patient emotions.' if empathy == 'high' else 'Focuses on clinical facts.' if empathy == 'low' else ''}"
        ).strip()

        return AgentProfile(
            name=name,
            role=Role.DOCTOR,
            traits={
                "setting": setting,
                "time_pressure": time_pressure,
                "verbosity": verbosity,
                "empathy": empathy,
                "comprehension_checking": comp_check,
            },
            backstory=backstory,
        )

    def _pick_name(self) -> str:
        available = [n for n in self._name_pool if n not in self._used_names]
        if not available:
            available = self._name_pool
        name = random.choice(available)
        self._used_names.add(name)
        return name

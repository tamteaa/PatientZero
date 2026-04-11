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

from core.config.doctor_distribution import US_BASELINE_DOCTOR
from core.config.patient_distribution import AGE_BUCKET_RANGES, US_ADULT_BASELINE
from core.types import AgentProfile, DoctorDistribution, PatientDistribution, Role

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

_DOCTOR_NAMES = [
    "Dr. Sarah Chen", "Dr. Michael Torres", "Dr. Emily Park",
    "Dr. James Wilson", "Dr. Priya Patel", "Dr. David Kim",
    "Dr. Rachel Martinez", "Dr. Robert Thompson", "Dr. Aisha Johnson",
    "Dr. William Nguyen",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def _weighted_choice(options: list[tuple[str, float]], rng: random.Random | None = None) -> str:
    r = rng or random
    values, weights = zip(*options)
    return r.choices(list(values), weights=list(weights), k=1)[0]


# ── Abstract base ─────────────────────────────────────────────────────────────

class ProfileGenerator(ABC):
    @abstractmethod
    def generate(self, n: int = 1) -> list[AgentProfile]:
        """Generate n profiles."""


# ── Patient generator ────────────────────────────────────────────────────────

class StaticPatientGenerator(ProfileGenerator):
    """
    Samples patient profiles from a PatientDistribution.

    Causal chain:
        age → education → literacy → tendency
        age → anxiety
        group → name

    Defaults to US_ADULT_BASELINE.
    """

    def __init__(
        self,
        distribution: PatientDistribution = US_ADULT_BASELINE,
        used_names: set[str] | None = None,
    ):
        self.distribution = distribution
        self._used_names: set[str] = used_names or set()

    def generate(
        self,
        n: int = 1,
        literacy: str | None = None,
        anxiety: str | None = None,
        rng: random.Random | None = None,
    ) -> list[AgentProfile]:
        return [self._generate_one(literacy=literacy, anxiety=anxiety, rng=rng) for _ in range(n)]

    def _generate_one(
        self,
        literacy: str | None = None,
        anxiety: str | None = None,
        rng: random.Random | None = None,
    ) -> AgentProfile:
        r = rng or random
        d = self.distribution

        # 1. Age bucket + concrete age
        bucket = d.age.sample(rng=r)
        lo, hi = AGE_BUCKET_RANGES[bucket]
        age = r.randint(lo, hi)

        # 2. Education (conditioned on age bucket)
        education = d.education_by_age.sample(bucket, rng=r)

        # 3. Literacy — use constraint if given, else sample from education (NAAL)
        if literacy is None:
            literacy = d.literacy_by_education.sample(education, rng=r)

        # 4. Anxiety — use constraint if given, else sample from age bucket (NHIS)
        if anxiety is None:
            anxiety = d.anxiety_by_age.sample(bucket, rng=r)

        # 5. Behavioral tendency (conditioned on final literacy)
        tendency = d.tendency_by_literacy.sample(literacy, rng=r)

        # 6. Name (from demographic group)
        group = _weighted_choice(list(_GROUP_WEIGHTS.items()), rng=r)
        name = self._pick_name(group, rng=r)

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

    def _pick_name(self, group: str, rng: random.Random | None = None) -> str:
        r = rng or random
        pool = _NAMES_BY_GROUP.get(group, _NAMES_BY_GROUP["white"])
        available = [n for n in pool if n not in self._used_names]
        if not available:
            # Exhausted pool — allow repeats with suffix
            base = r.choice(pool)
            name = f"{base} Jr."
        else:
            name = r.choice(available)
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
    Samples doctor profiles from a DoctorDistribution.

    Causal chain:
        setting → time_pressure → verbosity
        empathy → comprehension_checking

    Defaults to US_BASELINE_DOCTOR.
    """

    def __init__(
        self,
        distribution: DoctorDistribution = US_BASELINE_DOCTOR,
        used_names: set[str] | None = None,
    ):
        self.distribution = distribution
        self._used_names: set[str] = used_names or set()
        self._name_pool = list(_DOCTOR_NAMES)

    def generate(
        self,
        n: int = 1,
        empathy: str | None = None,
        verbosity: str | None = None,
        rng: random.Random | None = None,
    ) -> list[AgentProfile]:
        return [self._generate_one(empathy=empathy, verbosity=verbosity, rng=rng) for _ in range(n)]

    def _generate_one(
        self,
        empathy: str | None = None,
        verbosity: str | None = None,
        rng: random.Random | None = None,
    ) -> AgentProfile:
        r = rng or random
        d = self.distribution

        # 1. Practice setting
        setting = d.setting.sample(rng=r)

        # 2. Time pressure (conditioned on setting)
        time_pressure = d.time_pressure_by_setting.sample(setting, rng=r)

        # 3. Verbosity — use constraint if given, else sample from time pressure
        if verbosity is None:
            verbosity = d.verbosity_by_time_pressure.sample(time_pressure, rng=r)

        # 4. Empathy — use constraint if given, else sample from CAHPS distribution
        if empathy is None:
            empathy = d.empathy.sample(rng=r)

        # 5. Comprehension checking (conditioned on final empathy — RIAS)
        comp_check = d.comprehension_check_by_empathy.sample(empathy, rng=r)

        # 6. Name
        name = self._pick_name(rng=r)

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

    def _pick_name(self, rng: random.Random | None = None) -> str:
        r = rng or random
        available = [n for n in self._name_pool if n not in self._used_names]
        if not available:
            available = self._name_pool
        name = r.choice(available)
        self._used_names.add(name)
        return name

from dataclasses import asdict

from core.agents.prompts import build_doctor_prompt, build_patient_prompt
from core.agents.sim_agent import SimAgent
from core.db.database import Database
from core.db.queries.simulations import create_simulation
from core.llm.factory import parse_provider_model
from core.services.logger import SimulationLogger
from core.simulation.simulation import DEFAULT_MAX_TURNS, Simulation
from core.types import AgentProfile, Scenario


class SimulationService:
    def __init__(self, db: Database, logger: SimulationLogger):
        self.db = db
        self.logger = logger
        self._active: dict[str, Simulation] = {}

    def get_active(self, sim_id: str) -> Simulation | None:
        return self._active.get(sim_id)

    def create_and_start(
        self,
        doctor_profile: AgentProfile,
        patient_profile: AgentProfile,
        scenario: Scenario,
        model: str,
        max_turns: int = DEFAULT_MAX_TURNS,
    ) -> str:
        provider, model_name = parse_provider_model(model)

        doctor_prompt = build_doctor_prompt(doctor_profile, scenario)
        patient_prompt = build_patient_prompt(patient_profile)

        doctor = SimAgent(provider, model_name, doctor_profile, doctor_prompt)
        patient = SimAgent(provider, model_name, patient_profile, patient_prompt)

        sim_record = create_simulation(
            self.db,
            persona_name=patient_profile.name,
            scenario_name=scenario.test_name,
            model=model,
            config={
                "doctor": asdict(doctor_profile),
                "patient": asdict(patient_profile),
                "scenario": asdict(scenario),
                "model": model,
            },
        )
        sim_id = sim_record.id

        sim = Simulation(self.db, sim_id, doctor, patient, max_turns=max_turns, logger=self.logger)
        self._active[sim_id] = sim

        self.logger.start(sim_id, {
            "Model": model,
            "Scenario": scenario.test_name,
            "Doctor": doctor_profile.name,
            "Patient": patient_profile.name,
        })

        sim.on_done = lambda: self._active.pop(sim_id, None)
        sim.start()

        return sim_id

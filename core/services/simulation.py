from dataclasses import asdict

from core.agents.prompts import build_doctor_prompt, build_patient_prompt
from core.agents.sim_agent import SimAgent
from core.db.database import Database
from core.db.queries.experiments import get_experiment
from core.db.queries.optimization_targets import get_optimization_target
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
        experiment_id: str,
        doctor_profile: AgentProfile,
        patient_profile: AgentProfile,
        scenario: Scenario,
        model: str,
        *,
        style: str = "clinical",
        policy_version: str = "baseline",
        batch_id: str | None = None,
        max_turns: int = DEFAULT_MAX_TURNS,
    ) -> str:
        provider, model_name = parse_provider_model(model)

        doctor_tpl: str | None = None
        patient_tpl: str | None = None
        exp = get_experiment(self.db, experiment_id)
        if exp and exp.current_optimization_target_id:
            target = get_optimization_target(self.db, exp.current_optimization_target_id)
            if target and target.prompts:
                doctor_tpl = target.prompts.get("doctor")
                patient_tpl = target.prompts.get("patient")

        doctor_prompt = build_doctor_prompt(
            doctor_profile,
            scenario,
            style=style,
            policy_version=policy_version,
            doctor_template=doctor_tpl,
        )
        patient_prompt = build_patient_prompt(patient_profile, patient_template=patient_tpl)

        doctor = SimAgent(provider, model_name, doctor_profile, doctor_prompt)
        patient = SimAgent(provider, model_name, patient_profile, patient_prompt)

        opt_id = exp.current_optimization_target_id if exp else None
        sim_record = create_simulation(
            self.db,
            experiment_id=experiment_id,
            persona_name=patient_profile.name,
            scenario_name=scenario.name,
            model=model,
            config={
                "doctor": asdict(doctor_profile),
                "patient": asdict(patient_profile),
                "scenario": asdict(scenario),
                "model": model,
                "style": style,
                "policy_version": policy_version,
                "batch_id": batch_id,
                "optimization_target_id": opt_id,
            },
            optimization_target_id=opt_id,
        )
        sim_id = sim_record.id

        sim = Simulation(self.db, sim_id, doctor, patient, max_turns=max_turns, logger=self.logger)
        self._active[sim_id] = sim

        self.logger.start(sim_id, {
            "Model": model,
            "Scenario": scenario.name,
            "Doctor": doctor_profile.name,
            "Patient": patient_profile.name,
        })

        sim.on_done = lambda: self._active.pop(sim_id, None)
        sim.start()

        return sim_id

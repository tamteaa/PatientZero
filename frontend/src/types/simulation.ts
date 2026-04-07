export interface AgentProfile {
  name: string;
  role: string;
  traits: Record<string, string>;
  backstory: string;
}

export interface Scenario {
  name: string;
  description: string;
}

export type SimulationRole = 'doctor' | 'patient';

export interface SimulationConfig {
  scenario_name?: string;  // omit or "random" to generate
  model: string;
  max_turns?: number;
  patient_literacy?: string;
  patient_anxiety?: string;
  doctor_empathy?: string;
  doctor_verbosity?: string;
}

export interface SimulationMessage {
  role: SimulationRole;
  content: string;
}

export type SimulationStatus = 'idle' | 'running' | 'paused' | 'completed' | 'error';

export interface SimulationState {
  status: SimulationStatus;
  simulationId: string | null;
  config: SimulationConfig | null;
  messages: SimulationMessage[];
  streamingRole: SimulationRole | null;
  streamingContent: string;
  currentTurn: number;
  error: string | null;
}

export interface SimulationSummary {
  id: string;
  persona_name: string;
  scenario_name: string;
  model: string;
  state: string;
  duration_ms: number | null;
  created_at: string;
}

export interface SimulationTurn {
  turn_number: number;
  role: SimulationRole;
  content: string;
  duration_ms: number;
}

export interface SimulationDetail extends SimulationSummary {
  turns: SimulationTurn[];
  config_json: string;
  text_status?: string;
  max_turns?: number;
}

export interface Evaluation {
  id: number;
  simulation_id: string;
  model: string;
  comprehension_score: number | null;
  factual_recall: number | null;
  applied_reasoning: number | null;
  explanation_quality: number | null;
  interaction_quality: number | null;
  confidence_comprehension_gap: string | null;
  justification: string | null;
  created_at: string;
  persona_name?: string;
  scenario_name?: string;
}

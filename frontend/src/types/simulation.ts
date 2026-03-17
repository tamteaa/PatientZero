export interface Persona {
  name: string;
  age: string;
  education: string;
  literacy_level: string;
  anxiety: string;
  prior_knowledge: string;
  communication_style: string;
  backstory: string;
}

export interface Scenario {
  test_name: string;
  results: string;
  normal_range: string;
  significance: string;
  keywords: string[];
}

export type Style = 'clinical' | 'analogy';
export type Mode = 'static' | 'dialog';
export type SimulationRole = 'explainer' | 'patient';

export interface SimulationConfig {
  persona: Persona;
  style: Style;
  mode: Mode;
  scenario: Scenario;
  model: string;
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
  style: Style;
  mode: Mode;
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
}

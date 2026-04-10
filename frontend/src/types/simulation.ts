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
  experiment_id: string;
  scenario_name?: string;  // omit or "random" to generate
  model: string;
  max_turns?: number;
  patient_literacy?: string;
  patient_anxiety?: string;
  doctor_empathy?: string;
  doctor_verbosity?: string;
}

export interface Experiment {
  id: string;
  name: string;
  created_at: string;
  current_optimization_target_id: string | null;
}

export interface ExperimentDetail extends Experiment {
  patient_distribution: PatientDistribution;
  doctor_distribution: DoctorDistribution;
}

// ── Distributions ────────────────────────────────────────────────────────────

export interface Distribution {
  weights: Record<string, number>;
}

export interface ConditionalDistribution {
  by_parent: Record<string, Distribution>;
}

export interface PatientDistribution {
  age: Distribution;
  education_by_age: ConditionalDistribution;
  literacy_by_education: ConditionalDistribution;
  anxiety_by_age: ConditionalDistribution;
  tendency_by_literacy: ConditionalDistribution;
}

export interface DoctorDistribution {
  setting: Distribution;
  time_pressure_by_setting: ConditionalDistribution;
  verbosity_by_time_pressure: ConditionalDistribution;
  empathy: Distribution;
  comprehension_check_by_empathy: ConditionalDistribution;
}

export interface PatientDistributionResponse {
  distribution: PatientDistribution;
  age_bucket_ranges: Record<string, [number, number]>;
}

export interface DoctorDistributionResponse {
  distribution: DoctorDistribution;
}

export interface CoverageReport {
  cells_total: number;
  cells_hit: number;
  simulations_counted: number;
  coverage_pct: number;  // 0.0–1.0
  estimated_total_needed: number;
}

// ── Feedback / optimization ─────────────────────────────────────────────────

export interface OptimizationTarget {
  id: string;
  experiment_id: string;
  kind: string;
  prompts: Record<string, string>;
  parent_id: string | null;
  created_at: string;
}

export interface OptimizeRequest {
  metric_weights?: Record<string, number>;
  seeding_mode?: 'historical_failures' | 'fresh_trials';
  num_candidates?: number;
  trials_per_candidate?: number;
  worst_cases_k?: number;
}

export interface CandidateScoreSummary {
  target_id: string;
  mean_score: number;
  trial_count: number;
}

export interface OptimizationResult {
  new_target: OptimizationTarget;
  baseline: CandidateScoreSummary;
  candidates: CandidateScoreSummary[];
  improvement: number;
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
  experiment_id: string;
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

export interface JudgeResult {
  model: string;
  comprehension_score: number | null;
  factual_recall: number | null;
  applied_reasoning: number | null;
  explanation_quality: number | null;
  interaction_quality: number | null;
  confidence_comprehension_gap: string | null;
  justification: string | null;
}

export interface Evaluation {
  id: number | null;
  simulation_id: string;
  created_at: string | null;
  judge_results: JudgeResult[];
}

export type JudgeScoreKey =
  | 'comprehension_score'
  | 'factual_recall'
  | 'applied_reasoning'
  | 'explanation_quality'
  | 'interaction_quality';

export function meanScore(ev: Evaluation, key: JudgeScoreKey): number | null {
  const vals = ev.judge_results
    .map((j) => j[key])
    .filter((v): v is number => v != null);
  return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
}

export interface AppSettings {
  max_concurrent_simulations: number;
}

// ── Roles / profiles ────────────────────────────────────────────────────────

/** Agent name — arbitrary, declared in the experiment config. */
export type SimulationRole = string;

/** Map of sampled trait values per agent, keyed by agent name. */
export type ProfileMap = Record<string, Record<string, string>>;

// ── Experiment counts ───────────────────────────────────────────────────────

export interface ExperimentCounts {
  total: number;
  completed: number;
  running: number;
  error: number;
  evaluated: number;
}

// ── Distributions (DAG of trait nodes, per backend distribution_to_dict) ────

export interface MarginalNode {
  kind: 'marginal';
  weights: Record<string, number>;
}

export interface ConditionalNode {
  kind: 'conditional';
  parent: string;
  /** table[parent_value][child_value] = prob */
  table: Record<string, Record<string, number>>;
}

export type DistributionNode = MarginalNode | ConditionalNode;

/** A trait DAG: keys are trait names; values are marginal or conditional nodes. */
export type AgentDistribution = Record<string, DistributionNode>;

export interface AgentDistributionResponse {
  distribution: AgentDistribution;
}

// ── Experiment config (nested inside Experiment) ────────────────────────────

export interface AgentSpec {
  name: string;
  prompt: string;
  distribution: AgentDistribution;
  model: string | null;
}

export interface JudgeSpec {
  rubric: Record<string, string>;
  instructions: string;
  model: string | null;
}

export interface ExperimentConfig {
  name: string;
  agents: AgentSpec[];
  judge: JudgeSpec;
  model: string;
  seed: number | null;
  max_turns: number;
  num_optimizations: number;
}

export interface Experiment {
  id: string;
  created_at: string;
  config: ExperimentConfig;
  current_optimization_target_id: string | null;
  sample_draw_index: number;
  counts: ExperimentCounts;
}

// ── Coverage ────────────────────────────────────────────────────────────────

export interface CoverageReport {
  cells_total: number;
  cells_hit: number;
  simulations_counted: number;
  /** 0.0–1.0 */
  coverage_pct: number;
  estimated_total_needed: number;
  target_method?: 'monte_carlo' | 'independence';
  mc_samples?: number | null;
  /** 1 − TVD between target cell distribution and completed sims (when available). */
  distribution_match?: number | null;
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

/**
 * Backend-only opts the POST /optimize endpoint doesn't currently accept a
 * body, but the type is retained for future parameterization. If passed, it's
 * sent as the request body and silently ignored server-side today.
 */
export interface OptimizeRequest {
  metric_weights?: Record<string, number>;
  seeding_mode?: 'historical_failures' | 'fresh_trials';
  num_candidates?: number;
  trials_per_candidate?: number;
  worst_cases_k?: number;
}

/** Matches FeedbackService.optimize().to_dict(): new + previous target, rationale, trace count. */
export interface OptimizationResult {
  new_target: OptimizationTarget;
  previous_target: OptimizationTarget;
  rationale: string;
  traces_considered: number;
}

// ── Simulation (records + streaming) ────────────────────────────────────────

export interface SimulationConfigRecord {
  experiment_id: string;
  optimization_target_id: string;
  profiles: ProfileMap;
  model: string;
  max_turns: number;
  draw_index: number | null;
}

/** Request body for POST /simulate — backend's `SimulateRequest`. */
export interface StartSimulationRequest {
  experiment_id: string;
  model: string;
  max_turns?: number;
  /** Per-agent trait pins: {agent_name: {trait: value}}. */
  constraints?: Record<string, Record<string, string>>;
}

export type SimulationState = 'idle' | 'running' | 'paused' | 'completed' | 'error';

/** Matches SimulationRecord.to_dict. */
export interface SimulationSummary {
  id: string;
  created_at: string;
  config: SimulationConfigRecord;
  state: string;
  duration_ms: number | null;
  completed_at: string | null;
}

export interface SimulationTurn {
  turn_number: number;
  role: SimulationRole;
  agent_type?: string;
  content: string;
  duration_ms: number;
}

/** GET /simulations/{id} — record + turns; active sims also include text_status/max_turns overlays. */
export interface SimulationDetail extends SimulationSummary {
  turns: SimulationTurn[];
  text_status?: string;
  /** Present only while the sim is live in-memory. */
  max_turns?: number;
}

// ── Streaming ───────────────────────────────────────────────────────────────

export interface SimulationMessage {
  role: SimulationRole;
  content: string;
}

// ── Evaluation / Judge ──────────────────────────────────────────────────────

/** Matches JudgeResult.to_dict — rubric-driven score map, not a fixed field set. */
export interface JudgeResult {
  model: string;
  scores: Record<string, number | null>;
  justification: string | null;
}

export interface Evaluation {
  id: number | null;
  simulation_id: string;
  experiment_id: string | null;
  created_at: string | null;
  judge_results: JudgeResult[];
}

/** Mean of a given rubric key across the evaluation's judge_results. */
export function meanScore(ev: Evaluation, key: string): number | null {
  const vals = ev.judge_results
    .map((j) => j.scores?.[key])
    .filter((v): v is number => typeof v === 'number');
  return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
}

/** Mean across every rubric key in the evaluation. Useful when no one key is canonical. */
export function meanOverallScore(ev: Evaluation): number | null {
  const vals: number[] = [];
  for (const j of ev.judge_results) {
    for (const v of Object.values(j.scores ?? {})) {
      if (typeof v === 'number') vals.push(v);
    }
  }
  return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
}

// ── App settings ────────────────────────────────────────────────────────────

export interface AppSettings {
  max_concurrent_simulations: number;
  max_concurrent_optimizations: number;
}

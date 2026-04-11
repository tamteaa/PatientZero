import type { Session, SessionDetail } from '@/types/chat';
import type {
  AgentProfile,
  AppSettings,
  CoverageReport,
  DoctorDistributionResponse,
  Evaluation,
  Experiment,
  ExperimentDetail,
  OptimizationTarget,
  OptimizationResult,
  OptimizeRequest,
  PatientDistributionResponse,
  Scenario,
  SimulationConfig,
  SimulationDetail,
  SimulationRole,
  SimulationSummary,
} from '@/types/simulation';
import { client, API_BASE } from './client';

// ── Sessions ────────────────────────────────────────────────────────────────

export async function createSession(model: string = 'mock:default'): Promise<Session> {
  const { data } = await client.post('/sessions', { model });
  return data;
}

export async function listSessions(): Promise<Session[]> {
  const { data } = await client.get('/sessions');
  return data;
}

export async function getSession(id: string): Promise<SessionDetail> {
  const { data } = await client.get(`/sessions/${id}`);
  return data;
}

export async function updateSessionModel(id: string, model: string): Promise<Session> {
  const { data } = await client.patch(`/sessions/${id}`, { model });
  return data;
}

export async function deleteSession(id: string): Promise<void> {
  await client.delete(`/sessions/${id}`);
}

// ── Models / Personas / Doctors / Scenarios / Styles ────────────────────────

export async function listModels(): Promise<string[]> {
  const { data } = await client.get('/models');
  return data;
}

export async function getSettings(): Promise<AppSettings> {
  const { data } = await client.get('/settings');
  return data;
}

// ── Experiments ─────────────────────────────────────────────────────────────

export async function listExperiments(): Promise<Experiment[]> {
  const { data } = await client.get('/experiments');
  return data;
}

export async function createExperiment(name: string): Promise<Experiment> {
  const { data } = await client.post('/experiments', { name });
  return data;
}

export async function getExperiment(id: string): Promise<ExperimentDetail> {
  const { data } = await client.get(`/experiments/${id}`);
  return data;
}

export async function deleteExperiment(id: string): Promise<void> {
  await client.delete(`/experiments/${id}`);
}

export async function getExperimentCoverage(
  id: string,
  params?: { target_method?: 'monte_carlo' | 'independence'; mc_samples?: number },
): Promise<CoverageReport> {
  const { data } = await client.get(`/experiments/${id}/coverage`, { params });
  return data;
}

export interface PatchExperimentRequest {
  sampling_seed?: number | null;
  reset_sample_draw_index?: boolean;
}

export async function patchExperiment(
  id: string,
  body: PatchExperimentRequest,
): Promise<ExperimentDetail> {
  const { data } = await client.patch(`/experiments/${id}`, body);
  return data;
}

export async function optimizeExperiment(
  id: string,
  request: OptimizeRequest = {},
): Promise<OptimizationResult> {
  const { data } = await client.post(`/experiments/${id}/optimize`, request);
  return data;
}

export async function listOptimizationTargets(experimentId: string): Promise<OptimizationTarget[]> {
  const { data } = await client.get(`/experiments/${experimentId}/optimization-targets`);
  return data;
}

export async function setCurrentOptimizationTarget(
  experimentId: string,
  optimizationTargetId: string,
): Promise<ExperimentDetail> {
  const { data } = await client.post(`/experiments/${experimentId}/optimization-target/current`, {
    optimization_target_id: optimizationTargetId,
  });
  return data;
}

// ── Distributions ───────────────────────────────────────────────────────────

export async function getPatientDistribution(): Promise<PatientDistributionResponse> {
  const { data } = await client.get('/distributions/patient');
  return data;
}

export async function getDoctorDistribution(): Promise<DoctorDistributionResponse> {
  const { data } = await client.get('/distributions/doctor');
  return data;
}

export async function listPersonas(): Promise<AgentProfile[]> {
  const { data } = await client.get('/personas');
  return data;
}

export async function listDoctors(): Promise<AgentProfile[]> {
  const { data } = await client.get('/doctors');
  return data;
}

export async function listScenarios(): Promise<Scenario[]> {
  const { data } = await client.get('/scenarios');
  return data;
}

export async function listStyles(): Promise<string[]> {
  const { data } = await client.get('/styles');
  return data;
}

// ── Simulations ─────────────────────────────────────────────────────────────

export async function listSimulations(): Promise<SimulationSummary[]> {
  const { data } = await client.get('/simulations');
  return data;
}

export async function getSimulation(id: string): Promise<SimulationDetail> {
  const { data } = await client.get(`/simulations/${id}`);
  return data;
}

export async function deleteSimulation(id: string): Promise<void> {
  await client.delete(`/simulations/${id}`);
}

export async function pauseSimulation(id: string): Promise<void> {
  await client.post(`/simulations/${id}/pause`);
}

export async function resumeSimulation(id: string): Promise<void> {
  await client.post(`/simulations/${id}/resume`);
}

export async function stopSimulation(id: string): Promise<void> {
  await client.post(`/simulations/${id}/stop`);
}

export async function evaluateSimulation(id: string, model: string): Promise<Evaluation> {
  const { data } = await client.post(`/simulations/${id}/evaluate`, { model });
  return data;
}

export async function getSimulationEvaluation(id: string): Promise<Evaluation | null> {
  const { data } = await client.get(`/simulations/${id}/evaluation`);
  return data;
}

export async function listEvaluations(): Promise<Evaluation[]> {
  const { data } = await client.get('/evaluations');
  return data;
}

export async function getAnalysis(): Promise<AnalysisResult> {
  const { data } = await client.get('/analysis');
  return data;
}

export interface MetricStats {
  mean: number | null;
  std: number | null;
  n: number;
}

export interface ScoreStats {
  comprehension_score: MetricStats;
  factual_recall: MetricStats;
  applied_reasoning: MetricStats;
  explanation_quality: MetricStats;
  interaction_quality: MetricStats;
}

export type MetricKey = keyof ScoreStats;

export interface EffectSizeTriple {
  high_vs_low: number | null;
  high_vs_moderate: number | null;
  moderate_vs_low: number | null;
}

export interface VerbosityEffectTriple {
  thorough_vs_terse: number | null;
  thorough_vs_moderate: number | null;
  moderate_vs_terse: number | null;
}

export interface GapGroupStats {
  rate: number;
  n: number;
  n_gap: number;
}

export interface GapAnalysis {
  total_with_gap: number;
  gap_rate: number;
  by_literacy: Record<string, GapGroupStats>;
  by_scenario: Record<string, GapGroupStats>;
  by_doctor_empathy: Record<string, GapGroupStats>;
}

export interface WorstCombo {
  patient_literacy: string;
  doctor_empathy: string;
  doctor_verbosity: string;
  scenario: string;
  mean_comprehension: number;
  scores: ScoreStats;
  n: number;
}

export interface AnalysisResult {
  total_evaluations: number;
  overall: ScoreStats;
  by_patient_literacy: Record<string, ScoreStats>;
  by_patient_anxiety: Record<string, ScoreStats>;
  by_patient_age: Record<string, ScoreStats>;
  by_doctor_empathy: Record<string, ScoreStats>;
  by_doctor_verbosity: Record<string, ScoreStats>;
  by_doctor_comprehension_checking: Record<string, ScoreStats>;
  by_scenario: Record<string, ScoreStats>;
  by_style?: Record<string, ScoreStats>;
  by_policy_version?: Record<string, ScoreStats>;
  by_experiment_id?: Record<string, ScoreStats>;
  by_optimization_target_id?: Record<string, ScoreStats>;
  effect_sizes: Record<string, Record<MetricKey, EffectSizeTriple | VerbosityEffectTriple>>;
  gap_analysis: GapAnalysis;
  worst_combinations: WorstCombo[];
}

// ── Chat SSE ────────────────────────────────────────────────────────────────

export async function sendMessage(
  sessionId: string,
  message: string,
  onToken: (token: string) => void,
  onDone: () => void,
  onError?: (error: string) => void,
) {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  });

  if (!response.ok) {
    const text = await response.text().catch(() => 'Unknown error');
    throw new Error(`Chat request failed (${response.status}): ${text}`);
  }

  const reader = response.body?.getReader();
  if (!reader) return;

  const decoder = new TextDecoder();
  let buffer = '';
  let currentEvent = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('event:')) {
        currentEvent = line.slice(6).trim();
        continue;
      }
      if (line.startsWith('data:')) {
        const raw = line.slice(5).trim();
        if (!raw) continue;
        try {
          const parsed = JSON.parse(raw);
          if (currentEvent === 'error') {
            onError?.(parsed.error ?? 'Unknown error');
            onDone();
            return;
          }
          if (parsed.token) onToken(parsed.token);
        } catch {
          // skip non-JSON data lines
        }
        currentEvent = '';
      }
      if (line.startsWith('event: done')) {
        onDone();
        return;
      }
    }
  }
  onDone();
}

// ── Simulation ──────────────────────────────────────────────────────────────

export async function startSimulation(config: SimulationConfig): Promise<string> {
  const { data } = await client.post('/simulate', config);
  return data.simulation_id;
}

export interface SimulationStreamCallbacks {
  onTurnStart?: (role: SimulationRole, turn: number) => void;
  onToken?: (token: string) => void;
  onTurnEnd?: (role: SimulationRole, turn: number) => void;
  onDone?: () => void;
}

export function subscribeToSimulation(
  simId: string,
  callbacks: SimulationStreamCallbacks,
  signal?: AbortSignal,
): void {
  const url = `${API_BASE}/simulations/${simId}/stream`;

  fetch(url, { signal }).then(async (response) => {
    const reader = response.body?.getReader();
    if (!reader) return;

    const decoder = new TextDecoder();
    let buffer = '';
    let currentEvent = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('event:')) {
          currentEvent = line.slice(6).trim();
          continue;
        }
        if (line.startsWith('data:')) {
          const raw = line.slice(5).trim();
          if (!raw) continue;
          try {
            const parsed = JSON.parse(raw);
            if (currentEvent === 'turn_start') {
              callbacks.onTurnStart?.(parsed.role as SimulationRole, parsed.turn);
            } else if (currentEvent === 'turn_end') {
              callbacks.onTurnEnd?.(parsed.role as SimulationRole, parsed.turn);
            } else if (currentEvent === 'done') {
              callbacks.onDone?.();
              return;
            } else if (parsed.token !== undefined) {
              callbacks.onToken?.(parsed.token);
            }
          } catch { /* skip */ }
          currentEvent = '';
        }
      }
    }
    callbacks.onDone?.();
  }).catch(() => {});
}

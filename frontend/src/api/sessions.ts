import type { Session, SessionDetail } from '@/types/chat';
import type {
  AgentDistributionResponse,
  AppSettings,
  CoverageReport,
  Evaluation,
  Experiment,
  OptimizationResult,
  OptimizationTarget,
  OptimizeRequest,
  SimulationDetail,
  SimulationRole,
  SimulationSummary,
  StartSimulationRequest,
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

// ── Models / settings ───────────────────────────────────────────────────────

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

export async function listExperimentSimulations(experimentId: string): Promise<SimulationSummary[]> {
  const { data } = await client.get(`/experiments/${experimentId}/simulations`);
  return data;
}

export async function listExperimentEvaluations(experimentId: string): Promise<Evaluation[]> {
  const { data } = await client.get(`/experiments/${experimentId}/evaluations`);
  return data;
}

export async function getExperimentAnalysis(experimentId: string): Promise<AnalysisResult> {
  const { data } = await client.get(`/experiments/${experimentId}/analysis`);
  return data;
}

export interface PatchExperimentRequest {
  reset_sample_draw_index?: boolean;
}

export async function patchExperiment(
  id: string,
  body: PatchExperimentRequest,
): Promise<Experiment> {
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
): Promise<Experiment> {
  const { data } = await client.post(`/experiments/${experimentId}/optimization-target/current`, {
    optimization_target_id: optimizationTargetId,
  });
  return data;
}

// ── Distributions ───────────────────────────────────────────────────────────

export async function getAgentDistribution(
  experimentId: string,
  agentName: string,
): Promise<AgentDistributionResponse> {
  const { data } = await client.get(
    `/experiments/${experimentId}/distributions/${agentName}`,
  );
  return data;
}

// ── Experiment agents view ──────────────────────────────────────────────────

export interface ExperimentAgentsResponse {
  agents: Array<{ name: string; prompt: string; model: string | null }>;
  judge: { rubric: Record<string, string>; instructions: string; model: string | null };
}

export async function getExperimentAgents(experimentId: string): Promise<ExperimentAgentsResponse> {
  const { data } = await client.get(`/experiments/${experimentId}/agents`);
  return data;
}

// ── Simulations ─────────────────────────────────────────────────────────────

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

/** Backend ignores any body on evaluate — judge is derived from the experiment's config. */
export async function evaluateSimulation(id: string): Promise<Evaluation> {
  const { data } = await client.post(`/simulations/${id}/evaluate`);
  return data;
}

export async function getSimulationEvaluation(id: string): Promise<Evaluation | null> {
  const { data } = await client.get(`/simulations/${id}/evaluation`);
  return data;
}

// ── Analysis (per-experiment) ───────────────────────────────────────────────

export interface MetricStats {
  mean: number | null;
  std: number | null;
  n: number;
}

/** Map from rubric metric name → stats bucket. */
export type RubricStats = Record<string, MetricStats>;

/** Matches backend /experiments/{id}/analysis exactly. */
export interface AnalysisResult {
  total_evaluations: number;
  overall: RubricStats;
  /** Keyed as `${agent_name}.${trait_name}` → trait_value → per-metric stats. */
  by_trait: Record<string, Record<string, RubricStats>>;
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
  if (!reader) {
    onDone();
    return;
  }

  const decoder = new TextDecoder();
  let buffer = '';
  let currentEvent = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('event:')) {
          currentEvent = line.slice(6).trim();
          if (currentEvent === 'done') {
            onDone();
            return;
          }
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
            if (typeof parsed.token === 'string') onToken(parsed.token);
          } catch {
            // non-JSON data line, skip
          }
          currentEvent = '';
        }
      }
    }
  } finally {
    onDone();
  }
}

// ── Simulation streaming ────────────────────────────────────────────────────

export async function startSimulation(config: StartSimulationRequest): Promise<string> {
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
          if (currentEvent === 'done') {
            callbacks.onDone?.();
            return;
          }
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

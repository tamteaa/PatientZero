import type { Session, SessionDetail } from '@/types/chat';
import type { Evaluation, Persona, Scenario, SimulationConfig, SimulationDetail, SimulationRole, SimulationSummary } from '@/types/simulation';
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

// ── Models / Personas / Scenarios ───────────────────────────────────────────

export async function listModels(): Promise<string[]> {
  const { data } = await client.get('/models');
  return data;
}

export async function listPersonas(): Promise<Persona[]> {
  const { data } = await client.get('/personas');
  return data;
}

export async function listScenarios(): Promise<Scenario[]> {
  const { data } = await client.get('/scenarios');
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

// ── Batch run SSE ────────────────────────────────────────────────────────────

export interface BatchEvent {
  type: 'batch_start' | 'sim_start' | 'sim_skip' | 'sim_done' | 'batch_done';
  current?: number;
  total: number;
  persona?: string;
  scenario?: string;
  style?: string;
  mode?: string;
  sim_id?: string;
  state?: 'completed' | 'error';
  duration_ms?: number;
  error?: string;
  succeeded?: number;
  failed?: number;
  skipped?: number;
}

export async function runBatch(
  model: string,
  skipExisting: boolean,
  onEvent: (event: BatchEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE}/simulate/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model, skip_existing: skipExisting }),
    signal,
  });

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
          onEvent({ type: currentEvent as BatchEvent['type'], ...parsed });
        } catch { /* skip */ }
        currentEvent = '';
      }
    }
  }
}

// ── Chat SSE ────────────────────────────────────────────────────────────────

export async function sendMessage(
  sessionId: string,
  message: string,
  onToken: (token: string) => void,
  onDone: () => void,
) {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  });

  const reader = response.body?.getReader();
  if (!reader) return;

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data:')) {
        const raw = line.slice(5).trim();
        if (!raw) continue;
        try {
          const parsed = JSON.parse(raw);
          if (parsed.token) onToken(parsed.token);
        } catch {
          // skip non-JSON data lines
        }
      }
      if (line.startsWith('event: done')) {
        onDone();
        return;
      }
    }
  }
  onDone();
}

// ── Simulation SSE ──────────────────────────────────────────────────────────

export async function runSimulation(
  config: SimulationConfig,
  onTurnStart: (role: SimulationRole, turn: number, simulationId?: string) => void,
  onToken: (token: string) => void,
  onTurnEnd: (role: SimulationRole, turn: number) => void,
  onDone: (simulationId: string) => void,
) {
  const response = await fetch(`${API_BASE}/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });

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
            onTurnStart(parsed.role as SimulationRole, parsed.turn, parsed.simulation_id);
          } else if (currentEvent === 'turn_end') {
            onTurnEnd(parsed.role as SimulationRole, parsed.turn);
          } else if (currentEvent === 'done') {
            onDone(parsed.simulation_id);
            return;
          } else if (parsed.token !== undefined) {
            onToken(parsed.token);
          }
        } catch {
          // skip non-JSON
        }
        currentEvent = '';
      }
    }
  }
}

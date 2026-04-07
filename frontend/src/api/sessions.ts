import type { Session, SessionDetail } from '@/types/chat';
import type { AgentProfile, Evaluation, Scenario, SimulationConfig, SimulationDetail, SimulationRole, SimulationSummary } from '@/types/simulation';
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

  if (!response.ok) {
    const text = await response.text().catch(() => 'Unknown error');
    throw new Error(`Chat request failed (${response.status}): ${text}`);
  }

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

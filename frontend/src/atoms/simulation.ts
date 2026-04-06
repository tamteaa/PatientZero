import { atom } from 'jotai';
import type { SimulationDetail, SimulationMessage, SimulationRole } from '@/types/simulation';

// Current simulation detail from DB
export const simulationDetailAtom = atom<SimulationDetail | null>(null);

// Live state
export const simulationStatusAtom = atom<string>('idle');
export const simulationTextStatusAtom = atom<string>('');
export const simulationMessagesAtom = atom<SimulationMessage[]>([]);

// Streaming state
export const streamingRoleAtom = atom<SimulationRole | null>(null);
export const streamingContentAtom = atom<string>('');

// Derived
export const isSimulationActiveAtom = atom((get) => {
  const status = get(simulationStatusAtom);
  return status === 'running' || status === 'paused';
});

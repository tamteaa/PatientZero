import { atom } from 'jotai';
import type { ExperimentAgentsResponse } from '@/api/sessions';

/** Cache of the active experiment's agents, keyed by experiment id. */
export const agentsConfigAtom = atom<ExperimentAgentsResponse | null>(null);

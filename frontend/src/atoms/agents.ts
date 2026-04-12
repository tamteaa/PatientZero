import { atom } from 'jotai';
import type { AgentsConfig } from '@/types/agents';

export const agentsConfigAtom = atom<AgentsConfig | null>(null);

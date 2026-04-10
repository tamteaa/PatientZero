import { atom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import type { Experiment } from '@/types/simulation';

export const activeExperimentIdAtom = atomWithStorage<string | null>('pz.activeExperimentId', null);
export const experimentsAtom = atom<Experiment[]>([]);

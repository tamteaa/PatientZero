import { atom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import type { AppSettings } from '@/types/simulation';

export const globalModelAtom = atomWithStorage<string>('pz.globalModel', 'mock:default');
export const availableModelsAtom = atom<string[]>([]);
export const appSettingsAtom = atom<AppSettings | null>(null);

import { createContext, useContext, useRef, useState, useCallback, type ReactNode } from 'react';
import { runBatch } from '@/api/sessions';
import type { BatchEvent } from '@/api/sessions';

export interface BatchLogEntry {
  type: BatchEvent['type'];
  persona?: string;
  scenario?: string;
  style?: string;
  mode?: string;
  state?: string;
  error?: string;
}

interface BatchRunContextValue {
  batchRunning: boolean;
  batchDone: boolean;
  batchCurrent: number;
  batchTotal: number;
  batchLog: BatchLogEntry[];
  batchSummary: { succeeded: number; failed: number; skipped: number } | null;
  start: (model: string, onSimComplete?: () => void) => Promise<void>;
  cancel: () => void;
  dismiss: () => void;
}

const BatchRunContext = createContext<BatchRunContextValue | null>(null);

export function BatchRunProvider({ children }: { children: ReactNode }) {
  const [batchRunning, setBatchRunning] = useState(false);
  const [batchDone, setBatchDone] = useState(false);
  const [batchCurrent, setBatchCurrent] = useState(0);
  const [batchTotal, setBatchTotal] = useState(0);
  const [batchLog, setBatchLog] = useState<BatchLogEntry[]>([]);
  const [batchSummary, setBatchSummary] = useState<{ succeeded: number; failed: number; skipped: number } | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const start = useCallback(async (model: string, onSimComplete?: () => void) => {
    if (batchRunning) return;
    const abort = new AbortController();
    abortRef.current = abort;
    setBatchRunning(true);
    setBatchDone(false);
    setBatchLog([]);
    setBatchSummary(null);
    setBatchCurrent(0);
    setBatchTotal(0);

    try {
      await runBatch(
        model,
        true,
        (event) => {
          if (event.type === 'batch_start') {
            setBatchTotal(event.total);
          } else if (event.type === 'sim_start' || event.type === 'sim_skip') {
            setBatchCurrent(event.current ?? 0);
            setBatchLog((prev) => [...prev, {
              type: event.type,
              persona: event.persona,
              scenario: event.scenario,
              style: event.style,
              mode: event.mode,
            }]);
          } else if (event.type === 'sim_done') {
            setBatchCurrent(event.current ?? 0);
            setBatchLog((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last?.type === 'sim_start') {
                updated[updated.length - 1] = { ...last, type: 'sim_done', state: event.state, error: event.error };
              }
              return updated;
            });
            if (event.state === 'completed') onSimComplete?.();
          } else if (event.type === 'batch_done') {
            setBatchSummary({ succeeded: event.succeeded ?? 0, failed: event.failed ?? 0, skipped: event.skipped ?? 0 });
            setBatchDone(true);
            setBatchRunning(false);
            onSimComplete?.();
          }
        },
        abort.signal,
      );
    } catch {
      setBatchRunning(false);
    }
  }, [batchRunning]);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setBatchRunning(false);
    setBatchDone(true);
  }, []);

  const dismiss = useCallback(() => {
    setBatchDone(false);
    setBatchLog([]);
    setBatchSummary(null);
  }, []);

  return (
    <BatchRunContext.Provider value={{
      batchRunning, batchDone, batchCurrent, batchTotal,
      batchLog, batchSummary, start, cancel, dismiss,
    }}>
      {children}
    </BatchRunContext.Provider>
  );
}

export function useBatchRun() {
  const ctx = useContext(BatchRunContext);
  if (!ctx) throw new Error('useBatchRun must be used inside BatchRunProvider');
  return ctx;
}
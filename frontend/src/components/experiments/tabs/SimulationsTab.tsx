import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAtomValue } from 'jotai';
import { Button } from '@/components/ui/button';
import { FlaskConical, Loader2, Play, Trash2 } from 'lucide-react';
import {
  deleteSimulation,
  evaluateSimulation,
  listExperimentEvaluations,
  listExperimentSimulations,
  startSimulation,
} from '@/api/sessions';
import { globalModelAtom } from '@/atoms/model';
import { useError } from '@/contexts/ErrorContext';
import type { Evaluation, SimulationSummary } from '@/types/simulation';
import { meanOverallScore } from '@/types/simulation';

interface Props {
  experimentId: string;
  refreshKey: number;
  onRefresh: () => void;
}

function summarizeProfiles(profiles: Record<string, Record<string, string>>): string {
  const parts: string[] = [];
  for (const [agent, traits] of Object.entries(profiles ?? {})) {
    const traitSummary = Object.entries(traits).slice(0, 2).map(([k, v]) => `${k}=${v}`).join(',');
    parts.push(traitSummary ? `${agent}(${traitSummary})` : agent);
  }
  return parts.join(' · ');
}

export function SimulationsTab({ experimentId, refreshKey, onRefresh }: Props) {
  const navigate = useNavigate();
  const model = useAtomValue(globalModelAtom);
  const { handleError } = useError();
  const [allSimulations, setAllSimulations] = useState<SimulationSummary[]>([]);
  const [allEvaluations, setAllEvaluations] = useState<Evaluation[]>([]);
  const [launching, setLaunching] = useState(false);
  const [evaluating, setEvaluating] = useState<Set<string>>(new Set());

  const refresh = useCallback(async () => {
    try {
      const [sims, evals] = await Promise.all([
        listExperimentSimulations(experimentId),
        listExperimentEvaluations(experimentId),
      ]);
      setAllSimulations(sims);
      setAllEvaluations(evals);
    } catch (err) {
      handleError(err, 'Failed to reload simulations');
    }
  }, [experimentId, handleError]);

  useEffect(() => {
    refresh();
  }, [refresh, refreshKey]);

  const handleRun = useCallback(async () => {
    if (!model || launching) return;
    setLaunching(true);
    try {
      await startSimulation({ experiment_id: experimentId, model });
      onRefresh();
    } catch (err) {
      handleError(err, 'Failed to start simulation');
    } finally {
      setLaunching(false);
    }
  }, [model, launching, experimentId, onRefresh, handleError]);

  const handleEvaluate = useCallback(async (simId: string) => {
    setEvaluating((prev) => new Set(prev).add(simId));
    try {
      const result = await evaluateSimulation(simId);
      setAllEvaluations((prev) => {
        const filtered = prev.filter((e) => e.simulation_id !== simId);
        return [result, ...filtered];
      });
    } catch (err) {
      handleError(err, 'Evaluation failed');
    } finally {
      setEvaluating((prev) => {
        const next = new Set(prev);
        next.delete(simId);
        return next;
      });
    }
  }, [handleError]);

  const handleDeleteSim = useCallback(async (simId: string) => {
    try {
      await deleteSimulation(simId);
      setAllSimulations((prev) => prev.filter((s) => s.id !== simId));
    } catch (err) {
      handleError(err, 'Failed to delete simulation');
    }
  }, [handleError]);

  const simulations = useMemo(
    () => allSimulations.filter((s) => s.config.experiment_id === experimentId),
    [allSimulations, experimentId],
  );
  const simIds = useMemo(() => new Set(simulations.map((s) => s.id)), [simulations]);
  const evalBySim = useMemo(() => {
    const map = new Map<string, Evaluation>();
    for (const e of allEvaluations) {
      if (simIds.has(e.simulation_id) && !map.has(e.simulation_id)) {
        map.set(e.simulation_id, e);
      }
    }
    return map;
  }, [allEvaluations, simIds]);

  const inProgress = simulations.filter((s) => s.state === 'running' || s.state === 'pending');
  const finished = simulations.filter((s) => s.state === 'completed' || s.state === 'error');

  const renderRow = (sim: SimulationSummary) => {
    const isEvaluating = evaluating.has(sim.id);
    const ev = evalBySim.get(sim.id);
    const score = ev ? meanOverallScore(ev) : null;
    const hasEval = ev != null;
    const canEval = sim.state === 'completed';
    const isError = sim.state === 'error';
    const isRunning = sim.state === 'running' || sim.state === 'pending';
    const label = summarizeProfiles(sim.config.profiles) || sim.id.slice(0, 8);
    const modelLabel = sim.config.model;

    return (
      <div
        key={sim.id}
        className="group flex items-center gap-3 px-3 py-2 border-b border-border last:border-b-0 hover:bg-muted/40 transition-colors"
      >
        <div className="flex items-center gap-2 shrink-0">
          {isRunning ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin text-blue-500" />
          ) : isError ? (
            <span className="h-2 w-2 rounded-full bg-red-500" />
          ) : (
            <span className="h-2 w-2 rounded-full bg-green-500" />
          )}
        </div>
        <button
          className="flex-1 min-w-0 text-left"
          onClick={() => navigate(`/simulations/${sim.id}`)}
        >
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-sm font-medium truncate">{label}</span>
            <span className="text-xs text-muted-foreground truncate">· {modelLabel}</span>
          </div>
        </button>
        <div className="shrink-0 w-16 text-right tabular-nums">
          {score != null ? (
            <span className="text-sm font-medium">{score.toFixed(1)}</span>
          ) : isError ? (
            <span className="text-xs text-red-500">error</span>
          ) : (
            <span className="text-xs text-muted-foreground">—</span>
          )}
        </div>
        <div className="shrink-0 flex items-center gap-1">
          {!isRunning && (
            <Button
              size="sm"
              variant={hasEval ? 'outline' : 'default'}
              className="h-7 text-xs gap-1"
              disabled={!canEval || isEvaluating}
              onClick={(e) => { e.stopPropagation(); handleEvaluate(sim.id); }}
            >
              {isEvaluating ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <><FlaskConical className="h-3 w-3" /> {hasEval ? 'Re-eval' : 'Evaluate'}</>
              )}
            </Button>
          )}
          <Button
            size="sm"
            variant="ghost"
            className="h-7 w-7 p-0 text-muted-foreground hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={(e) => { e.stopPropagation(); handleDeleteSim(sim.id); }}
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3 rounded-md border border-border bg-card px-4 py-3">
        <div className="flex flex-col min-w-0">
          <span className="text-sm font-medium">Run a simulation</span>
          <span className="text-xs text-muted-foreground truncate">
            Samples from this experiment's target distribution using{' '}
            <span className="font-mono text-foreground">{model ?? 'no model'}</span>
          </span>
        </div>
        <Button
          className="gap-1.5 h-9 shrink-0"
          disabled={launching || !model}
          onClick={handleRun}
        >
          {launching ? (
            <><Loader2 className="h-4 w-4 animate-spin" /> Running…</>
          ) : (
            <><Play className="h-4 w-4" /> Run</>
          )}
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <section className="min-w-0">
          <div className="flex items-baseline justify-between mb-2 px-1">
            <h3 className="text-[11px] uppercase tracking-wide text-muted-foreground font-semibold">
              In progress
            </h3>
            <span className="text-[11px] text-muted-foreground tabular-nums">
              {inProgress.length}
            </span>
          </div>
          <div className="rounded-md border border-border bg-card overflow-hidden">
            {inProgress.length === 0 ? (
              <p className="text-xs text-muted-foreground px-3 py-4 text-center">
                Nothing running right now.
              </p>
            ) : (
              inProgress.map(renderRow)
            )}
          </div>
        </section>

        <section className="min-w-0">
          <div className="flex items-baseline justify-between mb-2 px-1">
            <h3 className="text-[11px] uppercase tracking-wide text-muted-foreground font-semibold">
              Completed
            </h3>
            <span className="text-[11px] text-muted-foreground tabular-nums">
              {finished.length}
            </span>
          </div>
          <div className="rounded-md border border-border bg-card overflow-hidden">
            {finished.length === 0 ? (
              <p className="text-xs text-muted-foreground px-3 py-4 text-center">
                No completed simulations yet.
              </p>
            ) : (
              finished.slice(0, 20).map(renderRow)
            )}
          </div>
          {finished.length > 20 && (
            <p className="text-[11px] text-muted-foreground text-right mt-1 px-1 tabular-nums">
              Showing 20 of {finished.length}
            </p>
          )}
        </section>
      </div>
    </div>
  );
}

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAtomValue } from 'jotai';
import { useError } from '@/contexts/ErrorContext';
import { Header } from '@/components/common/Header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Play, Loader2, FlaskConical } from 'lucide-react';
import { listSimulations, listEvaluations, startSimulation, getExperimentCoverage, evaluateSimulation } from '@/api/sessions';
import { activeExperimentIdAtom, experimentsAtom } from '@/atoms/experiment';
import { globalModelAtom } from '@/atoms/model';
import type { CoverageReport, Evaluation, SimulationSummary } from '@/types/simulation';
import { meanScore } from '@/types/simulation';

const STATUS_COLORS: Record<string, string> = {
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  running: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  error: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
};


function Stat({
  label,
  value,
  sub,
  onClick,
}: {
  label: string;
  value: string | number;
  sub?: string;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!onClick}
      className={`flex flex-col text-left rounded-md p-3 ${onClick ? 'cursor-pointer hover:bg-muted/40 transition-colors' : ''}`}
    >
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-2xl font-semibold tabular-nums mt-0.5">{value}</p>
      {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
    </button>
  );
}


export function DashboardPage() {
  const navigate = useNavigate();
  const { handleError } = useError();
  const activeExperimentId = useAtomValue(activeExperimentIdAtom);
  const experiments = useAtomValue(experimentsAtom);
  const model = useAtomValue(globalModelAtom);
  const [allSimulations, setAllSimulations] = useState<SimulationSummary[]>([]);
  const [allEvaluations, setAllEvaluations] = useState<Evaluation[]>([]);
  const [coverage, setCoverage] = useState<CoverageReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [launching, setLaunching] = useState(false);
  const [evaluating, setEvaluating] = useState<Set<string>>(new Set());

  const refreshSimulations = useCallback(async () => {
    try {
      const sims = await listSimulations();
      setAllSimulations(sims);
      if (activeExperimentId) {
        const cov = await getExperimentCoverage(activeExperimentId, { mc_samples: 12_000 });
        setCoverage(cov);
      }
    } catch (err) {
      handleError(err, 'Failed to reload simulations');
    }
  }, [handleError, activeExperimentId]);

  useEffect(() => {
    Promise.all([
      listSimulations(),
      listEvaluations(),
    ])
      .then(([sims, evals]) => {
        setAllSimulations(sims);
        setAllEvaluations(evals);
      })
      .catch((err) => handleError(err, 'Failed to load dashboard data'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!activeExperimentId) {
      setCoverage(null);
      return;
    }
    getExperimentCoverage(activeExperimentId, { mc_samples: 12_000 })
      .then(setCoverage)
      .catch(() => setCoverage(null));
  }, [activeExperimentId]);

  const handleEvaluate = useCallback(async (simId: string) => {
    if (!model) return;
    setEvaluating((prev) => new Set(prev).add(simId));
    try {
      const result = await evaluateSimulation(simId, model);
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
  }, [model, handleError]);

  const handleRun = useCallback(async () => {
    if (!activeExperimentId || !model || launching) return;
    setLaunching(true);
    try {
      await startSimulation({ experiment_id: activeExperimentId, model });
      await refreshSimulations();
    } catch (err) {
      handleError(err, 'Failed to start simulation');
    } finally {
      setLaunching(false);
    }
  }, [activeExperimentId, model, launching, refreshSimulations, handleError]);

  const activeExperiment = experiments.find((e) => e.id === activeExperimentId) ?? null;

  // Scope everything to the active experiment
  const simulations = useMemo(
    () => allSimulations.filter((s) => s.experiment_id === activeExperimentId),
    [allSimulations, activeExperimentId]
  );

  const simIds = useMemo(() => new Set(simulations.map((s) => s.id)), [simulations]);

  const evaluations = useMemo(
    () => allEvaluations.filter((e) => simIds.has(e.simulation_id)),
    [allEvaluations, simIds]
  );

  const completed = simulations.filter((s) => s.state === 'completed');

  const evalMeans = evaluations
    .map((e) => meanScore(e, 'comprehension_score'))
    .filter((v): v is number => v != null);
  const avgComprehension = evalMeans.length > 0
    ? evalMeans.reduce((a, b) => a + b, 0) / evalMeans.length
    : null;

  const evaluatedSimIds = useMemo(() => new Set(evaluations.map((e) => e.simulation_id)), [evaluations]);

  const recentSims = simulations.slice(0, 10);
  const recentEvals = useMemo(() => {
    const simById = new Map(simulations.map((s) => [s.id, s]));
    return evaluations
      .filter((e) => simById.has(e.simulation_id))
      .slice(0, 10)
      .map((e) => ({ evaluation: e, sim: simById.get(e.simulation_id)! }));
  }, [evaluations, simulations]);

  if (loading) {
    return (
      <>
        <Header title="Dashboard" />
        <div className="flex flex-1 items-center justify-center text-muted-foreground text-sm">Loading…</div>
      </>
    );
  }

  if (!activeExperiment) {
    return (
      <>
        <Header title="Dashboard" />
        <div className="flex flex-1 items-center justify-center text-muted-foreground">
          <div className="text-center space-y-2">
            <p className="text-sm font-medium">No active experiment</p>
            <p className="text-xs">Create or select one to see its dashboard.</p>
            <Button size="sm" className="mt-2" onClick={() => navigate('/experiments')}>
              Go to Experiments
            </Button>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Header title="Dashboard">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>experiment:</span>
          <button
            className="font-medium text-foreground hover:underline"
            onClick={() => navigate('/experiments')}
          >
            {activeExperiment.name}
          </button>
        </div>
      </Header>
      <ScrollArea className="flex-1">
        <div className="p-6 max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* ── Left column: single overview panel ──────────────────────── */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Overview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              {/* Stats */}
              <div className="grid grid-cols-2 gap-2">
                <Stat
                  label="Simulations"
                  value={simulations.length}
                  sub={`${completed.length} completed`}
                  onClick={() => navigate('/simulations')}
                />
                <Stat
                  label="Evaluated"
                  value={evaluations.length}
                  sub={`of ${completed.length} completed`}
                  onClick={() => navigate('/judge')}
                />
                <Stat
                  label="Avg comprehension"
                  value={avgComprehension != null ? avgComprehension.toFixed(0) : '—'}
                  sub={evalMeans.length > 0 ? `from ${evalMeans.length} eval${evalMeans.length > 1 ? 's' : ''}` : 'no evals yet'}
                />
                <Stat
                  label="Completion rate"
                  value={simulations.length > 0 ? `${Math.round((completed.length / simulations.length) * 100)}%` : '—'}
                  sub={`${simulations.length - completed.length} not completed`}
                />
              </div>

              {/* Coverage */}
              <div className="border-t border-border pt-4 space-y-4">
                <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Coverage in this experiment
                </h3>
                {coverage && (
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">Distribution coverage</span>
                      <span className="tabular-nums font-medium text-foreground">
                        {(coverage.coverage_pct * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-2 bg-muted rounded overflow-hidden">
                      <div
                        className="h-full bg-primary/70 transition-all"
                        style={{ width: `${Math.min(100, coverage.coverage_pct * 100)}%` }}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {coverage.cells_hit} of {coverage.cells_total} cells hit ·{' '}
                      <span className="tabular-nums">
                        {coverage.simulations_counted} / {coverage.estimated_total_needed}
                      </span>{' '}
                      simulations toward full coverage
                      {coverage.target_method && (
                        <>
                          <br />
                          Target: {coverage.target_method}
                          {coverage.mc_samples != null && coverage.mc_samples > 0
                            ? ` · MC samples ${coverage.mc_samples.toLocaleString()}`
                            : ''}
                        </>
                      )}
                      {coverage.distribution_match != null && (
                        <>
                          <br />
                          Match to target (1 − TVD):{' '}
                          <span className="tabular-nums font-medium text-foreground">
                            {(coverage.distribution_match * 100).toFixed(1)}%
                          </span>
                        </>
                      )}
                    </p>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-xs text-muted-foreground">
                  <div className="flex justify-between">
                    <span>Distinct scenarios</span>
                    <span className="tabular-nums font-medium text-foreground">
                      {new Set(simulations.map((s) => s.scenario_name)).size}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Distinct patients</span>
                    <span className="tabular-nums font-medium text-foreground">
                      {new Set(simulations.map((s) => s.persona_name)).size}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Distinct models</span>
                    <span className="tabular-nums font-medium text-foreground">
                      {new Set(simulations.map((s) => s.model)).size}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Errored runs</span>
                    <span className="tabular-nums font-medium text-foreground">
                      {simulations.filter((s) => s.state === 'error').length}
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
          {/* ── Right column: run + lists ───────────────────────────────── */}
          <div className="space-y-4">
            {/* Run next simulation */}
            <Card>
              <CardContent className="py-4 flex items-center justify-between">
                <div className="flex flex-col gap-0.5">
                  <span className="text-sm font-medium">Run next simulation</span>
                  <span className="text-xs text-muted-foreground">
                    Samples from this experiment's target distribution using <span className="font-mono">{model}</span>.
                  </span>
                </div>
                <Button
                  size="sm"
                  className="gap-1.5 h-9"
                  disabled={launching || !model}
                  onClick={handleRun}
                >
                  {launching ? (
                    <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Running…</>
                  ) : (
                    <><Play className="h-3.5 w-3.5" /> Run</>
                  )}
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Simulations</CardTitle>
              </CardHeader>
              <CardContent className="space-y-1.5">
                {recentSims.length === 0 ? (
                  <p className="text-xs text-muted-foreground py-2">No simulations yet.</p>
                ) : (
                  recentSims.map((sim) => {
                    const isEvaluating = evaluating.has(sim.id);
                    const hasEval = evaluatedSimIds.has(sim.id);
                    const canEval = sim.state === 'completed';
                    return (
                      <div
                        key={sim.id}
                        className="flex items-center justify-between gap-2 rounded-md px-2 py-1.5 hover:bg-muted/40 transition-colors"
                      >
                        <button
                          className="flex flex-col gap-0.5 min-w-0 text-left flex-1"
                          onClick={() => navigate(`/simulations/${sim.id}`)}
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <span className="text-sm font-medium truncate">{sim.persona_name}</span>
                            <Badge className={`${STATUS_COLORS[sim.state] ?? ''} text-xs px-1.5 py-0 shrink-0`}>
                              {sim.state}
                            </Badge>
                          </div>
                          <span className="text-xs text-muted-foreground truncate">{sim.scenario_name}</span>
                        </button>
                        <Button
                          size="sm"
                          variant={hasEval ? 'outline' : 'default'}
                          className="h-7 text-xs gap-1 shrink-0"
                          disabled={!canEval || isEvaluating || !model}
                          onClick={() => handleEvaluate(sim.id)}
                        >
                          {isEvaluating ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <><FlaskConical className="h-3 w-3" /> {hasEval ? 'Re-eval' : 'Evaluate'}</>
                          )}
                        </Button>
                      </div>
                    );
                  })
                )}
                {simulations.length > 10 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full text-xs text-muted-foreground mt-1"
                    onClick={() => navigate('/simulations')}
                  >
                    View all {simulations.length}
                  </Button>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Evaluations</CardTitle>
              </CardHeader>
              <CardContent className="space-y-1.5">
                {recentEvals.length === 0 ? (
                  <p className="text-xs text-muted-foreground py-2">No evaluations yet.</p>
                ) : (
                  recentEvals.map(({ evaluation, sim }) => {
                    const score = meanScore(evaluation, 'comprehension_score');
                    return (
                      <button
                        key={evaluation.id ?? sim.id}
                        className="w-full flex items-center justify-between gap-2 rounded-md px-2 py-1.5 hover:bg-muted/40 transition-colors text-left"
                        onClick={() => navigate('/judge')}
                      >
                        <div className="flex flex-col gap-0.5 min-w-0">
                          <span className="text-sm font-medium truncate">{sim.persona_name}</span>
                          <span className="text-xs text-muted-foreground truncate">{sim.scenario_name}</span>
                        </div>
                        <Badge className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-xs px-1.5 py-0 shrink-0 tabular-nums">
                          {score != null ? score.toFixed(0) : '—'}
                        </Badge>
                      </button>
                    );
                  })
                )}
              </CardContent>
            </Card>
          </div>

        </div>
      </ScrollArea>
    </>
  );
}

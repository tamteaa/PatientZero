import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Play, Loader2, Trash2, ListVideo, X, CheckCircle2, AlertCircle, SkipForward } from 'lucide-react';
import {
  runSimulation,
  listModels,
  listPersonas,
  listScenarios,
  listSimulations,
  deleteSimulation,
} from '@/api/sessions';
import { useBatchRun } from '@/contexts/BatchRunContext';
import type {
  Persona,
  Scenario,
  SimulationSummary,
  Style,
  Mode,
} from '@/types/simulation';

const conditions: { id: string; label: string; style: Style; mode: Mode }[] = [
  { id: 'clinical-static', label: 'Clinical + Static', style: 'clinical', mode: 'static' },
  { id: 'clinical-dialog', label: 'Clinical + Dialog', style: 'clinical', mode: 'dialog' },
  { id: 'analogy-static', label: 'Analogy + Static', style: 'analogy', mode: 'static' },
  { id: 'analogy-dialog', label: 'Analogy + Dialog', style: 'analogy', mode: 'dialog' },
];

const statusColor: Record<string, string> = {
  running: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  error: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
};

export function SimulationsPage() {
  const navigate = useNavigate();
  const batch = useBatchRun();

  const [personas, setPersonas] = useState<Persona[]>([]);
  const [scenariosList, setScenariosList] = useState<Scenario[]>([]);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [simulations, setSimulations] = useState<SimulationSummary[]>([]);

  const [personaIdx, setPersonaIdx] = useState<number>(0);
  const [conditionIdx, setConditionIdx] = useState<number>(0);
  const [scenarioIdx, setScenarioIdx] = useState<number>(0);
  const [model, setModel] = useState<string>('');
  const [maxTurns, setMaxTurns] = useState<string>('');
  const [isLaunching, setIsLaunching] = useState(false);

  const logEndRef = useRef<HTMLDivElement | null>(null);

  // Filter state
  const [filterPersona, setFilterPersona] = useState('');
  const [filterScenario, setFilterScenario] = useState('');
  const [filterCondition, setFilterCondition] = useState('');
  const [filterModel, setFilterModel] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  const fetchSimulations = useCallback(() => {
    listSimulations().then(setSimulations).catch(() => {});
  }, []);

  useEffect(() => {
    listPersonas().then(setPersonas).catch(() => {});
    listScenarios().then(setScenariosList).catch(() => {});
    listModels().then((models) => {
      setAvailableModels(models);
      if (models.length > 0 && !model) setModel(models[0]);
    }).catch(() => {});
    fetchSimulations();
  }, []);

  // Poll while batch is running or there are running simulations
  const hasRunning = simulations.some((s) => s.state === 'running');
  useEffect(() => {
    if (!batch.batchRunning && !hasRunning) return;
    const id = setInterval(fetchSimulations, 2000);
    return () => clearInterval(id);
  }, [batch.batchRunning, hasRunning, fetchSimulations]);

  // Scroll log to bottom on new entries
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [batch.batchLog.length]);

  const selectedCondition = conditions[conditionIdx];
  const defaultTurns = selectedCondition.mode === 'static' ? 2 : 8;

  const handleRun = useCallback(async () => {
    if (personas.length === 0 || scenariosList.length === 0) return;

    const condition = conditions[conditionIdx];
    const parsedMaxTurns = maxTurns ? parseInt(maxTurns, 10) : undefined;
    const config = {
      persona: personas[personaIdx],
      style: condition.style,
      mode: condition.mode,
      scenario: scenariosList[scenarioIdx],
      model,
      ...(parsedMaxTurns && !isNaN(parsedMaxTurns) ? { max_turns: parsedMaxTurns } : {}),
    };

    setIsLaunching(true);

    try {
      let navigated = false;
      await runSimulation(
        config,
        (_role, _turn, simId) => {
          if (!navigated && simId) {
            navigated = true;
            navigate(`/simulations/${simId}`);
          }
        },
        (_token) => {},
        (_role, _turn) => {},
        (_simulationId) => {
          setIsLaunching(false);
          fetchSimulations();
        },
      );
    } catch {
      setIsLaunching(false);
    }
  }, [personas, scenariosList, personaIdx, conditionIdx, scenarioIdx, model, maxTurns, navigate, fetchSimulations]);

  const handleDelete = useCallback(async (id: string) => {
    try {
      await deleteSimulation(id);
      fetchSimulations();
    } catch {
      alert('Failed to delete simulation. Please try again.');
    }
  }, [fetchSimulations]);

  const handleRunAll = useCallback(() => {
    batch.start(model, fetchSimulations);
  }, [model, batch, fetchSimulations]);

  const dataLoaded = personas.length > 0 && scenariosList.length > 0;

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 max-w-5xl mx-auto space-y-6">

          {/* New simulation card */}
          <Card>
            <CardContent className="pt-5 pb-4">
              <h3 className="text-sm font-semibold mb-3">New Simulation</h3>
              <div className="flex items-end gap-3 flex-wrap">
                <div className="flex flex-col gap-1">
                  <label className="text-xs text-muted-foreground">Persona</label>
                  <Select value={String(personaIdx)} onValueChange={(v) => setPersonaIdx(Number(v))}>
                    <SelectTrigger className="w-44 h-9 text-xs"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {personas.map((p, i) => (
                        <SelectItem key={i} value={String(i)}>{p.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex flex-col gap-1">
                  <label className="text-xs text-muted-foreground">Scenario</label>
                  <Select value={String(scenarioIdx)} onValueChange={(v) => setScenarioIdx(Number(v))}>
                    <SelectTrigger className="w-52 h-9 text-xs"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {scenariosList.map((s, i) => (
                        <SelectItem key={i} value={String(i)}>{s.test_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex flex-col gap-1">
                  <label className="text-xs text-muted-foreground">Condition</label>
                  <Select value={String(conditionIdx)} onValueChange={(v) => setConditionIdx(Number(v))}>
                    <SelectTrigger className="w-40 h-9 text-xs"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {conditions.map((c, i) => (
                        <SelectItem key={i} value={String(i)}>{c.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex flex-col gap-1">
                  <label className="text-xs text-muted-foreground">Model</label>
                  <Select value={model} onValueChange={(v) => { if (v) setModel(v); }}>
                    <SelectTrigger className="w-40 h-9 text-xs"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {availableModels.map((m) => (
                        <SelectItem key={m} value={m}>{m}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex flex-col gap-1">
                  <label className="text-xs text-muted-foreground">Max turns</label>
                  <Input
                    type="number"
                    min={1}
                    max={20}
                    placeholder={String(defaultTurns)}
                    value={maxTurns}
                    onChange={(e) => setMaxTurns(e.target.value)}
                    className="w-20 h-9 text-xs"
                  />
                </div>

                <Button onClick={handleRun} disabled={isLaunching || batch.batchRunning || !dataLoaded} size="sm" className="gap-1.5 h-9">
                  {isLaunching ? (
                    <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Running...</>
                  ) : (
                    <><Play className="h-3.5 w-3.5" /> Run</>
                  )}
                </Button>
                <Button
                  onClick={handleRunAll}
                  disabled={batch.batchRunning || isLaunching || !dataLoaded}
                  size="sm"
                  variant="outline"
                  className="gap-1.5 h-9"
                >
                  {batch.batchRunning ? (
                    <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Running all...</>
                  ) : (
                    <><ListVideo className="h-3.5 w-3.5" /> Run All (144)</>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Batch progress card */}
          {(batch.batchRunning || batch.batchDone) && (
            <Card>
              <CardContent className="pt-4 pb-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold">Batch Run</span>
                    {batch.batchTotal > 0 && (
                      <span className="text-xs text-muted-foreground tabular-nums">
                        {batch.batchCurrent} / {batch.batchTotal}
                      </span>
                    )}
                    {batch.batchSummary && (
                      <span className="text-xs text-muted-foreground">
                        — {batch.batchSummary.succeeded} ok · {batch.batchSummary.failed} failed · {batch.batchSummary.skipped} skipped
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {batch.batchRunning && (
                      <Button size="sm" variant="ghost" className="h-7 text-xs gap-1 text-muted-foreground" onClick={batch.cancel}>
                        <X className="h-3 w-3" /> Stop
                      </Button>
                    )}
                    {batch.batchDone && (
                      <Button size="sm" variant="ghost" className="h-7 text-xs gap-1 text-muted-foreground" onClick={batch.dismiss}>
                        <X className="h-3 w-3" /> Close
                      </Button>
                    )}
                  </div>
                </div>

                {batch.batchTotal > 0 && (
                  <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden mb-3">
                    <div
                      className="h-full bg-primary rounded-full transition-all"
                      style={{ width: `${(batch.batchCurrent / batch.batchTotal) * 100}%` }}
                    />
                  </div>
                )}

                <div className="max-h-48 overflow-y-auto space-y-1 text-xs font-mono">
                  {batch.batchLog.map((entry, i) => (
                    <div key={i} className="flex items-center gap-2">
                      {entry.type === 'sim_done' && entry.state === 'completed' && (
                        <CheckCircle2 className="h-3 w-3 text-green-500 shrink-0" />
                      )}
                      {entry.type === 'sim_done' && entry.state === 'error' && (
                        <AlertCircle className="h-3 w-3 text-red-500 shrink-0" />
                      )}
                      {entry.type === 'sim_skip' && (
                        <SkipForward className="h-3 w-3 text-muted-foreground shrink-0" />
                      )}
                      {entry.type === 'sim_start' && (
                        <Loader2 className="h-3 w-3 text-blue-500 animate-spin shrink-0" />
                      )}
                      <span className={
                        entry.type === 'sim_done' && entry.state === 'error' ? 'text-red-500'
                        : entry.type === 'sim_skip' ? 'text-muted-foreground'
                        : ''
                      }>
                        {entry.persona} · {entry.scenario} · {entry.style}+{entry.mode}
                        {entry.error && ` — ${entry.error}`}
                      </span>
                    </div>
                  ))}
                  <div ref={logEndRef} />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Background-run banner: shown when returning to page mid-batch */}
          {!batch.batchRunning && !batch.batchDone && hasRunning && (
            <Card>
              <CardContent className="py-3 flex items-center gap-3">
                <Loader2 className="h-4 w-4 animate-spin text-blue-500 shrink-0" />
                <span className="text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">
                    {simulations.filter((s) => s.state === 'running').length} simulation{simulations.filter((s) => s.state === 'running').length > 1 ? 's' : ''} running
                  </span>
                  {' '}— refreshing automatically
                </span>
              </CardContent>
            </Card>
          )}

          {/* Simulation list */}
          <div>
            {simulations.length === 0 ? (
              <p className="text-muted-foreground text-sm">No simulations yet. Configure and run one above.</p>
            ) : (() => {
              // Derive unique values for filter dropdowns from actual data
              const uniquePersonas = [...new Set(simulations.map((s) => s.persona_name))].sort();
              const uniqueScenarios = [...new Set(simulations.map((s) => s.scenario_name))].sort();
              const uniqueModels = [...new Set(simulations.map((s) => s.model))].sort();
              const uniqueConditions = [...new Set(simulations.map((s) => `${s.style}+${s.mode}`))].sort();

              const filtered = simulations.filter((s) => {
                if (filterPersona && s.persona_name !== filterPersona) return false;
                if (filterScenario && s.scenario_name !== filterScenario) return false;
                if (filterModel && s.model !== filterModel) return false;
                if (filterCondition && `${s.style}+${s.mode}` !== filterCondition) return false;
                if (filterStatus && s.state !== filterStatus) return false;
                return true;
              });

              const hasFilter = filterPersona || filterScenario || filterModel || filterCondition || filterStatus;

              return (
                <>
                  {/* Filter bar */}
                  <div className="flex flex-wrap items-center gap-2 mb-3">
                    <Select value={filterPersona} onValueChange={(v) => setFilterPersona(!v || v === '__all__' ? '' : v)}>
                      <SelectTrigger className="h-7 w-36 text-xs"><SelectValue placeholder="All personas" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__all__">All personas</SelectItem>
                        {uniquePersonas.map((p) => <SelectItem key={p} value={p}>{p}</SelectItem>)}
                      </SelectContent>
                    </Select>

                    <Select value={filterScenario} onValueChange={(v) => setFilterScenario(!v || v === '__all__' ? '' : v)}>
                      <SelectTrigger className="h-7 w-40 text-xs"><SelectValue placeholder="All scenarios" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__all__">All scenarios</SelectItem>
                        {uniqueScenarios.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                      </SelectContent>
                    </Select>

                    <Select value={filterCondition} onValueChange={(v) => setFilterCondition(!v || v === '__all__' ? '' : v)}>
                      <SelectTrigger className="h-7 w-36 text-xs"><SelectValue placeholder="All conditions" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__all__">All conditions</SelectItem>
                        {uniqueConditions.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                      </SelectContent>
                    </Select>

                    <Select value={filterModel} onValueChange={(v) => setFilterModel(!v || v === '__all__' ? '' : v)}>
                      <SelectTrigger className="h-7 w-36 text-xs"><SelectValue placeholder="All models" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__all__">All models</SelectItem>
                        {uniqueModels.map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}
                      </SelectContent>
                    </Select>

                    <Select value={filterStatus} onValueChange={(v) => setFilterStatus(!v || v === '__all__' ? '' : v)}>
                      <SelectTrigger className="h-7 w-32 text-xs"><SelectValue placeholder="All statuses" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__all__">All statuses</SelectItem>
                        <SelectItem value="completed">Completed</SelectItem>
                        <SelectItem value="running">Running</SelectItem>
                        <SelectItem value="error">Error</SelectItem>
                      </SelectContent>
                    </Select>

                    {hasFilter && (
                      <Button size="sm" variant="ghost" className="h-7 text-xs gap-1 text-muted-foreground"
                        onClick={() => { setFilterPersona(''); setFilterScenario(''); setFilterModel(''); setFilterCondition(''); setFilterStatus(''); }}>
                        <X className="h-3 w-3" /> Clear
                      </Button>
                    )}
                    <span className="text-xs text-muted-foreground ml-auto">{filtered.length} of {simulations.length}</span>
                  </div>

                  <div className="flex flex-col gap-3">
                    {filtered.length === 0 && (
                      <p className="text-muted-foreground text-sm">No simulations match the current filters.</p>
                    )}
                    {filtered.map((sim) => (
                  <Card
                    key={sim.id}
                    size="sm"
                    className="cursor-pointer hover:bg-muted/40 transition-colors"
                    onClick={() => navigate(`/simulations/${sim.id}`)}
                  >
                    <CardContent className="flex items-center justify-between py-3">
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">{sim.persona_name}</span>
                          <span className="text-muted-foreground text-xs">—</span>
                          <span className="text-sm text-muted-foreground">{sim.scenario_name}</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <span>{sim.style} + {sim.mode}</span>
                          <span>·</span>
                          <span>{sim.model}</span>
                          <span>·</span>
                          <span>{new Date(sim.created_at).toLocaleString()}</span>
                          {sim.duration_ms != null && (
                            <>
                              <span>·</span>
                              <span>{(sim.duration_ms / 1000).toFixed(1)}s</span>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={statusColor[sim.state] || ''}>{sim.state}</Badge>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0 text-muted-foreground hover:text-red-500"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(sim.id);
                          }}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                  </div>
                </>
              );
            })()}
          </div>

        </div>
      </div>
    </div>
  );
}
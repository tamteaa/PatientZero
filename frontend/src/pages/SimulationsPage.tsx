import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
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
  runBatch,
  listModels,
  listPersonas,
  listScenarios,
  listSimulations,
  deleteSimulation,
} from '@/api/sessions';
import type { BatchEvent } from '@/api/sessions';
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

interface BatchLogEntry {
  type: BatchEvent['type'];
  persona?: string;
  scenario?: string;
  style?: string;
  mode?: string;
  state?: string;
  error?: string;
}

export function SimulationsPage() {
  const navigate = useNavigate();

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

  // Batch run state
  const [batchRunning, setBatchRunning] = useState(false);
  const [batchDone, setBatchDone] = useState(false);
  const [batchCurrent, setBatchCurrent] = useState(0);
  const [batchTotal, setBatchTotal] = useState(0);
  const [batchLog, setBatchLog] = useState<BatchLogEntry[]>([]);
  const [batchSummary, setBatchSummary] = useState<{ succeeded: number; failed: number; skipped: number } | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const logEndRef = useRef<HTMLDivElement | null>(null);

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

  const handleRunAll = useCallback(async () => {
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
            logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
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
          } else if (event.type === 'batch_done') {
            setBatchSummary({ succeeded: event.succeeded ?? 0, failed: event.failed ?? 0, skipped: event.skipped ?? 0 });
            setBatchDone(true);
            setBatchRunning(false);
            fetchSimulations();
          }
        },
        abort.signal,
      );
    } catch {
      setBatchRunning(false);
    }
  }, [model, fetchSimulations]);

  const handleCancelBatch = useCallback(() => {
    abortRef.current?.abort();
    setBatchRunning(false);
    setBatchDone(true);
    fetchSimulations();
  }, [fetchSimulations]);

  const dataLoaded = personas.length > 0 && scenariosList.length > 0;

  return (
    <ScrollArea className="flex-1">
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

              <Button onClick={handleRun} disabled={isLaunching || batchRunning || !dataLoaded} size="sm" className="gap-1.5 h-9">
                {isLaunching ? (
                  <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Running...</>
                ) : (
                  <><Play className="h-3.5 w-3.5" /> Run</>
                )}
              </Button>
              <Button
                onClick={handleRunAll}
                disabled={batchRunning || isLaunching || !dataLoaded}
                size="sm"
                variant="outline"
                className="gap-1.5 h-9"
              >
                {batchRunning ? (
                  <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Running all...</>
                ) : (
                  <><ListVideo className="h-3.5 w-3.5" /> Run All (144)</>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Batch progress card */}
        {(batchRunning || batchDone) && (
          <Card>
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold">Batch Run</span>
                  {batchTotal > 0 && (
                    <span className="text-xs text-muted-foreground tabular-nums">
                      {batchCurrent} / {batchTotal}
                    </span>
                  )}
                  {batchSummary && (
                    <span className="text-xs text-muted-foreground">
                      — {batchSummary.succeeded} ok · {batchSummary.failed} failed · {batchSummary.skipped} skipped
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {batchRunning && (
                    <Button size="sm" variant="ghost" className="h-7 text-xs gap-1 text-muted-foreground" onClick={handleCancelBatch}>
                      <X className="h-3 w-3" /> Cancel
                    </Button>
                  )}
                  {batchDone && (
                    <Button size="sm" variant="ghost" className="h-7 text-xs gap-1 text-muted-foreground" onClick={() => { setBatchDone(false); setBatchLog([]); }}>
                      <X className="h-3 w-3" /> Close
                    </Button>
                  )}
                </div>
              </div>

              {batchTotal > 0 && (
                <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden mb-3">
                  <div
                    className="h-full bg-primary rounded-full transition-all"
                    style={{ width: `${(batchCurrent / batchTotal) * 100}%` }}
                  />
                </div>
              )}

              <div className="max-h-48 overflow-y-auto space-y-1 text-xs font-mono">
                {batchLog.map((entry, i) => (
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
                    <span className={entry.type === 'sim_done' && entry.state === 'error' ? 'text-red-500' : entry.type === 'sim_skip' ? 'text-muted-foreground' : ''}>
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

        {/* Simulation list */}
        <div>
          {simulations.length === 0 ? (
            <p className="text-muted-foreground text-sm">No simulations yet. Configure and run one above.</p>
          ) : (
            <div className="flex flex-col gap-3">
              {simulations.map((sim) => (
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
          )}
        </div>
      </div>
    </ScrollArea>
  );
}

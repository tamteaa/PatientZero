import { useState, useEffect, useCallback, useRef } from 'react';
import { Header } from '@/components/common/Header';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Loader2, FlaskConical, ChevronDown, ChevronUp, CheckCircle2, AlertCircle, X } from 'lucide-react';
import {
  listSimulations,
  listModels,
  evaluateSimulation,
  listEvaluations,
  runBatchEvaluate,
} from '@/api/sessions';
import type { Evaluation, SimulationSummary } from '@/types/simulation';

const SCORE_FIELDS: { key: keyof Evaluation; label: string }[] = [
  { key: 'comprehension_score', label: 'Comprehension' },
  { key: 'factual_recall', label: 'Factual Recall' },
  { key: 'applied_reasoning', label: 'Applied Reasoning' },
  { key: 'explanation_quality', label: 'Explanation Quality' },
  { key: 'interaction_quality', label: 'Interaction Quality' },
];

function ScoreBar({ label, value }: { label: string; value: number | null }) {
  const pct = value != null ? Math.max(0, Math.min(100, value)) : null;
  const color =
    pct == null ? 'bg-muted'
    : pct >= 75 ? 'bg-green-500'
    : pct >= 50 ? 'bg-amber-500'
    : 'bg-red-500';

  return (
    <div className="flex items-center gap-3">
      <span className="w-36 shrink-0 text-xs text-muted-foreground text-right">{label}</span>
      <div className="flex-1 h-3 bg-muted rounded overflow-hidden">
        {pct != null && (
          <div className={`h-full rounded transition-all ${color}`} style={{ width: `${pct}%` }} />
        )}
      </div>
      <span className="w-10 text-xs tabular-nums text-right text-muted-foreground">
        {pct != null ? pct : 'N/A'}
      </span>
    </div>
  );
}

function EvaluationPanel({ evaluation }: { evaluation: Evaluation }) {
  return (
    <div className="mt-3 space-y-2 border-t pt-3">
      <div className="space-y-1.5">
        {SCORE_FIELDS.map(({ key, label }) => (
          <ScoreBar
            key={key}
            label={label}
            value={evaluation[key] as number | null}
          />
        ))}
      </div>
      {evaluation.confidence_comprehension_gap && (
        <div className="mt-2">
          <span className="text-xs font-medium text-muted-foreground">Confidence gap: </span>
          <span className="text-xs">{evaluation.confidence_comprehension_gap}</span>
        </div>
      )}
      {evaluation.justification && (
        <div className="mt-1">
          <span className="text-xs font-medium text-muted-foreground">Justification: </span>
          <span className="text-xs text-muted-foreground">{evaluation.justification}</span>
        </div>
      )}
      <div className="text-xs text-muted-foreground mt-1">
        Evaluated with <span className="font-mono">{evaluation.model}</span> · {new Date(evaluation.created_at).toLocaleString()}
      </div>
    </div>
  );
}

export function JudgePage() {
  const [simulations, setSimulations] = useState<SimulationSummary[]>([]);
  const [evaluations, setEvaluations] = useState<Map<string, Evaluation>>(new Map());
  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState('mock:default');
  const [evaluating, setEvaluating] = useState<Set<string>>(new Set());
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  // Batch evaluate state
  const [batchRunning, setBatchRunning] = useState(false);
  const [batchDone, setBatchDone] = useState(false);
  const [batchCurrent, setBatchCurrent] = useState(0);
  const [batchTotal, setBatchTotal] = useState(0);
  const [batchLog, setBatchLog] = useState<{ simId: string; persona: string; scenario: string; state: 'running' | 'completed' | 'error'; score?: number | null; error?: string }[]>([]);
  const [batchSummary, setBatchSummary] = useState<{ succeeded: number; failed: number } | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const logEndRef = useRef<HTMLDivElement | null>(null);

  const reload = useCallback(() => {
    return Promise.all([
      listSimulations(),
      listEvaluations(),
    ]).then(([sims, evals]) => {
      setSimulations(sims.filter((s) => s.state === 'completed'));
      const evalMap = new Map<string, Evaluation>();
      for (const e of evals) evalMap.set(e.simulation_id, e);
      setEvaluations(evalMap);
    });
  }, []);

  useEffect(() => {
    listModels().then((ms) => {
      setModels(ms);
      if (ms.length > 0) setSelectedModel(ms[0]);
    }).catch(() => {});
    reload().finally(() => setLoading(false));
  }, [reload]);

  const handleEvaluate = useCallback(async (simId: string) => {
    setEvaluating((prev) => new Set(prev).add(simId));
    try {
      const result = await evaluateSimulation(simId, selectedModel);
      setEvaluations((prev) => new Map(prev).set(simId, result));
      setExpanded((prev) => new Set(prev).add(simId));
    } finally {
      setEvaluating((prev) => {
        const next = new Set(prev);
        next.delete(simId);
        return next;
      });
    }
  }, [selectedModel]);

  const handleBatchEvaluate = useCallback(async () => {
    const abort = new AbortController();
    abortRef.current = abort;
    setBatchRunning(true);
    setBatchDone(false);
    setBatchLog([]);
    setBatchSummary(null);
    setBatchCurrent(0);
    setBatchTotal(0);

    try {
      await runBatchEvaluate(
        selectedModel,
        (event) => {
          if (event.type === 'batch_start') {
            setBatchTotal(event.total);
          } else if (event.type === 'eval_start') {
            setBatchCurrent(event.current ?? 0);
            setBatchLog((prev) => [...prev, {
              simId: event.sim_id ?? '',
              persona: event.persona ?? '',
              scenario: event.scenario ?? '',
              state: 'running',
            }]);
            logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
          } else if (event.type === 'eval_done') {
            setBatchCurrent(event.current ?? 0);
            setBatchLog((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last?.state === 'running') {
                updated[updated.length - 1] = {
                  ...last,
                  state: event.state === 'error' ? 'error' : 'completed',
                  score: event.comprehension_score,
                  error: event.error,
                };
              }
              return updated;
            });
            if (event.state === 'completed' && event.sim_id) {
              reload();
            }
          } else if (event.type === 'batch_done') {
            setBatchSummary({ succeeded: event.succeeded ?? 0, failed: event.failed ?? 0 });
            setBatchRunning(false);
            setBatchDone(true);
            reload();
          }
        },
        abort.signal,
      );
    } catch {
      setBatchRunning(false);
    }
  }, [selectedModel, reload]);

  const toggleExpand = (simId: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(simId)) next.delete(simId);
      else next.add(simId);
      return next;
    });
  };

  const evaluatedCount = evaluations.size;
  const avgComprehension = evaluatedCount > 0
    ? Array.from(evaluations.values())
        .filter((e) => e.comprehension_score != null)
        .reduce((sum, e, _, arr) => sum + (e.comprehension_score ?? 0) / arr.length, 0)
    : null;

  if (loading) {
    return (
      <>
        <Header title="Judge Calibration" />
        <div className="flex flex-1 items-center justify-center text-muted-foreground text-sm">
          Loading…
        </div>
      </>
    );
  }

  if (simulations.length === 0) {
    return (
      <>
        <Header title="Judge Calibration" />
        <div className="flex flex-1 items-center justify-center text-muted-foreground">
          <div className="text-center">
            <p className="text-sm font-medium">No completed simulations</p>
            <p className="text-xs mt-1">Complete some simulations to run judge evaluations.</p>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Header title="Judge Calibration">
        <div className="flex items-center gap-2">
          {avgComprehension != null && (
            <span className="text-xs text-muted-foreground">
              avg comprehension: <span className="font-semibold tabular-nums">{avgComprehension.toFixed(0)}</span>
            </span>
          )}
          <Select value={selectedModel} onValueChange={(v) => { if (v) setSelectedModel(v); }}>
            <SelectTrigger className="h-7 w-36 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {models.map((m) => (
                <SelectItem key={m} value={m}>{m}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-xs gap-1.5"
            disabled={batchRunning}
            onClick={handleBatchEvaluate}
          >
            {batchRunning
              ? <><Loader2 className="h-3 w-3 animate-spin" /> Evaluating…</>
              : <><FlaskConical className="h-3 w-3" /> Evaluate All</>}
          </Button>
        </div>
      </Header>
      <ScrollArea className="flex-1">
        <div className="p-6 max-w-3xl mx-auto space-y-3">
          <p className="text-xs text-muted-foreground">
            {evaluatedCount} of {simulations.length} simulations evaluated
          </p>

          {/* Batch progress */}
          {(batchRunning || batchDone) && (
            <Card>
              <CardContent className="py-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold">Batch Evaluate</span>
                    {batchTotal > 0 && (
                      <span className="text-xs text-muted-foreground tabular-nums">{batchCurrent} / {batchTotal}</span>
                    )}
                    {batchSummary && (
                      <span className="text-xs text-muted-foreground">— {batchSummary.succeeded} ok · {batchSummary.failed} failed</span>
                    )}
                  </div>
                  {batchDone && (
                    <Button size="sm" variant="ghost" className="h-6 w-6 p-0 text-muted-foreground"
                      onClick={() => { setBatchDone(false); setBatchLog([]); }}>
                      <X className="h-3 w-3" />
                    </Button>
                  )}
                </div>
                {batchTotal > 0 && (
                  <div className="h-1 w-full bg-muted rounded-full overflow-hidden mb-2">
                    <div className="h-full bg-primary rounded-full transition-all"
                      style={{ width: `${(batchCurrent / batchTotal) * 100}%` }} />
                  </div>
                )}
                <div className="max-h-36 overflow-y-auto space-y-0.5 text-xs font-mono">
                  {batchLog.map((entry, i) => (
                    <div key={i} className="flex items-center gap-2">
                      {entry.state === 'completed' && <CheckCircle2 className="h-3 w-3 text-green-500 shrink-0" />}
                      {entry.state === 'error' && <AlertCircle className="h-3 w-3 text-red-500 shrink-0" />}
                      {entry.state === 'running' && <Loader2 className="h-3 w-3 text-blue-500 animate-spin shrink-0" />}
                      <span className={entry.state === 'error' ? 'text-red-500' : ''}>
                        {entry.persona} · {entry.scenario}
                        {entry.state === 'completed' && entry.score != null && ` → ${entry.score}`}
                        {entry.error && ` — ${entry.error}`}
                      </span>
                    </div>
                  ))}
                  <div ref={logEndRef} />
                </div>
              </CardContent>
            </Card>
          )}

          {simulations.map((sim) => {
            const evaluation = evaluations.get(sim.id);
            const isEvaluating = evaluating.has(sim.id);
            const isExpanded = expanded.has(sim.id);

            return (
              <Card key={sim.id} size="sm">
                <CardContent className="py-3">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex flex-col gap-0.5 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm truncate">{sim.persona_name}</span>
                        <span className="text-muted-foreground text-xs">—</span>
                        <span className="text-xs text-muted-foreground truncate">{sim.scenario_name}</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span>{sim.style} + {sim.mode}</span>
                        <span>·</span>
                        <span className="font-mono">{sim.model}</span>
                        {evaluation && (
                          <>
                            <span>·</span>
                            <Badge className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-xs px-1.5 py-0">
                              score: {evaluation.comprehension_score ?? '—'}
                            </Badge>
                          </>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      {evaluation && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0 text-muted-foreground"
                          onClick={() => toggleExpand(sim.id)}
                        >
                          {isExpanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant={evaluation ? 'outline' : 'default'}
                        className="h-7 text-xs gap-1.5"
                        disabled={isEvaluating}
                        onClick={() => handleEvaluate(sim.id)}
                      >
                        {isEvaluating ? (
                          <><Loader2 className="h-3 w-3 animate-spin" /> Evaluating…</>
                        ) : (
                          <><FlaskConical className="h-3 w-3" /> {evaluation ? 'Re-evaluate' : 'Evaluate'}</>
                        )}
                      </Button>
                    </div>
                  </div>

                  {evaluation && isExpanded && (
                    <EvaluationPanel evaluation={evaluation} />
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </ScrollArea>
    </>
  );
}
import { useState, useEffect, useCallback } from 'react';
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
import { Loader2, FlaskConical, ChevronDown, ChevronUp } from 'lucide-react';
import {
  listSimulations,
  listModels,
  evaluateSimulation,
  listEvaluations,
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
        </div>
      </Header>
      <ScrollArea className="flex-1">
        <div className="p-6 max-w-3xl mx-auto space-y-3">
          <p className="text-xs text-muted-foreground">
            {evaluatedCount} of {simulations.length} simulations evaluated
          </p>

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
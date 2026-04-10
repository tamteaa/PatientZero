import { useState, useEffect, useCallback } from 'react';
import { useAtomValue } from 'jotai';
import { Header } from '@/components/common/Header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, FlaskConical } from 'lucide-react';
import {
  listSimulations,
  evaluateSimulation,
  listEvaluations,
} from '@/api/sessions';
import { useError } from '@/contexts/ErrorContext';
import { globalModelAtom } from '@/atoms/model';
import type { Evaluation, JudgeScoreKey, SimulationSummary } from '@/types/simulation';
import { meanScore } from '@/types/simulation';

const SCORE_FIELDS: { key: JudgeScoreKey; label: string }[] = [
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

function DetailPane({
  sim,
  evaluation,
  isEvaluating,
  onEvaluate,
}: {
  sim: SimulationSummary;
  evaluation: Evaluation | undefined;
  isEvaluating: boolean;
  onEvaluate: () => void;
}) {
  return (
    <div className="flex flex-col gap-4 p-6 max-w-2xl">
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-col gap-1 min-w-0">
          <h2 className="text-lg font-semibold">{sim.persona_name}</h2>
          <p className="text-sm text-muted-foreground">{sim.scenario_name}</p>
          <p className="text-xs text-muted-foreground font-mono mt-1">{sim.model}</p>
        </div>
        <Button
          size="sm"
          variant={evaluation ? 'outline' : 'default'}
          className="h-8 text-xs gap-1.5 shrink-0"
          disabled={isEvaluating}
          onClick={onEvaluate}
        >
          {isEvaluating ? (
            <><Loader2 className="h-3 w-3 animate-spin" /> Evaluating…</>
          ) : (
            <><FlaskConical className="h-3 w-3" /> {evaluation ? 'Re-evaluate' : 'Evaluate'}</>
          )}
        </Button>
      </div>

      {evaluation && evaluation.judge_results.length > 0 ? (
        <div className="space-y-3 border-t pt-4">
          <div className="space-y-1.5">
            {SCORE_FIELDS.map(({ key, label }) => (
              <ScoreBar
                key={key}
                label={label}
                value={meanScore(evaluation, key)}
              />
            ))}
          </div>
          {evaluation.judge_results[0].confidence_comprehension_gap && (
            <div>
              <span className="text-xs font-medium text-muted-foreground">Confidence gap: </span>
              <span className="text-xs">{evaluation.judge_results[0].confidence_comprehension_gap}</span>
            </div>
          )}
          {evaluation.judge_results[0].justification && (
            <div>
              <span className="text-xs font-medium text-muted-foreground">Justification: </span>
              <span className="text-xs text-muted-foreground">{evaluation.judge_results[0].justification}</span>
            </div>
          )}
          <div className="text-xs text-muted-foreground">
            Evaluated with <span className="font-mono">{evaluation.judge_results.map((j) => j.model).join(', ')}</span>
            {evaluation.created_at && ` · ${new Date(evaluation.created_at).toLocaleString()}`}
          </div>
        </div>
      ) : (
        <div className="border-t pt-4 text-sm text-muted-foreground">
          Not yet evaluated. Click Evaluate to run the judge.
        </div>
      )}
    </div>
  );
}

export function JudgePage() {
  const [simulations, setSimulations] = useState<SimulationSummary[]>([]);
  const [evaluations, setEvaluations] = useState<Map<string, Evaluation>>(new Map());
  const selectedModel = useAtomValue(globalModelAtom);
  const [evaluating, setEvaluating] = useState<Set<string>>(new Set());
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const { handleError } = useError();

  const reload = useCallback(() => {
    return Promise.all([
      listSimulations(),
      listEvaluations(),
    ]).then(([sims, evals]) => {
      const completed = sims.filter((s) => s.state === 'completed');
      setSimulations(completed);
      const evalMap = new Map<string, Evaluation>();
      for (const e of evals) evalMap.set(e.simulation_id, e);
      setEvaluations(evalMap);
      setSelectedId((prev) => prev ?? completed[0]?.id ?? null);
    });
  }, []);

  useEffect(() => {
    reload()
      .catch((err) => handleError(err, 'Failed to load evaluations'))
      .finally(() => setLoading(false));
  }, [reload]);

  const handleEvaluate = useCallback(async (simId: string) => {
    setEvaluating((prev) => new Set(prev).add(simId));
    try {
      const result = await evaluateSimulation(simId, selectedModel);
      setEvaluations((prev) => new Map(prev).set(simId, result));
    } catch (err) {
      handleError(err, 'Evaluation failed');
    } finally {
      setEvaluating((prev) => {
        const next = new Set(prev);
        next.delete(simId);
        return next;
      });
    }
  }, [selectedModel, handleError]);

  const evaluatedCount = evaluations.size;
  const comprehensionMeans = Array.from(evaluations.values())
    .map((e) => meanScore(e, 'comprehension_score'))
    .filter((v): v is number => v != null);
  const avgComprehension = comprehensionMeans.length
    ? comprehensionMeans.reduce((a, b) => a + b, 0) / comprehensionMeans.length
    : null;

  const selectedSim = simulations.find((s) => s.id === selectedId) ?? null;

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
        {avgComprehension != null && (
          <span className="text-xs text-muted-foreground">
            avg comprehension: <span className="font-semibold tabular-nums">{avgComprehension.toFixed(0)}</span>
          </span>
        )}
      </Header>
      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Left: list */}
        <div className="flex flex-col w-80 border-r border-border min-h-0">
          <div className="px-4 py-2 text-xs text-muted-foreground border-b border-border">
            {evaluatedCount} of {simulations.length} evaluated
          </div>
          <ScrollArea className="flex-1 min-h-0">
            <div className="flex flex-col">
              {simulations.map((sim) => {
                const evaluation = evaluations.get(sim.id);
                const isSelected = sim.id === selectedId;
                return (
                  <button
                    key={sim.id}
                    onClick={() => setSelectedId(sim.id)}
                    className={`flex flex-col gap-0.5 px-4 py-3 text-left border-b border-border/50 transition-colors ${
                      isSelected ? 'bg-muted' : 'hover:bg-muted/50'
                    }`}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="font-medium text-sm truncate">{sim.persona_name}</span>
                      {evaluation && (
                        <Badge className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-xs px-1.5 py-0 shrink-0">
                          {meanScore(evaluation, 'comprehension_score')?.toFixed(0) ?? '—'}
                        </Badge>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground truncate">{sim.scenario_name}</span>
                  </button>
                );
              })}
            </div>
          </ScrollArea>
        </div>

        {/* Right: detail */}
        <ScrollArea className="flex-1 min-h-0">
          {selectedSim ? (
            <DetailPane
              sim={selectedSim}
              evaluation={evaluations.get(selectedSim.id)}
              isEvaluating={evaluating.has(selectedSim.id)}
              onEvaluate={() => handleEvaluate(selectedSim.id)}
            />
          ) : (
            <div className="flex items-center justify-center h-full p-6 text-sm text-muted-foreground">
              Select a simulation from the list.
            </div>
          )}
        </ScrollArea>
      </div>
    </>
  );
}

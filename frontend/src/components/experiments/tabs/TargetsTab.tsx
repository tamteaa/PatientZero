import { useCallback, useEffect, useState } from 'react';
import { useAtomValue, useSetAtom } from 'jotai';
import { Loader2, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  getExperimentAnalysis,
  listExperiments,
  listOptimizationTargets,
  optimizeExperiment,
  setCurrentOptimizationTarget,
} from '@/api/sessions';
import type { ScoreStats } from '@/api/sessions';
import { experimentsAtom } from '@/atoms/experiment';
import { useError } from '@/contexts/ErrorContext';
import type {
  OptimizationResult,
  OptimizationTarget,
} from '@/types/simulation';
import {
  OptimizeOptionsForm,
  DEFAULT_OPTIMIZE_OPTIONS,
  type OptimizeOptions,
} from '../targets/OptimizeOptionsForm';
import { CurrentPromptsTabs } from '../targets/CurrentPromptsTabs';
import { OptimizationResultCard } from '../targets/OptimizationResultCard';
import { OptimizationTargetsList } from '../targets/OptimizationTargetsList';

interface Props {
  experimentId: string;
}

export function TargetsTab({ experimentId }: Props) {
  const { handleError } = useError();
  const experiments = useAtomValue(experimentsAtom);
  const setExperiments = useSetAtom(experimentsAtom);
  const experiment = experiments.find((e) => e.id === experimentId) ?? null;
  const [targets, setTargets] = useState<OptimizationTarget[]>([]);
  const [scoresByTargetId, setScoresByTargetId] = useState<Record<string, ScoreStats>>({});
  const [loading, setLoading] = useState(false);
  const [activatingTargetId, setActivatingTargetId] = useState<string | null>(null);
  const [optimizing, setOptimizing] = useState(false);
  const [lastResult, setLastResult] = useState<OptimizationResult | null>(null);
  const [options, setOptions] = useState<OptimizeOptions>(DEFAULT_OPTIMIZE_OPTIONS);
  const [optionsExpanded, setOptionsExpanded] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [ts, analysis] = await Promise.all([
        listOptimizationTargets(experimentId),
        getExperimentAnalysis(experimentId),
      ]);
      setTargets(ts);
      const allScores = analysis.by_optimization_target_id ?? {};
      const targetIds = new Set(ts.map((t) => t.id));
      const filtered: Record<string, ScoreStats> = {};
      for (const [id, stats] of Object.entries(allScores)) {
        if (targetIds.has(id)) filtered[id] = stats;
      }
      setScoresByTargetId(filtered);
    } catch (err) {
      handleError(err, 'Failed to load optimization targets');
    } finally {
      setLoading(false);
    }
  }, [experimentId, handleError]);

  useEffect(() => {
    setLastResult(null);
    refresh();
  }, [refresh]);

  const handleOptimize = async () => {
    setOptimizing(true);
    try {
      const result = await optimizeExperiment(experimentId, {
        seeding_mode: options.seeding_mode,
        num_candidates: options.num_candidates,
        trials_per_candidate: options.trials_per_candidate,
        worst_cases_k: options.worst_cases_k,
        metric_weights: { comprehension_score: options.comprehension_weight },
      });
      setLastResult(result);
      setExperiments(await listExperiments());
      await refresh();
    } catch (err) {
      handleError(err, 'Optimization failed');
    } finally {
      setOptimizing(false);
    }
  };

  const handleActivate = async (targetId: string) => {
    setActivatingTargetId(targetId);
    try {
      await setCurrentOptimizationTarget(experimentId, targetId);
      setExperiments(await listExperiments());
      await refresh();
    } catch (err) {
      handleError(err, 'Failed to activate target');
    } finally {
      setActivatingTargetId(null);
    }
  };

  const currentTargetId = experiment?.current_optimization_target_id ?? null;
  const currentTarget = targets.find((t) => t.id === currentTargetId) ?? null;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1 min-w-0">
          <h3 className="text-sm font-semibold">Optimization</h3>
          <p className="text-xs text-muted-foreground">
            Each run produces a new version of the prompt set. Activate any prior version to roll
            back without deleting newer ones.
          </p>
        </div>
        <Button
          variant="default"
          size="sm"
          className="h-8 text-xs gap-1.5 shrink-0"
          disabled={optimizing}
          onClick={handleOptimize}
        >
          {optimizing ? (
            <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Optimizing…</>
          ) : (
            <><Sparkles className="h-3.5 w-3.5" /> Optimize</>
          )}
        </Button>
      </div>

      <OptimizeOptionsForm
        value={options}
        onChange={setOptions}
        expanded={optionsExpanded}
        onToggle={() => setOptionsExpanded((v) => !v)}
      />

      {/* A + B + C: last-run result card */}
      {lastResult && (
        <OptimizationResultCard
          result={lastResult}
          onDismiss={() => setLastResult(null)}
        />
      )}

      {/* G: current prompts with per-role tabs */}
      {currentTarget && <CurrentPromptsTabs target={currentTarget} />}

      {/* D + E: scored + lineage version list */}
      <OptimizationTargetsList
        targets={targets}
        currentTargetId={currentTargetId}
        loading={loading}
        activatingTargetId={activatingTargetId}
        scoresByTargetId={scoresByTargetId}
        onActivate={handleActivate}
      />
    </div>
  );
}

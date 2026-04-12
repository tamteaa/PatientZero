import { useCallback, useEffect, useState } from 'react';
import {
  getExperimentCoverage,
  listExperimentEvaluations,
  listExperimentSimulations,
} from '@/api/sessions';
import { useError } from '@/contexts/ErrorContext';
import type { CoverageReport, Evaluation, SimulationSummary } from '@/types/simulation';
import { meanScore } from '@/types/simulation';

interface Props {
  experimentId: string;
  refreshKey: number;
}

function StatCell({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="flex flex-col px-4 py-3 min-w-0">
      <p className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="text-2xl font-semibold tabular-nums mt-1">{value}</p>
      {sub && <p className="text-[11px] text-muted-foreground mt-0.5 truncate">{sub}</p>}
    </div>
  );
}

export function ExperimentSummary({ experimentId, refreshKey }: Props) {
  const { handleError } = useError();
  const [sims, setSims] = useState<SimulationSummary[]>([]);
  const [evals, setEvals] = useState<Evaluation[]>([]);
  const [coverage, setCoverage] = useState<CoverageReport | null>(null);

  const load = useCallback(async () => {
    try {
      const [s, e, cov] = await Promise.all([
        listExperimentSimulations(experimentId),
        listExperimentEvaluations(experimentId),
        getExperimentCoverage(experimentId, { mc_samples: 12_000 }),
      ]);
      setSims(s);
      setEvals(e);
      setCoverage(cov);
    } catch (err) {
      handleError(err, 'Failed to load experiment summary');
    }
  }, [experimentId, handleError]);

  useEffect(() => {
    setCoverage(null);
    load();
  }, [load, refreshKey]);

  const completed = sims.filter((s) => s.state === 'completed');
  const evalMeans = evals
    .map((e) => meanScore(e, 'comprehension_score'))
    .filter((v): v is number => v != null);
  const avgComprehension = evalMeans.length > 0
    ? evalMeans.reduce((a, b) => a + b, 0) / evalMeans.length
    : null;
  const failed = sims.length - completed.length;
  const completionPct = sims.length > 0 ? Math.round((completed.length / sims.length) * 100) : null;

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-4 divide-x divide-border rounded-md border border-border bg-card">
        <StatCell
          label="Simulations"
          value={sims.length}
          sub={`${completed.length} completed`}
        />
        <StatCell
          label="Evaluated"
          value={`${evals.length} / ${completed.length}`}
          sub={completed.length > 0
            ? `${Math.round((evals.length / completed.length) * 100)}% of done`
            : '—'}
        />
        <StatCell
          label="Avg compreh"
          value={avgComprehension != null ? avgComprehension.toFixed(0) : '—'}
          sub={evalMeans.length > 0 ? `from ${evalMeans.length} evals` : 'no evals yet'}
        />
        <StatCell
          label="Completion"
          value={completionPct != null ? `${completionPct}%` : '—'}
          sub={`${failed} not completed`}
        />
      </div>

      {coverage && (
        <div className="rounded-md border border-border bg-card px-4 py-3 space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
              Coverage
            </span>
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
          <div className="flex items-center justify-between text-[11px] text-muted-foreground tabular-nums">
            <span>{coverage.cells_hit} / {coverage.cells_total} cells hit</span>
            <span>{coverage.simulations_counted} / {coverage.estimated_total_needed} sims to full</span>
            {coverage.distribution_match != null && (
              <span>
                match{' '}
                <span className="font-medium text-foreground">
                  {(coverage.distribution_match * 100).toFixed(1)}%
                </span>
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

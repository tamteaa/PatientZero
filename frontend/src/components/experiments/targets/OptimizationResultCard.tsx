import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronDown, ChevronRight, Sparkles, TrendingUp, TrendingDown, Minus, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { OptimizationResult } from '@/types/simulation';

interface Props {
  result: OptimizationResult;
  onDismiss: () => void;
}

export function OptimizationResultCard({ result, onDismiss }: Props) {
  const [showCandidates, setShowCandidates] = useState(false);
  const [showWorstCases, setShowWorstCases] = useState(false);
  const navigate = useNavigate();

  const delta = result.improvement;
  const positive = delta > 0.01;
  const negative = delta < -0.01;
  const baselineScore = result.baseline.mean_score;
  const newScore = baselineScore + delta;

  const sortedCandidates = [...result.candidates].sort((a, b) => b.mean_score - a.mean_score);
  const winnerId = sortedCandidates[0]?.target_id;

  const DeltaIcon = positive ? TrendingUp : negative ? TrendingDown : Minus;
  const deltaColor = positive
    ? 'text-emerald-600 dark:text-emerald-400'
    : negative
      ? 'text-red-600 dark:text-red-400'
      : 'text-muted-foreground';

  const worstCases = result.signal.worst_cases;

  return (
    <div className="rounded-md border border-border bg-card overflow-hidden">
      {/* Header */}
      <div className="flex items-start gap-3 px-4 py-3 bg-gradient-to-r from-primary/5 to-transparent border-b border-border">
        <Sparkles className="h-4 w-4 text-primary mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2 flex-wrap">
            <h4 className="text-sm font-semibold">Last optimization</h4>
            <span className="text-[11px] text-muted-foreground tabular-nums">
              {new Date(result.new_target.created_at).toLocaleString()}
            </span>
          </div>
        </div>
        <button
          onClick={onDismiss}
          className="text-muted-foreground hover:text-foreground shrink-0"
          aria-label="Dismiss"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Scoreboard */}
      <div className="grid grid-cols-4 divide-x divide-border">
        <div className="px-4 py-3">
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Baseline</p>
          <p className="text-xl font-semibold tabular-nums mt-1">{baselineScore.toFixed(2)}</p>
          <p className="text-[11px] text-muted-foreground mt-0.5">
            {result.baseline.trial_count} sims
          </p>
        </div>
        <div className="px-4 py-3">
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground">New</p>
          <p className="text-xl font-semibold tabular-nums mt-1">{newScore.toFixed(2)}</p>
          <p className="text-[11px] text-muted-foreground mt-0.5">winning candidate</p>
        </div>
        <div className="px-4 py-3">
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Δ Change</p>
          <p className={`text-xl font-semibold tabular-nums mt-1 flex items-center gap-1 ${deltaColor}`}>
            <DeltaIcon className="h-4 w-4" />
            {delta >= 0 ? '+' : ''}{delta.toFixed(2)}
          </p>
          <p className="text-[11px] text-muted-foreground mt-0.5">vs baseline</p>
        </div>
        <div className="px-4 py-3">
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Tried</p>
          <p className="text-xl font-semibold tabular-nums mt-1">{result.candidates.length}</p>
          <p className="text-[11px] text-muted-foreground mt-0.5">candidates</p>
        </div>
      </div>

      {/* Candidate leaderboard */}
      <div className="border-t border-border">
        <button
          onClick={() => setShowCandidates((v) => !v)}
          className="flex items-center gap-1.5 w-full text-left px-4 py-2 text-xs font-medium hover:bg-muted/40 transition-colors"
        >
          {showCandidates ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
          Candidate leaderboard
          <span className="text-muted-foreground font-normal">
            ({result.candidates.length})
          </span>
        </button>
        {showCandidates && (
          <div className="px-4 pb-3">
            <div className="rounded border border-border/60 overflow-hidden">
              <table className="w-full text-xs tabular-nums">
                <thead className="bg-muted/30 text-muted-foreground">
                  <tr>
                    <th className="text-left px-3 py-1.5 font-medium">Rank</th>
                    <th className="text-left px-3 py-1.5 font-medium">Candidate</th>
                    <th className="text-right px-3 py-1.5 font-medium">Mean score</th>
                    <th className="text-right px-3 py-1.5 font-medium">Trials</th>
                    <th className="text-right px-3 py-1.5 font-medium">Δ vs baseline</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedCandidates.map((c, i) => {
                    const isWinner = c.target_id === winnerId;
                    const candDelta = c.mean_score - baselineScore;
                    return (
                      <tr
                        key={c.target_id}
                        className={`border-t border-border/60 ${isWinner ? 'bg-emerald-50/50 dark:bg-emerald-900/10' : ''}`}
                      >
                        <td className="px-3 py-1.5">
                          {i + 1}
                          {isWinner && <span className="ml-1 text-emerald-600 dark:text-emerald-400">★</span>}
                        </td>
                        <td className="px-3 py-1.5 font-mono text-[11px] text-muted-foreground">
                          {c.target_id.slice(0, 8)}…
                        </td>
                        <td className="px-3 py-1.5 text-right font-medium">{c.mean_score.toFixed(2)}</td>
                        <td className="px-3 py-1.5 text-right text-muted-foreground">{c.trial_count}</td>
                        <td className={`px-3 py-1.5 text-right ${candDelta > 0 ? 'text-emerald-600 dark:text-emerald-400' : candDelta < 0 ? 'text-red-600 dark:text-red-400' : 'text-muted-foreground'}`}>
                          {candDelta >= 0 ? '+' : ''}{candDelta.toFixed(2)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Worst cases that drove the run */}
      <div className="border-t border-border">
        <button
          onClick={() => setShowWorstCases((v) => !v)}
          className="flex items-center gap-1.5 w-full text-left px-4 py-2 text-xs font-medium hover:bg-muted/40 transition-colors"
        >
          {showWorstCases ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
          Worst cases targeted
          <span className="text-muted-foreground font-normal">
            ({worstCases.length} of {result.signal.simulations_considered} sims considered)
          </span>
        </button>
        {showWorstCases && (
          <div className="px-4 pb-3 space-y-2">
            {worstCases.length === 0 ? (
              <p className="text-xs text-muted-foreground italic">
                No worst cases — signal was empty or config.worst_cases_k = 0.
              </p>
            ) : (
              worstCases.map((wc) => {
                const compScore = wc.scores.comprehension_score;
                return (
                  <div
                    key={wc.simulation_id}
                    className="rounded border border-border/60 px-3 py-2 text-xs bg-muted/20 hover:bg-muted/40 transition-colors cursor-pointer"
                    onClick={() => navigate(`/simulations/${wc.simulation_id}`)}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="font-medium truncate">{wc.scenario_name}</span>
                      {compScore != null && (
                        <span className="shrink-0 font-mono tabular-nums text-red-600 dark:text-red-400">
                          score {compScore}
                        </span>
                      )}
                    </div>
                    {Object.keys(wc.patient_traits).length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-1">
                        {Object.entries(wc.patient_traits).slice(0, 4).map(([k, v]) => (
                          <span
                            key={k}
                            className="text-[10px] px-1.5 py-0.5 rounded bg-background border border-border/60 text-muted-foreground"
                          >
                            {k}: {v}
                          </span>
                        ))}
                      </div>
                    )}
                    {wc.judge_justification && (
                      <p className="text-[11px] text-muted-foreground line-clamp-2">
                        {wc.judge_justification}
                      </p>
                    )}
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>
    </div>
  );
}

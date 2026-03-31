import { useState, useEffect } from 'react';
import { Header } from '@/components/common/Header';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { listSimulations, listEvaluations, listPersonas } from '@/api/sessions';
import type { Evaluation, Persona, SimulationSummary } from '@/types/simulation';
import { anova2x2 } from '@/lib/anova';
import type { AnovaEffect } from '@/lib/anova';

const CONDITIONS = [
  { key: 'clinical-static', label: 'Clinical + Static', style: 'clinical', mode: 'static' },
  { key: 'clinical-dialog', label: 'Clinical + Dialog', style: 'clinical', mode: 'dialog' },
  { key: 'analogy-static', label: 'Analogy + Static', style: 'analogy', mode: 'static' },
  { key: 'analogy-dialog', label: 'Analogy + Dialog', style: 'analogy', mode: 'dialog' },
];

const CONDITION_COLORS: Record<string, string> = {
  'clinical-static': 'bg-blue-500',
  'clinical-dialog': 'bg-blue-400',
  'analogy-static': 'bg-violet-500',
  'analogy-dialog': 'bg-violet-400',
};

const SCORE_METRICS: { key: keyof Evaluation; label: string }[] = [
  { key: 'comprehension_score', label: 'Comprehension' },
  { key: 'factual_recall', label: 'Factual Recall' },
  { key: 'applied_reasoning', label: 'Applied Reasoning' },
  { key: 'explanation_quality', label: 'Explanation Quality' },
  { key: 'interaction_quality', label: 'Interaction Quality' },
];

function avg(values: number[]): number | null {
  if (values.length === 0) return null;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function scoreColor(v: number | null): string {
  if (v == null) return 'text-muted-foreground';
  if (v >= 70) return 'text-green-600 dark:text-green-400';
  if (v >= 50) return 'text-amber-600 dark:text-amber-400';
  return 'text-red-600 dark:text-red-400';
}

function ScoreBar({
  label, value, n, colorClass,
}: {
  label: string; value: number | null; n: number; colorClass?: string;
}) {
  const pct = value != null ? Math.max(0, Math.min(100, value)) : null;
  const bar = colorClass ?? (
    pct == null ? 'bg-muted'
    : pct >= 70 ? 'bg-green-500'
    : pct >= 50 ? 'bg-amber-500'
    : 'bg-red-500'
  );
  return (
    <div className="flex items-center gap-3">
      <span className="w-36 shrink-0 text-xs text-muted-foreground text-right">{label}</span>
      <div className="flex-1 h-5 bg-muted rounded overflow-hidden">
        {pct != null && (
          <div className={`h-full rounded transition-all ${bar}`} style={{ width: `${pct}%` }} />
        )}
      </div>
      <span className={`w-16 text-xs tabular-nums text-right ${scoreColor(value)}`}>
        {value != null ? `${value.toFixed(1)} (${n})` : '—'}
      </span>
    </div>
  );
}

function DeltaBadge({ delta }: { delta: number | null }) {
  if (delta == null) return <span className="text-xs text-muted-foreground">—</span>;
  const pos = delta > 0;
  return (
    <span className={`text-xs font-semibold tabular-nums ${pos ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
      {pos ? '+' : ''}{delta.toFixed(1)}
    </span>
  );
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <Card size="sm">
      <CardContent className="pt-3 pb-3">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-2xl font-semibold tabular-nums mt-0.5">{value}</p>
        {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
      </CardContent>
    </Card>
  );
}

function BarChart({
  data, maxValue, formatValue,
}: {
  data: { label: string; value: number; colorClass: string }[];
  maxValue: number;
  formatValue?: (v: number) => string;
}) {
  return (
    <div className="space-y-2.5">
      {data.map(({ label, value, colorClass }) => (
        <div key={label} className="flex items-center gap-3">
          <span className="w-36 shrink-0 text-xs text-muted-foreground text-right">{label}</span>
          <div className="flex-1 flex items-center gap-2">
            <div className="flex-1 h-5 bg-muted rounded overflow-hidden">
              <div
                className={`h-full rounded transition-all ${colorClass}`}
                style={{ width: maxValue > 0 ? `${(value / maxValue) * 100}%` : '0%' }}
              />
            </div>
            <span className="w-10 text-xs tabular-nums text-right">
              {formatValue ? formatValue(value) : value}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

export function AnalysisPage() {
  const [simulations, setSimulations] = useState<SimulationSummary[]>([]);
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([listSimulations(), listEvaluations(), listPersonas()])
      .then(([sims, evals, ps]) => { setSimulations(sims); setEvaluations(evals); setPersonas(ps); })
      .finally(() => setLoading(false));
  }, []);

  const completed = simulations.filter((s) => s.state === 'completed');
  const errors = simulations.filter((s) => s.state === 'error');
  const running = simulations.filter((s) => s.state === 'running');
  const completionRate = simulations.length > 0 ? Math.round((completed.length / simulations.length) * 100) : 0;
  const avgDurationAll = completed.length > 0
    ? completed.reduce((s, sim) => s + (sim.duration_ms ?? 0), 0) / completed.length : 0;

  // ── Condition counts ──────────────────────────────────────────────────────
  const countByCondition = CONDITIONS.map(({ key, label, style, mode }) => ({
    label, colorClass: CONDITION_COLORS[key],
    value: simulations.filter((s) => s.style === style && s.mode === mode).length,
  }));
  const maxCount = Math.max(...countByCondition.map((d) => d.value), 1);

  const durationByCondition = CONDITIONS.map(({ key, label, style, mode }) => {
    const rel = completed.filter((s) => s.style === style && s.mode === mode && s.duration_ms != null);
    const a = rel.length > 0 ? rel.reduce((s, x) => s + (x.duration_ms ?? 0), 0) / rel.length : 0;
    return { label, value: a, colorClass: CONDITION_COLORS[key] };
  });
  const maxDuration = Math.max(...durationByCondition.map((d) => d.value), 1);

  // ── Score computations ────────────────────────────────────────────────────
  const hasEvals = evaluations.length > 0;

  function conditionEvals(style: string, mode: string) {
    return evaluations.filter((e) => e.style === style && e.mode === mode);
  }

  function metricAvg(evals: Evaluation[], key: keyof Evaluation): number | null {
    const vals = evals.map((e) => e[key] as number | null).filter((v): v is number => v != null);
    return avg(vals);
  }

  // Per-condition score for each metric
  const conditionMetrics = CONDITIONS.map(({ key, style, mode, label }) => {
    const evals = conditionEvals(style, mode);
    return {
      key, label, n: evals.length,
      comprehension: metricAvg(evals, 'comprehension_score'),
      factual_recall: metricAvg(evals, 'factual_recall'),
      applied_reasoning: metricAvg(evals, 'applied_reasoning'),
      explanation_quality: metricAvg(evals, 'explanation_quality'),
      interaction_quality: metricAvg(evals, 'interaction_quality'),
    };
  });

  // Comprehension by condition (for bar chart)
  const comprehensionByCondition = conditionMetrics.map(({ key, label, n, comprehension }) => ({
    label, n, value: comprehension, colorClass: CONDITION_COLORS[key],
  }));

  // Style effect: clinical vs analogy
  const clinicalEvals = evaluations.filter((e) => e.style === 'clinical');
  const analogyEvals = evaluations.filter((e) => e.style === 'analogy');
  const clinicalAvg = metricAvg(clinicalEvals, 'comprehension_score');
  const analogyAvg = metricAvg(analogyEvals, 'comprehension_score');
  const styleEffect = (analogyAvg != null && clinicalAvg != null) ? analogyAvg - clinicalAvg : null;

  // Mode effect: static vs dialog
  const staticEvals = evaluations.filter((e) => e.mode === 'static');
  const dialogEvals = evaluations.filter((e) => e.mode === 'dialog');
  const staticAvg = metricAvg(staticEvals, 'comprehension_score');
  const dialogAvg = metricAvg(dialogEvals, 'comprehension_score');
  const modeEffect = (dialogAvg != null && staticAvg != null) ? dialogAvg - staticAvg : null;

  // Overall averages
  const overallComprehension = metricAvg(evaluations, 'comprehension_score');
  const overallFactual = metricAvg(evaluations, 'factual_recall');
  const overallReasoning = metricAvg(evaluations, 'applied_reasoning');
  const overallExplanation = metricAvg(evaluations, 'explanation_quality');

  // ── Persona breakdown ────────────────────────────────────────────────────
  const personaMap = new Map(personas.map((p) => [p.name, p]));

  const LITERACY_LEVELS = ['low', 'marginal', 'adequate'] as const;
  const ANXIETY_LEVELS = ['low', 'moderate', 'high'] as const;

  function breakdownByField(field: 'literacy_level' | 'anxiety', groups: readonly string[]) {
    return groups.map((group) => {
      const evals = evaluations.filter((e) => {
        const p = e.persona_name ? personaMap.get(e.persona_name) : null;
        return p?.[field] === group;
      });
      return { group, n: evals.length, value: metricAvg(evals, 'comprehension_score') };
    });
  }

  const literacyBreakdown = breakdownByField('literacy_level', LITERACY_LEVELS);
  const anxietyBreakdown = breakdownByField('anxiety', ANXIETY_LEVELS);

  // ── ANOVA ─────────────────────────────────────────────────────────────────
  function getScores(style: string, mode: string): number[] {
    return evaluations
      .filter((e) => e.style === style && e.mode === mode)
      .map((e) => e.comprehension_score)
      .filter((v): v is number => v != null);
  }

  const anovaResult = hasEvals ? anova2x2(
    getScores('clinical', 'static'),
    getScores('clinical', 'dialog'),
    getScores('analogy', 'static'),
    getScores('analogy', 'dialog'),
  ) : null;

  if (loading) {
    return (
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header title="Analysis" />
        <div className="flex flex-1 items-center justify-center text-muted-foreground text-sm">Loading…</div>
      </div>
    );
  }

  if (simulations.length === 0) {
    return (
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header title="Analysis" />
        <div className="flex flex-1 items-center justify-center text-muted-foreground">
          <div className="text-center">
            <p className="text-sm font-medium">No simulations yet</p>
            <p className="text-xs mt-1">Run some simulations to see analysis here.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <Header title="Analysis" />
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 max-w-4xl mx-auto space-y-6">

          {/* ── Run stats ── */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <StatCard label="Total runs" value={simulations.length} />
            <StatCard label="Completed" value={completed.length} sub={`${completionRate}% success`} />
            <StatCard label="Evaluated" value={evaluations.length} sub={`of ${completed.length} completed`} />
            <StatCard
              label="Avg duration"
              value={avgDurationAll > 0 ? `${(avgDurationAll / 1000).toFixed(1)}s` : '—'}
              sub="completed only"
            />
          </div>

          {/* Status breakdown */}
          <Card>
            <CardHeader><CardTitle>Status breakdown</CardTitle></CardHeader>
            <CardContent>
              <div className="flex gap-2 h-5">
                {[
                  { count: completed.length, cls: 'bg-green-500' },
                  { count: running.length, cls: 'bg-blue-500' },
                  { count: errors.length, cls: 'bg-red-500' },
                ].map(({ count, cls }) =>
                  count > 0 ? <div key={cls} className={`h-full rounded ${cls}`} style={{ flex: count }} /> : null
                )}
              </div>
              <div className="flex gap-4 mt-2">
                {[
                  { label: 'Completed', count: completed.length, cls: 'bg-green-500' },
                  { label: 'Running', count: running.length, cls: 'bg-blue-500' },
                  { label: 'Error', count: errors.length, cls: 'bg-red-500' },
                ].map(({ label, count, cls }) => (
                  <div key={label} className="flex items-center gap-1.5">
                    <div className={`w-2.5 h-2.5 rounded-sm ${cls}`} />
                    <span className="text-xs text-muted-foreground">{label} ({count})</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Card>
              <CardHeader><CardTitle>Runs per condition</CardTitle></CardHeader>
              <CardContent><BarChart data={countByCondition} maxValue={maxCount} /></CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Avg duration per condition</CardTitle></CardHeader>
              <CardContent>
                {completed.length === 0
                  ? <p className="text-xs text-muted-foreground">No completed simulations yet.</p>
                  : <BarChart data={durationByCondition} maxValue={maxDuration} formatValue={(v) => v > 0 ? `${(v / 1000).toFixed(1)}s` : '—'} />
                }
              </CardContent>
            </Card>
          </div>

          <Separator />

          {/* ── Comprehension scores ── */}
          {!hasEvals ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                <p className="text-sm font-medium">No evaluations yet</p>
                <p className="text-xs mt-1">Run judge evaluations on completed simulations to see score analysis.</p>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Overall score summary */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: 'Avg comprehension', value: overallComprehension },
                  { label: 'Avg factual recall', value: overallFactual },
                  { label: 'Avg applied reasoning', value: overallReasoning },
                  { label: 'Avg explanation quality', value: overallExplanation },
                ].map(({ label, value }) => (
                  <Card size="sm" key={label}>
                    <CardContent className="pt-3 pb-3">
                      <p className="text-xs text-muted-foreground">{label}</p>
                      <p className={`text-2xl font-semibold tabular-nums mt-0.5 ${scoreColor(value)}`}>
                        {value != null ? value.toFixed(1) : '—'}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">out of 100</p>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Comprehension by condition */}
              <Card>
                <CardHeader>
                  <CardTitle>Comprehension by condition</CardTitle>
                  <CardDescription>Mean comprehension score (0–100) per 2×2 cell</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2.5">
                  {comprehensionByCondition.map(({ label, value, n, colorClass }) => (
                    <ScoreBar key={label} label={label} value={value} n={n} colorClass={colorClass} />
                  ))}
                </CardContent>
              </Card>

              {/* Style effect + Mode effect side by side */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Style effect</CardTitle>
                    <CardDescription>Clinical vs analogy explanation style</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <ScoreBar label="Clinical" value={clinicalAvg} n={clinicalEvals.length} colorClass="bg-blue-500" />
                    <ScoreBar label="Analogy" value={analogyAvg} n={analogyEvals.length} colorClass="bg-violet-500" />
                    <div className="flex items-center justify-between pt-1 border-t text-xs text-muted-foreground">
                      <span>Analogy advantage</span>
                      <DeltaBadge delta={styleEffect} />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Mode effect</CardTitle>
                    <CardDescription>Static reading vs interactive dialog</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <ScoreBar label="Static" value={staticAvg} n={staticEvals.length} colorClass="bg-slate-500" />
                    <ScoreBar label="Dialog" value={dialogAvg} n={dialogEvals.length} colorClass="bg-emerald-500" />
                    <div className="flex items-center justify-between pt-1 border-t text-xs text-muted-foreground">
                      <span>Dialog advantage</span>
                      <DeltaBadge delta={modeEffect} />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* All metrics by condition table */}
              <Card>
                <CardHeader>
                  <CardTitle>All metrics by condition</CardTitle>
                  <CardDescription>Mean score per metric across all 4 conditions (n = evaluations per cell)</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2 pr-4 font-medium text-muted-foreground w-36">Metric</th>
                          {conditionMetrics.map(({ key, label, n }) => (
                            <th key={key} className="text-center py-2 px-2 font-medium">
                              <div>{label}</div>
                              <div className="text-muted-foreground font-normal">n={n}</div>
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {SCORE_METRICS.map(({ key, label }) => (
                          <tr key={key} className="border-b last:border-0">
                            <td className="py-2 pr-4 text-muted-foreground">{label}</td>
                            {conditionMetrics.map(({ key: ck }) => {
                              const val = conditionMetrics.find((c) => c.key === ck)?.[key as keyof typeof conditionMetrics[0]] as number | null | undefined;
                              const isNull = val == null;
                              return (
                                <td key={ck} className={`text-center py-2 px-2 tabular-nums font-medium ${scoreColor(isNull ? null : val as number)}`}>
                                  {isNull ? (key === 'interaction_quality' && ck.includes('static') ? 'N/A' : '—') : (val as number).toFixed(1)}
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>

              {/* ── 2×2 ANOVA ── */}
              {anovaResult ? (
                <>
                  <Card>
                    <CardHeader>
                      <CardTitle>2×2 Factorial ANOVA</CardTitle>
                      <CardDescription>
                        Outcome: comprehension score — Style (clinical vs analogy) × Mode (static vs dialog), n={anovaResult.n}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="border-b">
                              {['Source', 'SS', 'df', 'MS', 'F', 'p', "Cohen's d", ''].map((h) => (
                                <th key={h} className={`py-2 px-2 font-medium text-muted-foreground ${h === 'Source' ? 'text-left' : 'text-right'}`}>{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {([
                              { label: 'Style', effect: anovaResult.style },
                              { label: 'Mode', effect: anovaResult.mode },
                              { label: 'Style × Mode', effect: anovaResult.interaction },
                            ] as { label: string; effect: AnovaEffect }[]).map(({ label, effect }) => (
                              <tr key={label} className="border-b">
                                <td className="py-2 px-2 font-medium">{label}</td>
                                <td className="py-2 px-2 text-right tabular-nums">{effect.SS.toFixed(1)}</td>
                                <td className="py-2 px-2 text-right tabular-nums">{effect.df}</td>
                                <td className="py-2 px-2 text-right tabular-nums">{effect.MS.toFixed(1)}</td>
                                <td className="py-2 px-2 text-right tabular-nums font-semibold">{effect.F.toFixed(2)}</td>
                                <td className="py-2 px-2 text-right tabular-nums">{effect.p < 0.001 ? '<.001' : effect.p.toFixed(3)}</td>
                                <td className="py-2 px-2 text-right tabular-nums font-semibold">
                                  <span className={
                                    effect.d >= 0.8 ? 'text-green-600 dark:text-green-400'
                                    : effect.d >= 0.5 ? 'text-amber-600 dark:text-amber-400'
                                    : effect.d >= 0.2 ? 'text-blue-600 dark:text-blue-400'
                                    : 'text-muted-foreground'
                                  }>{effect.d.toFixed(2)}</span>
                                </td>
                                <td className="py-2 px-2 text-center">
                                  {effect.p < 0.001
                                    ? <span className="text-green-600 dark:text-green-400 font-bold">***</span>
                                    : effect.p < 0.01
                                    ? <span className="text-green-600 dark:text-green-400 font-bold">**</span>
                                    : effect.p < 0.05
                                    ? <span className="text-amber-600 dark:text-amber-400 font-bold">*</span>
                                    : <span className="text-muted-foreground">ns</span>}
                                </td>
                              </tr>
                            ))}
                            <tr>
                              <td className="py-2 px-2 text-muted-foreground">Error</td>
                              <td className="py-2 px-2 text-right tabular-nums text-muted-foreground">{anovaResult.error.SS.toFixed(1)}</td>
                              <td className="py-2 px-2 text-right tabular-nums text-muted-foreground">{anovaResult.error.df}</td>
                              <td className="py-2 px-2 text-right tabular-nums text-muted-foreground">{anovaResult.error.MS.toFixed(1)}</td>
                              <td colSpan={4} />
                            </tr>
                          </tbody>
                        </table>
                      </div>
                      <p className="text-xs text-muted-foreground mt-3">* p&lt;.05 &nbsp; ** p&lt;.01 &nbsp; *** p&lt;.001 &nbsp; ns = not significant &nbsp;·&nbsp; Cohen's d: <span className="text-blue-600 dark:text-blue-400">small ≥.2</span> &nbsp;<span className="text-amber-600 dark:text-amber-400">medium ≥.5</span> &nbsp;<span className="text-green-600 dark:text-green-400">large ≥.8</span></p>
                    </CardContent>
                  </Card>

                  {/* Interaction plot */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Interaction plot</CardTitle>
                      <CardDescription>Mean comprehension score per cell — look for crossing lines to detect interaction</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-3 max-w-xs mx-auto">
                        {[
                          { label: 'Clinical + Static', mean: anovaResult.cellMeans.clinicalStatic, n: anovaResult.cellN.clinicalStatic, color: 'bg-blue-500' },
                          { label: 'Clinical + Dialog', mean: anovaResult.cellMeans.clinicalDialog, n: anovaResult.cellN.clinicalDialog, color: 'bg-blue-400' },
                          { label: 'Analogy + Static', mean: anovaResult.cellMeans.analogyStatic, n: anovaResult.cellN.analogyStatic, color: 'bg-violet-500' },
                          { label: 'Analogy + Dialog', mean: anovaResult.cellMeans.analogyDialog, n: anovaResult.cellN.analogyDialog, color: 'bg-violet-400' },
                        ].map(({ label, mean, n, color }) => (
                          <div key={label} className="flex flex-col items-center gap-1 p-3 rounded-lg bg-muted/50">
                            <div className={`w-3 h-3 rounded-full ${color}`} />
                            <span className="text-xs text-muted-foreground text-center leading-tight">{label}</span>
                            <span className={`text-xl font-bold tabular-nums ${scoreColor(mean)}`}>
                              {mean != null ? mean.toFixed(1) : '—'}
                            </span>
                            <span className="text-xs text-muted-foreground">n={n}</span>
                          </div>
                        ))}
                      </div>

                      {/* Interpretation */}
                      <div className="mt-4 space-y-1.5 text-xs text-muted-foreground border-t pt-3">
                        {anovaResult.style.significant && (
                          <p>
                            <span className="font-semibold text-foreground">Style effect:</span>{' '}
                            {(anovaResult.cellMeans.analogyStatic ?? 0) + (anovaResult.cellMeans.analogyDialog ?? 0) >
                             (anovaResult.cellMeans.clinicalStatic ?? 0) + (anovaResult.cellMeans.clinicalDialog ?? 0)
                              ? 'Analogy style produces higher comprehension'
                              : 'Clinical style produces higher comprehension'
                            }{' '}(F={anovaResult.style.F.toFixed(2)}, p={anovaResult.style.p < 0.001 ? '<.001' : anovaResult.style.p.toFixed(3)}).
                          </p>
                        )}
                        {anovaResult.mode.significant && (
                          <p>
                            <span className="font-semibold text-foreground">Mode effect:</span>{' '}
                            {(anovaResult.cellMeans.clinicalDialog ?? 0) + (anovaResult.cellMeans.analogyDialog ?? 0) >
                             (anovaResult.cellMeans.clinicalStatic ?? 0) + (anovaResult.cellMeans.analogyStatic ?? 0)
                              ? 'Dialog mode produces higher comprehension'
                              : 'Static mode produces higher comprehension'
                            }{' '}(F={anovaResult.mode.F.toFixed(2)}, p={anovaResult.mode.p < 0.001 ? '<.001' : anovaResult.mode.p.toFixed(3)}).
                          </p>
                        )}
                        {anovaResult.interaction.significant && (
                          <p>
                            <span className="font-semibold text-foreground">Interaction:</span>{' '}
                            The effect of style depends on mode (F={anovaResult.interaction.F.toFixed(2)}, p={anovaResult.interaction.p < 0.001 ? '<.001' : anovaResult.interaction.p.toFixed(3)}).
                          </p>
                        )}
                        {!anovaResult.style.significant && !anovaResult.mode.significant && !anovaResult.interaction.significant && (
                          <p>No significant main effects or interaction detected at α=0.05.</p>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <Card>
                  <CardContent className="py-5 text-center text-xs text-muted-foreground">
                    ANOVA requires at least one observation per cell (all 4 conditions evaluated).
                  </CardContent>
                </Card>
              )}

              {/* ── Persona breakdown ── */}
              {personas.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>By literacy level</CardTitle>
                      <CardDescription>Mean comprehension score per patient literacy group</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-2.5">
                      {literacyBreakdown.map(({ group, value, n }) => (
                        <ScoreBar
                          key={group}
                          label={group.charAt(0).toUpperCase() + group.slice(1)}
                          value={value}
                          n={n}
                        />
                      ))}
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>By anxiety level</CardTitle>
                      <CardDescription>Mean comprehension score per patient anxiety group</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-2.5">
                      {anxietyBreakdown.map(({ group, value, n }) => (
                        <ScoreBar
                          key={group}
                          label={group.charAt(0).toUpperCase() + group.slice(1)}
                          value={value}
                          n={n}
                        />
                      ))}
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Style × Literacy interaction */}
              {personas.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Style effect by literacy</CardTitle>
                    <CardDescription>Does analogy help more for low-literacy patients?</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left py-2 pr-4 font-medium text-muted-foreground">Literacy</th>
                            <th className="text-right py-2 px-2 font-medium">Clinical</th>
                            <th className="text-right py-2 px-2 font-medium">Analogy</th>
                            <th className="text-right py-2 px-2 font-medium text-muted-foreground">Δ (analogy−clinical)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {LITERACY_LEVELS.map((level) => {
                            const clinEvals = evaluations.filter((e) => {
                              const p = e.persona_name ? personaMap.get(e.persona_name) : null;
                              return p?.literacy_level === level && e.style === 'clinical';
                            });
                            const anaEvals = evaluations.filter((e) => {
                              const p = e.persona_name ? personaMap.get(e.persona_name) : null;
                              return p?.literacy_level === level && e.style === 'analogy';
                            });
                            const clin = metricAvg(clinEvals, 'comprehension_score');
                            const ana = metricAvg(anaEvals, 'comprehension_score');
                            const delta = clin != null && ana != null ? ana - clin : null;
                            return (
                              <tr key={level} className="border-b last:border-0">
                                <td className="py-2 pr-4 font-medium capitalize">{level}</td>
                                <td className="py-2 px-2 text-right tabular-nums text-blue-600 dark:text-blue-400">
                                  {clin != null ? clin.toFixed(1) : '—'}
                                </td>
                                <td className="py-2 px-2 text-right tabular-nums text-violet-600 dark:text-violet-400">
                                  {ana != null ? ana.toFixed(1) : '—'}
                                </td>
                                <td className="py-2 px-2 text-right tabular-nums">
                                  {delta != null
                                    ? <span className={delta > 0 ? 'text-green-600 dark:text-green-400 font-semibold' : 'text-red-600 dark:text-red-400 font-semibold'}>
                                        {delta > 0 ? '+' : ''}{delta.toFixed(1)}
                                      </span>
                                    : <span className="text-muted-foreground">—</span>
                                  }
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}

        </div>
      </div>
    </div>
  );
}
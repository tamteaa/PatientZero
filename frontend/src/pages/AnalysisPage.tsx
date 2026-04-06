import { useState, useEffect } from 'react';
import { Header } from '@/components/common/Header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';
import { getAnalysis } from '@/api/sessions';
import type { AnalysisResult, ScoreStats, MetricKey, GapAnalysis } from '@/api/sessions';
import { API_BASE } from '@/api/client';

// ── Constants ─────────────────────────────────────────────────────────────────

const TRAIT_LEVEL_ORDER = ['low', 'moderate', 'high'];
const VERBOSITY_ORDER = ['terse', 'moderate', 'thorough'];
const AGE_ORDER = ['18–35', '36–55', '56–75', '76+'];

const METRIC_LABELS: Record<MetricKey, string> = {
  comprehension_score: 'Comprehension',
  factual_recall: 'Factual Recall',
  applied_reasoning: 'Applied Reasoning',
  explanation_quality: 'Explanation Quality',
  interaction_quality: 'Interaction Quality',
};

const METRIC_KEYS = Object.keys(METRIC_LABELS) as MetricKey[];

// ── Helpers ───────────────────────────────────────────────────────────────────

function scoreColor(v: number | null): string {
  if (v == null) return 'text-muted-foreground';
  if (v >= 70) return 'text-green-600 dark:text-green-400';
  if (v >= 50) return 'text-amber-600 dark:text-amber-400';
  return 'text-red-600 dark:text-red-400';
}

function scoreBg(v: number | null): string {
  if (v == null) return 'bg-muted';
  if (v >= 70) return 'bg-green-500';
  if (v >= 50) return 'bg-amber-500';
  return 'bg-red-500';
}

function effectLabel(d: number | null): string {
  if (d == null) return '—';
  const abs = Math.abs(d);
  const sign = d > 0 ? '+' : '';
  const mag = abs < 0.2 ? 'negligible' : abs < 0.5 ? 'small' : abs < 0.8 ? 'medium' : 'large';
  return `d=${sign}${d.toFixed(2)} (${mag})`;
}

function sortedEntries(
  groups: Record<string, ScoreStats>,
  order: string[],
): [string, ScoreStats][] {
  return Object.entries(groups).sort(([a], [b]) => {
    const ai = order.indexOf(a);
    const bi = order.indexOf(b);
    if (ai === -1 && bi === -1) return a.localeCompare(b);
    if (ai === -1) return 1;
    if (bi === -1) return -1;
    return ai - bi;
  });
}

// ── Components ────────────────────────────────────────────────────────────────

function ScoreBar({ value }: { value: number | null }) {
  if (value == null) return <span className="text-xs text-muted-foreground">—</span>;
  return (
    <div className="flex items-center gap-1.5 min-w-0">
      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${scoreBg(value)}`} style={{ width: `${value}%` }} />
      </div>
      <span className={`text-xs tabular-nums w-6 text-right shrink-0 font-medium ${scoreColor(value)}`}>
        {value.toFixed(0)}
      </span>
    </div>
  );
}

/** Overall — 5 metrics as rows with bars */
function OverallCard({ stats }: { stats: ScoreStats }) {
  return (
    <Card>
      <CardHeader><CardTitle>Overall scores</CardTitle></CardHeader>
      <CardContent className="space-y-2.5">
        {METRIC_KEYS.map((key) => (
          <div key={key} className="flex items-center gap-3">
            <span className="w-36 shrink-0 text-xs text-muted-foreground truncate">{METRIC_LABELS[key]}</span>
            <div className="flex-1"><ScoreBar value={stats[key].mean} /></div>
            <span className="text-xs text-muted-foreground w-10 text-right shrink-0">n={stats[key].n}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

/**
 * Trait matrix — rows = metrics, columns = trait levels.
 * Shows all 5 scores at once so you can see which metrics shift with the trait.
 */
function TraitMatrixCard({
  title,
  groups,
  order = TRAIT_LEVEL_ORDER,
  effectSizes,
}: {
  title: string;
  groups: Record<string, ScoreStats>;
  order?: string[];
  effectSizes?: Record<MetricKey, { high_vs_low?: number | null; thorough_vs_terse?: number | null }>;
}) {
  const entries = sortedEntries(groups, order);

  if (entries.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
        <CardContent><p className="text-xs text-muted-foreground">No data yet.</p></CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
      <CardContent className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr>
              <th className="text-left text-muted-foreground font-normal pb-2 pr-3 w-32">Metric</th>
              {entries.map(([level]) => (
                <th key={level} className="text-center text-muted-foreground font-normal pb-2 px-2 capitalize min-w-[80px]">
                  {level}
                </th>
              ))}
              {effectSizes && <th className="text-left text-muted-foreground font-normal pb-2 pl-4">Effect size</th>}
            </tr>
          </thead>
          <tbody>
            {METRIC_KEYS.map((metric) => {
              const es = effectSizes?.[metric];
              const d = es && ('high_vs_low' in es ? es.high_vs_low : ('thorough_vs_terse' in es ? es.thorough_vs_terse : null));
              return (
                <tr key={metric} className="border-t border-border/40">
                  <td className="py-1.5 pr-3 text-muted-foreground truncate max-w-[128px]">
                    {METRIC_LABELS[metric]}
                  </td>
                  {entries.map(([level, stats]) => (
                    <td key={level} className="py-1.5 px-2">
                      <ScoreBar value={stats[metric].mean} />
                    </td>
                  ))}
                  {effectSizes && (
                    <td className="py-1.5 pl-4 text-muted-foreground whitespace-nowrap">
                      {effectLabel(d ?? null)}
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
        <div className="mt-2 flex gap-4 text-xs text-muted-foreground">
          {entries.map(([level, stats]) => (
            <span key={level} className="capitalize">
              {level}: n={stats.comprehension_score.n}
            </span>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/** Scenario — comprehension bar per scenario name */
function ScenarioCard({ groups }: { groups: Record<string, ScoreStats> }) {
  const entries = Object.entries(groups).sort(
    ([, a], [, b]) => (b.comprehension_score.mean ?? 0) - (a.comprehension_score.mean ?? 0),
  );

  return (
    <Card>
      <CardHeader><CardTitle>By scenario</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {entries.map(([scenario, stats]) => (
          <div key={scenario}>
            <div className="flex items-center gap-3 mb-0.5">
              <span className="w-48 shrink-0 text-xs text-muted-foreground truncate">{scenario}</span>
              <div className="flex-1"><ScoreBar value={stats.comprehension_score.mean} /></div>
              <span className="text-xs text-muted-foreground w-10 text-right shrink-0">
                n={stats.comprehension_score.n}
              </span>
            </div>
            <div className="flex gap-4 pl-[calc(12rem+0.75rem)] text-xs text-muted-foreground/70">
              {(['factual_recall', 'applied_reasoning'] as MetricKey[]).map((m) => (
                <span key={m}>{METRIC_LABELS[m].split(' ')[0]}: {stats[m].mean?.toFixed(0) ?? '—'}</span>
              ))}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

/** Gap analysis — confidence-comprehension gap rates */
function GapCard({ gap }: { gap: GapAnalysis }) {
  const litEntries = sortedEntries(
    gap.by_literacy as unknown as Record<string, ScoreStats>,
    TRAIT_LEVEL_ORDER,
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Confidence–comprehension gaps</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-xs text-muted-foreground">
          A gap occurs when the patient appears confident but misunderstands, or is uncertain despite understanding.{' '}
          <span className="font-medium text-foreground">
            {gap.gap_rate}% of evaluations ({gap.total_with_gap}) have a detected gap.
          </span>
        </p>

        {Object.keys(gap.by_literacy).length > 0 && (
          <div>
            <p className="text-xs font-medium mb-2">Gap rate by patient literacy</p>
            <div className="space-y-1.5">
              {litEntries.map(([level]) => {
                const g = gap.by_literacy[level];
                if (!g) return null;
                return (
                  <div key={level} className="flex items-center gap-3">
                    <span className="w-20 shrink-0 text-xs text-muted-foreground capitalize">{level}</span>
                    <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                      <div className="h-full rounded-full bg-amber-500" style={{ width: `${g.rate}%` }} />
                    </div>
                    <span className="text-xs tabular-nums text-muted-foreground w-24 text-right shrink-0">
                      {g.rate}% ({g.n_gap}/{g.n})
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {Object.keys(gap.by_doctor_empathy).length > 0 && (
          <div>
            <p className="text-xs font-medium mb-2">Gap rate by doctor empathy</p>
            <div className="space-y-1.5">
              {sortedEntries(gap.by_doctor_empathy as unknown as Record<string, ScoreStats>, TRAIT_LEVEL_ORDER).map(([level]) => {
                const g = gap.by_doctor_empathy[level];
                if (!g) return null;
                return (
                  <div key={level} className="flex items-center gap-3">
                    <span className="w-20 shrink-0 text-xs text-muted-foreground capitalize">{level}</span>
                    <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                      <div className="h-full rounded-full bg-amber-500" style={{ width: `${g.rate}%` }} />
                    </div>
                    <span className="text-xs tabular-nums text-muted-foreground w-24 text-right shrink-0">
                      {g.rate}% ({g.n_gap}/{g.n})
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/** Worst combinations */
function WorstCombosCard({ combos }: { combos: AnalysisResult['worst_combinations'] }) {
  if (combos.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>Worst combinations</CardTitle></CardHeader>
        <CardContent><p className="text-xs text-muted-foreground">No data yet.</p></CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader><CardTitle>Worst combinations (lowest comprehension)</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {combos.map((c, i) => (
          <div key={i} className="py-2 border-b border-border last:border-0">
            <div className="flex items-start justify-between gap-4 mb-1.5">
              <div className="flex flex-wrap gap-1.5">
                <span className="px-1.5 py-0.5 rounded bg-muted text-xs text-muted-foreground">
                  literacy: <span className="font-medium text-foreground capitalize">{c.patient_literacy}</span>
                </span>
                <span className="px-1.5 py-0.5 rounded bg-muted text-xs text-muted-foreground">
                  empathy: <span className="font-medium text-foreground capitalize">{c.doctor_empathy}</span>
                </span>
                {c.doctor_verbosity && c.doctor_verbosity !== '?' && (
                  <span className="px-1.5 py-0.5 rounded bg-muted text-xs text-muted-foreground">
                    verbosity: <span className="font-medium text-foreground capitalize">{c.doctor_verbosity}</span>
                  </span>
                )}
                <span className="px-1.5 py-0.5 rounded bg-muted text-xs text-muted-foreground">
                  {c.scenario}
                </span>
              </div>
              <span className={`text-sm tabular-nums font-bold shrink-0 ${scoreColor(c.mean_comprehension)}`}>
                {c.mean_comprehension.toFixed(0)}
              </span>
            </div>
            <div className="flex gap-4 text-xs text-muted-foreground pl-0.5">
              {METRIC_KEYS.map((m) => (
                <span key={m}>
                  {METRIC_LABELS[m].split(' ')[0]}:{' '}
                  <span className={scoreColor(c.scores[m].mean)}>{c.scores[m].mean?.toFixed(0) ?? '—'}</span>
                </span>
              ))}
              <span className="ml-auto">n={c.n}</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export function AnalysisPage() {
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAnalysis()
      .then(setAnalysis)
      .catch((e) => setError(e?.message ?? 'Failed to load analysis'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <>
        <Header title="Analysis" />
        <div className="flex flex-1 items-center justify-center text-muted-foreground text-sm">Loading…</div>
      </>
    );
  }

  if (error || !analysis) {
    return (
      <>
        <Header title="Analysis" />
        <div className="flex flex-1 items-center justify-center text-muted-foreground text-sm">
          {error ?? 'No data'}
        </div>
      </>
    );
  }

  if (analysis.total_evaluations === 0) {
    return (
      <>
        <Header title="Analysis" />
        <div className="flex flex-1 items-center justify-center text-center text-muted-foreground">
          <div>
            <p className="text-sm font-medium">No evaluations yet</p>
            <p className="text-xs mt-1">Run simulations and judge them to see analysis here.</p>
          </div>
        </div>
      </>
    );
  }

  const es = analysis.effect_sizes;

  return (
    <>
      <Header title="Analysis">
        <Button
          size="sm"
          variant="outline"
          className="gap-1.5"
          onClick={() => window.open(`${API_BASE}/analysis/export.csv`, '_blank')}
        >
          <Download className="h-3.5 w-3.5" />
          Export CSV
        </Button>
      </Header>
      <ScrollArea className="flex-1 min-h-0">
        <div className="p-6 max-w-5xl mx-auto space-y-8">

          <div className="text-xs text-muted-foreground">
            {analysis.total_evaluations} evaluation{analysis.total_evaluations !== 1 ? 's' : ''} analyzed
          </div>

          {/* Overall */}
          <OverallCard stats={analysis.overall} />

          {/* Patient trait breakdowns */}
          <section>
            <h2 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wider">
              Patient traits — all 5 metrics
            </h2>
            <div className="space-y-4">
              <TraitMatrixCard
                title="By literacy level"
                groups={analysis.by_patient_literacy}
                order={TRAIT_LEVEL_ORDER}
                effectSizes={es?.literacy as never}
              />
              <TraitMatrixCard
                title="By anxiety level"
                groups={analysis.by_patient_anxiety}
                order={TRAIT_LEVEL_ORDER}
                effectSizes={es?.anxiety as never}
              />
              {Object.keys(analysis.by_patient_age).length > 0 && (
                <TraitMatrixCard
                  title="By age group"
                  groups={analysis.by_patient_age}
                  order={AGE_ORDER}
                />
              )}
            </div>
          </section>

          {/* Doctor trait breakdowns */}
          <section>
            <h2 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wider">
              Doctor traits — all 5 metrics
            </h2>
            <div className="space-y-4">
              <TraitMatrixCard
                title="By empathy"
                groups={analysis.by_doctor_empathy}
                order={TRAIT_LEVEL_ORDER}
                effectSizes={es?.empathy as never}
              />
              <TraitMatrixCard
                title="By verbosity"
                groups={analysis.by_doctor_verbosity}
                order={VERBOSITY_ORDER}
                effectSizes={es?.verbosity as never}
              />
              <TraitMatrixCard
                title="By comprehension checking"
                groups={analysis.by_doctor_comprehension_checking}
                order={TRAIT_LEVEL_ORDER}
              />
            </div>
          </section>

          {/* Scenario */}
          <ScenarioCard groups={analysis.by_scenario} />

          {/* Gap analysis */}
          {analysis.gap_analysis.total_with_gap > 0 && (
            <GapCard gap={analysis.gap_analysis} />
          )}

          {/* Worst combinations */}
          <WorstCombosCard combos={analysis.worst_combinations} />

        </div>
      </ScrollArea>
    </>
  );
}

import { useState, useEffect } from 'react';
import { Header } from '@/components/common/Header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { listSimulations } from '@/api/sessions';
import type { SimulationSummary } from '@/types/simulation';

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

function BarChart({
  data,
  maxValue,
  formatValue,
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

export function AnalysisPage() {
  const [simulations, setSimulations] = useState<SimulationSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listSimulations()
      .then(setSimulations)
      .finally(() => setLoading(false));
  }, []);

  const completed = simulations.filter((s) => s.state === 'completed');
  const errors = simulations.filter((s) => s.state === 'error');
  const running = simulations.filter((s) => s.state === 'running');

  // Count by condition
  const countByCondition = CONDITIONS.map(({ key, label, style, mode }) => ({
    label,
    value: simulations.filter((s) => s.style === style && s.mode === mode).length,
    colorClass: CONDITION_COLORS[key],
  }));
  const maxCount = Math.max(...countByCondition.map((d) => d.value), 1);

  // Avg duration by condition (completed only)
  const durationByCondition = CONDITIONS.map(({ key, label, style, mode }) => {
    const relevant = completed.filter((s) => s.style === style && s.mode === mode && s.duration_ms != null);
    const avg = relevant.length > 0
      ? relevant.reduce((sum, s) => sum + (s.duration_ms ?? 0), 0) / relevant.length
      : 0;
    return { label, value: avg, colorClass: CONDITION_COLORS[key] };
  });
  const maxDuration = Math.max(...durationByCondition.map((d) => d.value), 1);

  // Persona breakdown
  const personaCounts = simulations.reduce<Record<string, number>>((acc, s) => {
    acc[s.persona_name] = (acc[s.persona_name] ?? 0) + 1;
    return acc;
  }, {});
  const personaData = Object.entries(personaCounts)
    .sort((a, b) => b[1] - a[1])
    .map(([label, value]) => ({ label, value, colorClass: 'bg-emerald-500' }));
  const maxPersona = Math.max(...personaData.map((d) => d.value), 1);

  // Scenario breakdown
  const scenarioCounts = simulations.reduce<Record<string, number>>((acc, s) => {
    acc[s.scenario_name] = (acc[s.scenario_name] ?? 0) + 1;
    return acc;
  }, {});
  const scenarioData = Object.entries(scenarioCounts)
    .sort((a, b) => b[1] - a[1])
    .map(([label, value]) => ({ label, value, colorClass: 'bg-amber-500' }));
  const maxScenario = Math.max(...scenarioData.map((d) => d.value), 1);

  const completionRate = simulations.length > 0
    ? Math.round((completed.length / simulations.length) * 100)
    : 0;

  const avgDurationAll = completed.length > 0
    ? completed.reduce((s, sim) => s + (sim.duration_ms ?? 0), 0) / completed.length
    : 0;

  if (loading) {
    return (
      <>
        <Header title="Analysis" />
        <div className="flex flex-1 items-center justify-center text-muted-foreground text-sm">
          Loading…
        </div>
      </>
    );
  }

  if (simulations.length === 0) {
    return (
      <>
        <Header title="Analysis" />
        <div className="flex flex-1 items-center justify-center text-muted-foreground">
          <div className="text-center">
            <p className="text-sm font-medium">No simulations yet</p>
            <p className="text-xs mt-1">Run some simulations to see analysis here.</p>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Header title="Analysis" />
      <ScrollArea className="flex-1">
        <div className="p-6 max-w-4xl mx-auto space-y-6">

          {/* Summary stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <StatCard label="Total runs" value={simulations.length} />
            <StatCard label="Completed" value={completed.length} sub={`${completionRate}% success`} />
            <StatCard label="Errors" value={errors.length} />
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
                  count > 0 ? (
                    <div
                      key={cls}
                      className={`h-full rounded ${cls}`}
                      style={{ flex: count }}
                      title={`${count}`}
                    />
                  ) : null
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

          {/* Count by condition */}
          <Card>
            <CardHeader><CardTitle>Runs per condition</CardTitle></CardHeader>
            <CardContent>
              <BarChart data={countByCondition} maxValue={maxCount} />
            </CardContent>
          </Card>

          {/* Avg duration by condition */}
          <Card>
            <CardHeader><CardTitle>Avg duration per condition (completed)</CardTitle></CardHeader>
            <CardContent>
              {completed.length === 0 ? (
                <p className="text-xs text-muted-foreground">No completed simulations yet.</p>
              ) : (
                <BarChart
                  data={durationByCondition}
                  maxValue={maxDuration}
                  formatValue={(v) => v > 0 ? `${(v / 1000).toFixed(1)}s` : '—'}
                />
              )}
            </CardContent>
          </Card>

          {/* Persona + Scenario side by side */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {personaData.length > 0 && (
              <Card>
                <CardHeader><CardTitle>Runs by persona</CardTitle></CardHeader>
                <CardContent>
                  <BarChart data={personaData} maxValue={maxPersona} />
                </CardContent>
              </Card>
            )}
            {scenarioData.length > 0 && (
              <Card>
                <CardHeader><CardTitle>Runs by scenario</CardTitle></CardHeader>
                <CardContent>
                  <BarChart data={scenarioData} maxValue={maxScenario} />
                </CardContent>
              </Card>
            )}
          </div>

        </div>
      </ScrollArea>
    </>
  );
}
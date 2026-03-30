import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '@/components/common/Header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Play, FlaskConical, BarChart3 } from 'lucide-react';
import { listSimulations, listEvaluations } from '@/api/sessions';
import type { Evaluation, SimulationSummary } from '@/types/simulation';

const TOTAL_PERSONAS = 12;
const TOTAL_SCENARIOS = 3;
const TOTAL_CONDITIONS = 4;
const TOTAL_POSSIBLE = TOTAL_PERSONAS * TOTAL_SCENARIOS * TOTAL_CONDITIONS; // 144

const CONDITIONS = [
  { key: 'clinical-static', label: 'Clinical + Static', style: 'clinical', mode: 'static', color: 'bg-blue-500' },
  { key: 'clinical-dialog', label: 'Clinical + Dialog', style: 'clinical', mode: 'dialog', color: 'bg-blue-400' },
  { key: 'analogy-static', label: 'Analogy + Static', style: 'analogy', mode: 'static', color: 'bg-violet-500' },
  { key: 'analogy-dialog', label: 'Analogy + Dialog', style: 'analogy', mode: 'dialog', color: 'bg-violet-400' },
];

const STATUS_COLORS: Record<string, string> = {
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  running: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  error: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
};

function StatCard({
  label,
  value,
  sub,
  onClick,
}: {
  label: string;
  value: string | number;
  sub?: string;
  onClick?: () => void;
}) {
  return (
    <Card size="sm" className={onClick ? 'cursor-pointer hover:bg-muted/40 transition-colors' : ''} onClick={onClick}>
      <CardContent className="pt-3 pb-3">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-2xl font-semibold tabular-nums mt-0.5">{value}</p>
        {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
      </CardContent>
    </Card>
  );
}

function CoverageBar({ covered, total }: { covered: number; total: number }) {
  const pct = total > 0 ? (covered / total) * 100 : 0;
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{covered} / {total} combinations run</span>
        <span>{pct.toFixed(0)}%</span>
      </div>
      <div className="h-2.5 w-full bg-muted rounded-full overflow-hidden">
        <div
          className="h-full bg-primary rounded-full transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function DashboardPage() {
  const navigate = useNavigate();
  const [simulations, setSimulations] = useState<SimulationSummary[]>([]);
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([listSimulations(), listEvaluations()])
      .then(([sims, evals]) => {
        setSimulations(sims);
        setEvaluations(evals);
      })
      .finally(() => setLoading(false));
  }, []);

  const completed = simulations.filter((s) => s.state === 'completed');

  // Unique (persona, scenario, style, mode) combinations that have been run
  const uniqueCombinations = new Set(
    simulations.map((s) => `${s.persona_name}|${s.scenario_name}|${s.style}|${s.mode}`)
  );
  const coverageCount = uniqueCombinations.size;

  // Avg comprehension across all evaluations
  const scoredEvals = evaluations.filter((e) => e.comprehension_score != null);
  const avgComprehension = scoredEvals.length > 0
    ? scoredEvals.reduce((sum, e) => sum + (e.comprehension_score ?? 0), 0) / scoredEvals.length
    : null;

  // Avg comprehension per condition
  const conditionScores = CONDITIONS.map(({ key, label, style, mode, color }) => {
    const relevant = evaluations.filter(
      (e) => e.style === style && e.mode === mode && e.comprehension_score != null
    );
    const avg = relevant.length > 0
      ? relevant.reduce((sum, e) => sum + (e.comprehension_score ?? 0), 0) / relevant.length
      : null;
    return { key, label, avg, color, count: relevant.length };
  });
  // Runs per condition (completed)
  const conditionCounts = CONDITIONS.map(({ key, label, style, mode, color }) => ({
    key,
    label,
    color,
    count: completed.filter((s) => s.style === style && s.mode === mode).length,
  }));
  const maxConditionCount = Math.max(...conditionCounts.map((c) => c.count), 1);

  // Recent simulations (last 5)
  const recent = simulations.slice(0, 5);

  if (loading) {
    return (
      <>
        <Header title="Dashboard" />
        <div className="flex flex-1 items-center justify-center text-muted-foreground text-sm">Loading…</div>
      </>
    );
  }

  return (
    <>
      <Header title="Dashboard" />
      <ScrollArea className="flex-1">
        <div className="p-6 max-w-4xl mx-auto space-y-6">

          {/* Quick actions */}
          <div className="flex gap-2">
            <Button size="sm" className="gap-1.5" onClick={() => navigate('/simulations')}>
              <Play className="h-3.5 w-3.5" /> Run Simulation
            </Button>
            <Button size="sm" variant="outline" className="gap-1.5" onClick={() => navigate('/judge')}>
              <FlaskConical className="h-3.5 w-3.5" /> Judge
            </Button>
            <Button size="sm" variant="outline" className="gap-1.5" onClick={() => navigate('/analysis')}>
              <BarChart3 className="h-3.5 w-3.5" /> Analysis
            </Button>
          </div>

          {/* Summary stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <StatCard
              label="Total runs"
              value={simulations.length}
              sub={`${completed.length} completed`}
              onClick={() => navigate('/simulations')}
            />
            <StatCard
              label="Coverage"
              value={`${coverageCount} / ${TOTAL_POSSIBLE}`}
              sub="unique combinations"
            />
            <StatCard
              label="Evaluated"
              value={evaluations.length}
              sub={`of ${completed.length} completed`}
              onClick={() => navigate('/judge')}
            />
            <StatCard
              label="Avg comprehension"
              value={avgComprehension != null ? avgComprehension.toFixed(0) : '—'}
              sub={scoredEvals.length > 0 ? `from ${scoredEvals.length} eval${scoredEvals.length > 1 ? 's' : ''}` : 'no evals yet'}
            />
          </div>

          {/* Experiment coverage */}
          <Card>
            <CardHeader><CardTitle>Experiment coverage</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <CoverageBar covered={coverageCount} total={TOTAL_POSSIBLE} />
              <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-xs text-muted-foreground">
                <div className="flex justify-between">
                  <span>Personas</span>
                  <span className="tabular-nums font-medium text-foreground">
                    {new Set(simulations.map((s) => s.persona_name)).size} / {TOTAL_PERSONAS}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Scenarios</span>
                  <span className="tabular-nums font-medium text-foreground">
                    {new Set(simulations.map((s) => s.scenario_name)).size} / {TOTAL_SCENARIOS}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Conditions run</span>
                  <span className="tabular-nums font-medium text-foreground">
                    {CONDITIONS.filter(({ style, mode }) =>
                      simulations.some((s) => s.style === style && s.mode === mode)
                    ).length} / {TOTAL_CONDITIONS}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Completion rate</span>
                  <span className="tabular-nums font-medium text-foreground">
                    {simulations.length > 0
                      ? `${Math.round((completed.length / simulations.length) * 100)}%`
                      : '—'}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Runs per condition */}
            <Card>
              <CardHeader><CardTitle>Completed runs per condition</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {conditionCounts.map(({ key, label, color, count }) => (
                  <div key={key} className="flex items-center gap-3">
                    <span className="w-32 shrink-0 text-xs text-muted-foreground text-right">{label}</span>
                    <div className="flex-1 h-4 bg-muted rounded overflow-hidden">
                      <div
                        className={`h-full rounded transition-all ${color}`}
                        style={{ width: maxConditionCount > 0 ? `${(count / maxConditionCount) * 100}%` : '0%' }}
                      />
                    </div>
                    <span className="w-6 text-xs tabular-nums text-right">{count}</span>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Avg comprehension per condition */}
            <Card>
              <CardHeader><CardTitle>Avg comprehension per condition</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {conditionScores.map(({ key, label, color, avg, count }) => (
                  <div key={key} className="flex items-center gap-3">
                    <span className="w-32 shrink-0 text-xs text-muted-foreground text-right">{label}</span>
                    <div className="flex-1 h-4 bg-muted rounded overflow-hidden">
                      {avg != null && (
                        <div
                          className={`h-full rounded transition-all ${color}`}
                          style={{ width: `${(avg / 100) * 100}%` }}
                        />
                      )}
                    </div>
                    <span className="w-10 text-xs tabular-nums text-right text-muted-foreground">
                      {avg != null ? `${avg.toFixed(0)} (${count})` : '—'}
                    </span>
                  </div>
                ))}
                {scoredEvals.length === 0 && (
                  <p className="text-xs text-muted-foreground">No evaluations yet — run Judge on completed simulations.</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Recent simulations */}
          {recent.length > 0 && (
            <Card>
              <CardHeader><CardTitle>Recent simulations</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {recent.map((sim) => (
                  <div
                    key={sim.id}
                    className="flex items-center justify-between cursor-pointer hover:bg-muted/40 rounded-lg px-2 py-1.5 transition-colors"
                    onClick={() => navigate(`/simulations/${sim.id}`)}
                  >
                    <div className="flex flex-col gap-0.5 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium truncate">{sim.persona_name}</span>
                        <span className="text-xs text-muted-foreground truncate">{sim.scenario_name}</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span>{sim.style} + {sim.mode}</span>
                        <span>·</span>
                        <span>{new Date(sim.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                    <Badge className={STATUS_COLORS[sim.state] ?? ''}>{sim.state}</Badge>
                  </div>
                ))}
                {simulations.length > 5 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full text-xs text-muted-foreground mt-1"
                    onClick={() => navigate('/simulations')}
                  >
                    View all {simulations.length} simulations
                  </Button>
                )}
              </CardContent>
            </Card>
          )}

          {simulations.length === 0 && (
            <div className="text-center py-12 text-muted-foreground">
              <p className="text-sm font-medium">No simulations yet</p>
              <p className="text-xs mt-1">Click "Run Simulation" to get started.</p>
            </div>
          )}

        </div>
      </ScrollArea>
    </>
  );
}
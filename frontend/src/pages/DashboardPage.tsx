import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '@/components/common/Header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Play, FlaskConical } from 'lucide-react';
import { listSimulations, listEvaluations } from '@/api/sessions';
import type { Evaluation, SimulationSummary } from '@/types/simulation';

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
    <Card className={onClick ? 'cursor-pointer hover:bg-muted/40 transition-colors' : ''} onClick={onClick}>
      <CardContent className="pt-3 pb-3">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-2xl font-semibold tabular-nums mt-0.5">{value}</p>
        {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
      </CardContent>
    </Card>
  );
}


export function DashboardPage() {
  const navigate = useNavigate();
  const { handleError } = useError();
  const [simulations, setSimulations] = useState<SimulationSummary[]>([]);
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      listSimulations(),
      listEvaluations(),
    ])
      .then(([sims, evals]) => {
        setSimulations(sims);
        setEvaluations(evals);
      })
      .catch((err) => handleError(err, 'Failed to load dashboard data'))
      .finally(() => setLoading(false));
  }, []);

  const completed = simulations.filter((s) => s.state === 'completed');

  // Unique (patient, scenario) combinations run so far
  const uniqueCombinations = new Set(
    simulations.map((s) => `${s.persona_name}|${s.scenario_name}`)
  );
  const coverageCount = uniqueCombinations.size;

  // Avg comprehension across all evaluations
  const scoredEvals = evaluations.filter((e) => e.comprehension_score != null);
  const avgComprehension = scoredEvals.length > 0
    ? scoredEvals.reduce((sum, e) => sum + (e.comprehension_score ?? 0), 0) / scoredEvals.length
    : null;

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
              label="Unique runs"
              value={coverageCount}
              sub="patient × scenario pairs"
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
            <CardContent>
              <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-xs text-muted-foreground">
                <div className="flex justify-between">
                  <span>Unique patients</span>
                  <span className="tabular-nums font-medium text-foreground">
                    {new Set(simulations.map((s) => s.persona_name)).size}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Scenarios covered</span>
                  <span className="tabular-nums font-medium text-foreground">
                    {new Set(simulations.map((s) => s.scenario_name)).size}
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

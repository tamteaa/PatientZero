import { useEffect, useState } from 'react';
import { useAtom } from 'jotai';
import { Header } from '@/components/common/Header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Trash2, Plus, Sparkles, Loader2 } from 'lucide-react';
import {
  listExperiments,
  createExperiment,
  deleteExperiment,
  getExperiment,
  getPatientDistribution,
  optimizeExperiment,
} from '@/api/sessions';
import { activeExperimentIdAtom, experimentsAtom } from '@/atoms/experiment';
import { useError } from '@/contexts/ErrorContext';
import type {
  ConditionalDistribution,
  Distribution,
  DoctorDistribution,
  PatientDistribution,
} from '@/types/simulation';

// ── Distribution visualizations ─────────────────────────────────────────────

function DistributionBars({ dist }: { dist: Distribution }) {
  return (
    <div className="space-y-1">
      {Object.entries(dist.weights).map(([label, weight]) => (
        <div key={label} className="flex items-center gap-2 text-xs">
          <span className="w-40 shrink-0 text-right text-muted-foreground truncate" title={label}>
            {label}
          </span>
          <div className="flex-1 h-2 bg-muted rounded overflow-hidden">
            <div
              className="h-full bg-primary/60"
              style={{ width: `${Math.round(weight * 100)}%` }}
            />
          </div>
          <span className="w-10 text-right tabular-nums text-muted-foreground">
            {(weight * 100).toFixed(0)}%
          </span>
        </div>
      ))}
    </div>
  );
}

function ConditionalDistributionBlock({ cond }: { cond: ConditionalDistribution }) {
  return (
    <div className="space-y-3">
      {Object.entries(cond.by_parent).map(([parent, dist]) => (
        <div key={parent} className="space-y-1">
          <div className="text-xs font-medium">{parent}</div>
          <DistributionBars dist={dist} />
        </div>
      ))}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold">{title}</h3>
      {children}
    </div>
  );
}

function PatientDistributionCard({
  dist,
  ageRanges,
}: {
  dist: PatientDistribution;
  ageRanges: Record<string, [number, number]>;
}) {
  const ageWithRanges: Distribution = {
    weights: Object.fromEntries(
      Object.entries(dist.age.weights).map(([label, w]) => {
        const range = ageRanges[label];
        const key = range ? `${label} (${range[0]}–${range[1]})` : label;
        return [key, w];
      })
    ),
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Patient distribution</CardTitle>
        <p className="text-xs text-muted-foreground">
          US adult baseline — Census ACS, NAAL, NHIS
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        <Section title="Age"><DistributionBars dist={ageWithRanges} /></Section>
        <Section title="Education | age"><ConditionalDistributionBlock cond={dist.education_by_age} /></Section>
        <Section title="Literacy | education (NAAL)"><ConditionalDistributionBlock cond={dist.literacy_by_education} /></Section>
        <Section title="Anxiety | age (NHIS)"><ConditionalDistributionBlock cond={dist.anxiety_by_age} /></Section>
        <Section title="Tendency | literacy"><ConditionalDistributionBlock cond={dist.tendency_by_literacy} /></Section>
      </CardContent>
    </Card>
  );
}

function DoctorDistributionCard({ dist }: { dist: DoctorDistribution }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Doctor distribution</CardTitle>
        <p className="text-xs text-muted-foreground">US physician baseline — RIAS, CAHPS</p>
      </CardHeader>
      <CardContent className="space-y-6">
        <Section title="Setting"><DistributionBars dist={dist.setting} /></Section>
        <Section title="Time pressure | setting"><ConditionalDistributionBlock cond={dist.time_pressure_by_setting} /></Section>
        <Section title="Verbosity | time pressure (RIAS)"><ConditionalDistributionBlock cond={dist.verbosity_by_time_pressure} /></Section>
        <Section title="Empathy (CAHPS)"><DistributionBars dist={dist.empathy} /></Section>
        <Section title="Comprehension checking | empathy (RIAS)"><ConditionalDistributionBlock cond={dist.comprehension_check_by_empathy} /></Section>
      </CardContent>
    </Card>
  );
}

// ── Detail pane ──────────────────────────────────────────────────────────────

function DetailPane({
  experiment,
  patientDist,
  ageRanges,
  doctorDist,
  optimizing,
  lastOptImprovement,
  onDelete,
  onOptimize,
}: {
  experiment: { id: string; name: string; created_at: string };
  patientDist: PatientDistribution | null;
  ageRanges: Record<string, [number, number]>;
  doctorDist: DoctorDistribution | null;
  optimizing: boolean;
  lastOptImprovement: number | null;
  onDelete: () => void;
  onOptimize: () => void;
}) {
  return (
    <div className="flex flex-col gap-4 p-6 max-w-3xl">
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-col gap-1 min-w-0">
          <h2 className="text-lg font-semibold">{experiment.name}</h2>
          <p className="text-xs text-muted-foreground">
            Created {new Date(experiment.created_at).toLocaleString()}
          </p>
          {lastOptImprovement != null && (
            <p className="text-xs text-emerald-600 dark:text-emerald-400">
              Last optimize: {lastOptImprovement >= 0 ? '+' : ''}{lastOptImprovement.toFixed(2)} improvement
            </p>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button
            variant="default"
            size="sm"
            className="h-8 text-xs gap-1.5"
            disabled={optimizing}
            onClick={onOptimize}
          >
            {optimizing ? (
              <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Optimizing…</>
            ) : (
              <><Sparkles className="h-3.5 w-3.5" /> Optimize</>
            )}
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-8 text-xs gap-1.5 text-red-600 hover:text-red-700"
            onClick={onDelete}
          >
            <Trash2 className="h-3.5 w-3.5" /> Delete
          </Button>
        </div>
      </div>

      <div className="border-t pt-4 space-y-1">
        <h3 className="text-sm font-semibold">Target distributions</h3>
        <p className="text-xs text-muted-foreground">
          Profiles for simulations in this experiment are sampled from these tables.
        </p>
      </div>

      {patientDist && <PatientDistributionCard dist={patientDist} ageRanges={ageRanges} />}
      {doctorDist && <DoctorDistributionCard dist={doctorDist} />}
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export function ExperimentsPage() {
  const [experiments, setExperiments] = useAtom(experimentsAtom);
  const [activeId, setActiveId] = useAtom(activeExperimentIdAtom);
  const [name, setName] = useState('');
  const [creating, setCreating] = useState(false);
  const [detail, setDetail] = useState<{ patient: PatientDistribution; doctor: DoctorDistribution } | null>(null);
  const [ageRanges, setAgeRanges] = useState<Record<string, [number, number]>>({});
  const [optimizing, setOptimizing] = useState(false);
  const [lastOptImprovement, setLastOptImprovement] = useState<number | null>(null);
  const { handleError } = useError();

  const reload = async () => {
    try {
      const exps = await listExperiments();
      setExperiments(exps);
      if (!activeId || !exps.find((e) => e.id === activeId)) {
        setActiveId(exps[0]?.id ?? null);
      }
    } catch (err) {
      handleError(err, 'Failed to load experiments');
    }
  };

  useEffect(() => {
    reload();
    // Global endpoint is only still used for the age-bucket range labels,
    // which are currently identical across experiments.
    getPatientDistribution()
      .then((r) => setAgeRanges(r.age_bucket_ranges))
      .catch(() => {});
  }, []);

  // Fetch distributions for the selected experiment
  useEffect(() => {
    setLastOptImprovement(null);
    if (!activeId) {
      setDetail(null);
      return;
    }
    getExperiment(activeId)
      .then((d) => setDetail({ patient: d.patient_distribution, doctor: d.doctor_distribution }))
      .catch(() => setDetail(null));
  }, [activeId]);

  const handleCreate = async () => {
    const trimmed = name.trim();
    if (!trimmed) return;
    setCreating(true);
    try {
      const exp = await createExperiment(trimmed);
      setName('');
      await reload();
      setActiveId(exp.id);
    } catch (err) {
      handleError(err, 'Failed to create experiment');
    } finally {
      setCreating(false);
    }
  };

  const handleOptimize = async (id: string) => {
    setOptimizing(true);
    try {
      const result = await optimizeExperiment(id);
      setLastOptImprovement(result.improvement);
    } catch (err) {
      handleError(err, 'Optimization failed');
    } finally {
      setOptimizing(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this experiment and all its simulations?')) return;
    try {
      await deleteExperiment(id);
      if (activeId === id) setActiveId(null);
      await reload();
    } catch (err) {
      handleError(err, 'Failed to delete experiment');
    }
  };

  const selectedExperiment = experiments.find((e) => e.id === activeId) ?? null;

  return (
    <>
      <Header title="Experiments" />
      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Left: list */}
        <div className="flex flex-col w-80 border-r border-border min-h-0">
          <div className="p-3 border-b border-border">
            <div className="flex gap-2">
              <Input
                placeholder="New experiment name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                className="h-8 text-xs"
              />
              <Button
                onClick={handleCreate}
                disabled={creating || !name.trim()}
                size="sm"
                className="h-8 px-2"
              >
                <Plus className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
          <ScrollArea className="flex-1 min-h-0">
            {experiments.length === 0 ? (
              <p className="text-xs text-muted-foreground p-4">No experiments yet.</p>
            ) : (
              <div className="flex flex-col">
                {experiments.map((exp) => {
                  const isSelected = exp.id === activeId;
                  return (
                    <button
                      key={exp.id}
                      onClick={() => setActiveId(exp.id)}
                      className={`flex flex-col gap-0.5 px-4 py-3 text-left border-b border-border/50 transition-colors ${
                        isSelected ? 'bg-muted' : 'hover:bg-muted/50'
                      }`}
                    >
                      <span className="font-medium text-sm truncate">{exp.name}</span>
                      <span className="text-xs text-muted-foreground truncate">
                        {new Date(exp.created_at).toLocaleString()}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </ScrollArea>
        </div>

        {/* Right: detail */}
        <ScrollArea className="flex-1 min-h-0">
          {selectedExperiment ? (
            <DetailPane
              experiment={selectedExperiment}
              patientDist={detail?.patient ?? null}
              ageRanges={ageRanges}
              doctorDist={detail?.doctor ?? null}
              optimizing={optimizing}
              lastOptImprovement={lastOptImprovement}
              onDelete={() => handleDelete(selectedExperiment.id)}
              onOptimize={() => handleOptimize(selectedExperiment.id)}
            />
          ) : (
            <div className="flex items-center justify-center h-full p-6 text-sm text-muted-foreground">
              Create or select an experiment.
            </div>
          )}
        </ScrollArea>
      </div>
    </>
  );
}

import { useEffect, useState } from 'react';
import { useAtom } from 'jotai';
import { Header } from '@/components/common/Header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Trash2, Plus, Sparkles, Loader2, ChevronDown, ChevronRight } from 'lucide-react';
import {
  listExperiments,
  createExperiment,
  deleteExperiment,
  getExperiment,
  getPatientDistribution,
  listOptimizationTargets,
  optimizeExperiment,
  patchExperiment,
  setCurrentOptimizationTarget,
} from '@/api/sessions';
import { activeExperimentIdAtom, experimentsAtom } from '@/atoms/experiment';
import { useError } from '@/contexts/ErrorContext';
import type {
  ConditionalDistribution,
  Distribution,
  DoctorDistribution,
  ExperimentDetail,
  OptimizationTarget,
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
  expDetail,
  patientDist,
  ageRanges,
  doctorDist,
  optimizationTargets,
  targetsLoading,
  activatingTargetId,
  onActivateTarget,
  optimizing,
  lastOptImprovement,
  onDelete,
  onOptimize,
  seedDraft,
  onSeedDraftChange,
  onApplySeed,
  onClearSeed,
  onResetDrawIndex,
  savingSeed,
  showOptimizeAdvanced,
  onToggleOptimizeAdvanced,
  optSeedingMode,
  onOptSeedingMode,
  optNumCandidates,
  onOptNumCandidates,
  optTrialsPerCandidate,
  onOptTrialsPerCandidate,
  optWorstCasesK,
  onOptWorstCasesK,
  optComprehensionWeight,
  onOptComprehensionWeight,
  showPrompts,
  onTogglePrompts,
}: {
  experiment: { id: string; name: string; created_at: string; current_optimization_target_id: string | null; sampling_seed: number | null };
  expDetail: ExperimentDetail | null;
  patientDist: PatientDistribution | null;
  ageRanges: Record<string, [number, number]>;
  doctorDist: DoctorDistribution | null;
  optimizationTargets: OptimizationTarget[];
  targetsLoading: boolean;
  activatingTargetId: string | null;
  onActivateTarget: (targetId: string) => void;
  optimizing: boolean;
  lastOptImprovement: number | null;
  onDelete: () => void;
  onOptimize: () => void;
  seedDraft: string;
  onSeedDraftChange: (v: string) => void;
  onApplySeed: () => void;
  onClearSeed: () => void;
  onResetDrawIndex: () => void;
  savingSeed: boolean;
  showOptimizeAdvanced: boolean;
  onToggleOptimizeAdvanced: () => void;
  optSeedingMode: 'historical_failures' | 'fresh_trials';
  onOptSeedingMode: (v: 'historical_failures' | 'fresh_trials') => void;
  optNumCandidates: number;
  onOptNumCandidates: (v: number) => void;
  optTrialsPerCandidate: number;
  onOptTrialsPerCandidate: (v: number) => void;
  optWorstCasesK: number;
  onOptWorstCasesK: (v: number) => void;
  optComprehensionWeight: number;
  onOptComprehensionWeight: (v: number) => void;
  showPrompts: boolean;
  onTogglePrompts: () => void;
}) {
  const currentTarget = optimizationTargets.find((t) => t.id === experiment.current_optimization_target_id);

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

      <div className="rounded-md border border-border/60 bg-muted/20 px-3 py-2 space-y-2">
        <button
          type="button"
          onClick={onToggleOptimizeAdvanced}
          className="flex items-center gap-1.5 text-xs font-medium text-foreground w-full text-left"
        >
          {showOptimizeAdvanced ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
          Optimize options
        </button>
        {showOptimizeAdvanced && (
          <div className="grid grid-cols-2 gap-2 text-xs pt-1">
            <label className="col-span-2 flex flex-col gap-0.5">
              <span className="text-muted-foreground">Seeding mode</span>
              <select
                className="h-8 rounded-md border border-input bg-background px-2"
                value={optSeedingMode}
                onChange={(e) => onOptSeedingMode(e.target.value as 'historical_failures' | 'fresh_trials')}
              >
                <option value="historical_failures">historical_failures</option>
                <option value="fresh_trials">fresh_trials</option>
              </select>
            </label>
            <label className="flex flex-col gap-0.5">
              <span className="text-muted-foreground">Candidates</span>
              <Input
                type="number"
                min={1}
                max={50}
                className="h-8 text-xs"
                value={optNumCandidates}
                onChange={(e) => onOptNumCandidates(Number(e.target.value))}
              />
            </label>
            <label className="flex flex-col gap-0.5">
              <span className="text-muted-foreground">Trials / candidate</span>
              <Input
                type="number"
                min={1}
                max={100}
                className="h-8 text-xs"
                value={optTrialsPerCandidate}
                onChange={(e) => onOptTrialsPerCandidate(Number(e.target.value))}
              />
            </label>
            <label className="flex flex-col gap-0.5">
              <span className="text-muted-foreground">Worst cases (k)</span>
              <Input
                type="number"
                min={0}
                max={50}
                className="h-8 text-xs"
                value={optWorstCasesK}
                onChange={(e) => onOptWorstCasesK(Number(e.target.value))}
              />
            </label>
            <label className="flex flex-col gap-0.5">
              <span className="text-muted-foreground">Weight: comprehension</span>
              <Input
                type="number"
                min={0}
                max={10}
                step={0.1}
                className="h-8 text-xs"
                value={optComprehensionWeight}
                onChange={(e) => onOptComprehensionWeight(Number(e.target.value))}
              />
            </label>
          </div>
        )}
      </div>

      <div className="border-t pt-4 space-y-2">
        <h3 className="text-sm font-semibold">Reproducible sampling</h3>
        <p className="text-xs text-muted-foreground">
          Set an integer seed so each new simulation draw uses a deterministic stream (API + feedback CLI).
          Reset the draw counter after changing seed or to replay the same sequence.
        </p>
        {expDetail ? (
          <div className="flex flex-wrap items-end gap-2 text-xs">
            <div className="flex flex-col gap-0.5">
              <span className="text-muted-foreground">Next draw index</span>
              <span className="font-mono tabular-nums">{expDetail.sample_draw_index}</span>
            </div>
            <label className="flex flex-col gap-0.5 min-w-[140px]">
              <span className="text-muted-foreground">Seed (integer)</span>
              <Input
                className="h-8 text-xs font-mono"
                placeholder={experiment.sampling_seed != null ? String(experiment.sampling_seed) : 'none'}
                value={seedDraft}
                onChange={(e) => onSeedDraftChange(e.target.value)}
              />
            </label>
            <Button type="button" size="sm" className="h-8 text-xs" disabled={savingSeed} onClick={onApplySeed}>
              Apply seed
            </Button>
            <Button type="button" variant="secondary" size="sm" className="h-8 text-xs" disabled={savingSeed} onClick={onClearSeed}>
              Clear
            </Button>
            <Button type="button" variant="outline" size="sm" className="h-8 text-xs" disabled={savingSeed} onClick={onResetDrawIndex}>
              Reset draw index
            </Button>
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">Loading experiment…</p>
        )}
      </div>

      {currentTarget && (
        <div className="rounded-md border border-border/60 bg-muted/10 px-3 py-2 space-y-2">
          <button
            type="button"
            onClick={onTogglePrompts}
            className="flex items-center gap-1.5 text-xs font-medium w-full text-left"
          >
            {showPrompts ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
            Current target prompts ({currentTarget.kind})
          </button>
          {showPrompts && (
            <div className="space-y-2 max-h-[min(50vh,28rem)] overflow-y-auto">
              {Object.entries(currentTarget.prompts).map(([role, text]) => (
                <div key={role} className="space-y-0.5">
                  <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide">{role}</div>
                  <pre className="text-[11px] whitespace-pre-wrap break-words rounded bg-muted/50 p-2 border border-border/40 font-mono">
                    {text}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="border-t pt-4 space-y-1">
        <h3 className="text-sm font-semibold">Optimization targets</h3>
        <p className="text-xs text-muted-foreground">
          History of prompt sets for this experiment. Use one to make new simulations follow that version
          (revert without deleting newer rows).
        </p>
      </div>
      {targetsLoading ? (
        <p className="text-xs text-muted-foreground">Loading targets…</p>
      ) : optimizationTargets.length === 0 ? (
        <p className="text-xs text-muted-foreground">No targets yet.</p>
      ) : (
        <ul className="space-y-2 text-xs">
          {optimizationTargets.map((t) => {
            const isCurrent = t.id === experiment.current_optimization_target_id;
            return (
              <li
                key={t.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-border/60 px-3 py-2"
              >
                <div className="min-w-0 flex flex-col gap-0.5">
                  <span className="font-mono text-[11px] truncate" title={t.id}>
                    {t.id.slice(0, 8)}…
                  </span>
                  <span className="text-muted-foreground">
                    {t.kind} · {new Date(t.created_at).toLocaleString()}
                    {isCurrent ? ' · current' : ''}
                  </span>
                </div>
                {!isCurrent ? (
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    className="h-7 text-[11px] shrink-0"
                    disabled={activatingTargetId !== null}
                    onClick={() => onActivateTarget(t.id)}
                  >
                    {activatingTargetId === t.id ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      'Use this target'
                    )}
                  </Button>
                ) : null}
              </li>
            );
          })}
        </ul>
      )}

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
  const [expDetail, setExpDetail] = useState<ExperimentDetail | null>(null);
  const [ageRanges, setAgeRanges] = useState<Record<string, [number, number]>>({});
  const [optimizing, setOptimizing] = useState(false);
  const [lastOptImprovement, setLastOptImprovement] = useState<number | null>(null);
  const [optimizationTargets, setOptimizationTargets] = useState<OptimizationTarget[]>([]);
  const [targetsLoading, setTargetsLoading] = useState(false);
  const [activatingTargetId, setActivatingTargetId] = useState<string | null>(null);
  const [seedDraft, setSeedDraft] = useState('');
  const [savingSeed, setSavingSeed] = useState(false);
  const [showOptimizeAdvanced, setShowOptimizeAdvanced] = useState(false);
  const [optSeedingMode, setOptSeedingMode] = useState<'historical_failures' | 'fresh_trials'>('historical_failures');
  const [optNumCandidates, setOptNumCandidates] = useState(5);
  const [optTrialsPerCandidate, setOptTrialsPerCandidate] = useState(10);
  const [optWorstCasesK, setOptWorstCasesK] = useState(5);
  const [optComprehensionWeight, setOptComprehensionWeight] = useState(1);
  const [showPrompts, setShowPrompts] = useState(false);
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

  // Fetch distributions + optimization targets for the selected experiment
  useEffect(() => {
    setLastOptImprovement(null);
    if (!activeId) {
      setExpDetail(null);
      setSeedDraft('');
      setOptimizationTargets([]);
      return;
    }
    getExperiment(activeId)
      .then((d) => {
        setExpDetail(d);
        setSeedDraft(d.sampling_seed != null ? String(d.sampling_seed) : '');
      })
      .catch(() => {
        setExpDetail(null);
        setSeedDraft('');
      });
    setTargetsLoading(true);
    listOptimizationTargets(activeId)
      .then(setOptimizationTargets)
      .catch(() => setOptimizationTargets([]))
      .finally(() => setTargetsLoading(false));
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
      const result = await optimizeExperiment(id, {
        seeding_mode: optSeedingMode,
        num_candidates: optNumCandidates,
        trials_per_candidate: optTrialsPerCandidate,
        worst_cases_k: optWorstCasesK,
        metric_weights: { comprehension_score: optComprehensionWeight },
      });
      setLastOptImprovement(result.improvement);
      const exps = await listExperiments();
      setExperiments(exps);
      const targets = await listOptimizationTargets(id);
      setOptimizationTargets(targets);
      const d = await getExperiment(id);
      setExpDetail(d);
    } catch (err) {
      handleError(err, 'Optimization failed');
    } finally {
      setOptimizing(false);
    }
  };

  const refreshExpDetail = async (id: string) => {
    try {
      const d = await getExperiment(id);
      setExpDetail(d);
      setSeedDraft(d.sampling_seed != null ? String(d.sampling_seed) : '');
    } catch {
      /* skip */
    }
  };

  const handleApplySeed = async () => {
    if (!activeId) return;
    const trimmed = seedDraft.trim();
    if (trimmed === '') {
      handleError(new Error('Enter a non-negative integer, or use Clear to remove the seed'), 'Invalid seed');
      return;
    }
    const n = Number.parseInt(trimmed, 10);
    if (Number.isNaN(n) || n < 0) {
      handleError(new Error('Seed must be a non-negative integer'), 'Invalid seed');
      return;
    }
    setSavingSeed(true);
    try {
      await patchExperiment(activeId, { sampling_seed: n });
      await reload();
      await refreshExpDetail(activeId);
    } catch (err) {
      handleError(err, 'Failed to update seed');
    } finally {
      setSavingSeed(false);
    }
  };

  const handleClearSeed = async () => {
    if (!activeId) return;
    setSavingSeed(true);
    try {
      await patchExperiment(activeId, { sampling_seed: null });
      setSeedDraft('');
      await reload();
      await refreshExpDetail(activeId);
    } catch (err) {
      handleError(err, 'Failed to clear seed');
    } finally {
      setSavingSeed(false);
    }
  };

  const handleResetDrawIndex = async () => {
    if (!activeId) return;
    setSavingSeed(true);
    try {
      await patchExperiment(activeId, { reset_sample_draw_index: true });
      await refreshExpDetail(activeId);
    } catch (err) {
      handleError(err, 'Failed to reset draw index');
    } finally {
      setSavingSeed(false);
    }
  };

  const handleActivateTarget = async (experimentId: string, targetId: string) => {
    setActivatingTargetId(targetId);
    try {
      await setCurrentOptimizationTarget(experimentId, targetId);
      const exps = await listExperiments();
      setExperiments(exps);
      const targets = await listOptimizationTargets(experimentId);
      setOptimizationTargets(targets);
    } catch (err) {
      handleError(err, 'Failed to activate target');
    } finally {
      setActivatingTargetId(null);
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
              expDetail={expDetail}
              patientDist={expDetail?.patient_distribution ?? null}
              ageRanges={ageRanges}
              doctorDist={expDetail?.doctor_distribution ?? null}
              optimizationTargets={optimizationTargets}
              targetsLoading={targetsLoading}
              activatingTargetId={activatingTargetId}
              onActivateTarget={(tid) => handleActivateTarget(selectedExperiment.id, tid)}
              optimizing={optimizing}
              lastOptImprovement={lastOptImprovement}
              onDelete={() => handleDelete(selectedExperiment.id)}
              onOptimize={() => handleOptimize(selectedExperiment.id)}
              seedDraft={seedDraft}
              onSeedDraftChange={setSeedDraft}
              onApplySeed={handleApplySeed}
              onClearSeed={handleClearSeed}
              onResetDrawIndex={handleResetDrawIndex}
              savingSeed={savingSeed}
              showOptimizeAdvanced={showOptimizeAdvanced}
              onToggleOptimizeAdvanced={() => setShowOptimizeAdvanced((v) => !v)}
              optSeedingMode={optSeedingMode}
              onOptSeedingMode={setOptSeedingMode}
              optNumCandidates={optNumCandidates}
              onOptNumCandidates={setOptNumCandidates}
              optTrialsPerCandidate={optTrialsPerCandidate}
              onOptTrialsPerCandidate={setOptTrialsPerCandidate}
              optWorstCasesK={optWorstCasesK}
              onOptWorstCasesK={setOptWorstCasesK}
              optComprehensionWeight={optComprehensionWeight}
              onOptComprehensionWeight={setOptComprehensionWeight}
              showPrompts={showPrompts}
              onTogglePrompts={() => setShowPrompts((v) => !v)}
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

import { useEffect, useState } from 'react';
import { useAtom } from 'jotai';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { listExperiments, patchExperiment } from '@/api/sessions';
import { experimentsAtom } from '@/atoms/experiment';
import { useError } from '@/contexts/ErrorContext';

interface Props {
  experimentId: string;
}

export function ReproducibilityTab({ experimentId }: Props) {
  const { handleError } = useError();
  const [experiments, setExperiments] = useAtom(experimentsAtom);
  const experiment = experiments.find((e) => e.id === experimentId) ?? null;
  const [seedDraft, setSeedDraft] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setSeedDraft(experiment?.sampling_seed != null ? String(experiment.sampling_seed) : '');
  }, [experimentId, experiment?.sampling_seed]);

  const refreshExperiments = async () => {
    setExperiments(await listExperiments());
  };

  const handleApplySeed = async () => {
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
    setSaving(true);
    try {
      await patchExperiment(experimentId, { sampling_seed: n });
      await refreshExperiments();
    } catch (err) {
      handleError(err, 'Failed to update seed');
    } finally {
      setSaving(false);
    }
  };

  const handleClearSeed = async () => {
    setSaving(true);
    try {
      await patchExperiment(experimentId, { sampling_seed: null });
      setSeedDraft('');
      await refreshExperiments();
    } catch (err) {
      handleError(err, 'Failed to clear seed');
    } finally {
      setSaving(false);
    }
  };

  const handleResetDrawIndex = async () => {
    setSaving(true);
    try {
      await patchExperiment(experimentId, { reset_sample_draw_index: true });
      await refreshExperiments();
    } catch (err) {
      handleError(err, 'Failed to reset draw index');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="space-y-1">
        <h3 className="text-sm font-semibold">Reproducible sampling</h3>
        <p className="text-xs text-muted-foreground">
          Set an integer seed so each new simulation draw uses a deterministic stream (API + feedback CLI).
          Reset the draw counter after changing seed or to replay the same sequence.
        </p>
      </div>
      {experiment ? (
        <div className="flex flex-wrap items-end gap-2 text-xs">
          <div className="flex flex-col gap-0.5">
            <span className="text-muted-foreground">Next draw index</span>
            <span className="font-mono tabular-nums">{experiment.sample_draw_index}</span>
          </div>
          <label className="flex flex-col gap-0.5 min-w-[140px]">
            <span className="text-muted-foreground">Seed (integer)</span>
            <Input
              className="h-8 text-xs font-mono"
              placeholder={experiment.sampling_seed != null ? String(experiment.sampling_seed) : 'none'}
              value={seedDraft}
              onChange={(e) => setSeedDraft(e.target.value)}
            />
          </label>
          <Button type="button" size="sm" className="h-8 text-xs" disabled={saving} onClick={handleApplySeed}>
            Apply seed
          </Button>
          <Button type="button" variant="secondary" size="sm" className="h-8 text-xs" disabled={saving} onClick={handleClearSeed}>
            Clear
          </Button>
          <Button type="button" variant="outline" size="sm" className="h-8 text-xs" disabled={saving} onClick={handleResetDrawIndex}>
            Reset draw index
          </Button>
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">Loading experiment…</p>
      )}
    </div>
  );
}

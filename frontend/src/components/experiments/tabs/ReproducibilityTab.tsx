import { useState } from 'react';
import { useAtom } from 'jotai';
import { Button } from '@/components/ui/button';
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
  const [saving, setSaving] = useState(false);

  const refreshExperiments = async () => {
    setExperiments(await listExperiments());
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

  if (!experiment) {
    return <p className="text-xs text-muted-foreground">Loading experiment…</p>;
  }

  const seed = experiment.config.seed;

  return (
    <div className="space-y-3">
      <div className="space-y-1">
        <h3 className="text-sm font-semibold">Reproducible sampling</h3>
        <p className="text-xs text-muted-foreground">
          With a seed set, simulations in this experiment draw profiles from a deterministic
          stream. Reset the draw counter to replay the same sequence from the start.
          Seed is set at experiment creation.
        </p>
      </div>
      <div className="flex flex-wrap items-end gap-4 text-xs">
        <div className="flex flex-col gap-0.5">
          <span className="text-muted-foreground">Seed</span>
          <span className="font-mono tabular-nums">
            {seed != null ? seed : <span className="text-muted-foreground">none</span>}
          </span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-muted-foreground">Next draw index</span>
          <span className="font-mono tabular-nums">{experiment.sample_draw_index}</span>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="h-8 text-xs"
          disabled={saving || seed == null}
          onClick={handleResetDrawIndex}
        >
          Reset draw index
        </Button>
      </div>
    </div>
  );
}

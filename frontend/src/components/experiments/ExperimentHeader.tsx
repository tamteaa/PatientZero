import { Button } from '@/components/ui/button';
import { Trash2 } from 'lucide-react';
import type { Experiment } from '@/types/simulation';

interface Props {
  experiment: Experiment;
  onDelete: () => void;
}

export function ExperimentHeader({ experiment, onDelete }: Props) {
  return (
    <div className="flex items-start justify-between gap-3 pb-3 border-b border-border">
      <div className="flex flex-col gap-1 min-w-0">
        <h2 className="text-lg font-semibold truncate">{experiment.name}</h2>
        <p className="text-xs text-muted-foreground">
          Created {new Date(experiment.created_at).toLocaleString()}
          {experiment.current_optimization_target_id && (
            <>
              {' · '}
              Target{' '}
              <span className="font-mono">
                {experiment.current_optimization_target_id.slice(0, 8)}
              </span>
            </>
          )}
        </p>
      </div>
      <Button
        variant="outline"
        size="sm"
        className="h-8 text-xs gap-1.5 text-red-600 hover:text-red-700 shrink-0"
        onClick={onDelete}
      >
        <Trash2 className="h-3.5 w-3.5" /> Delete
      </Button>
    </div>
  );
}

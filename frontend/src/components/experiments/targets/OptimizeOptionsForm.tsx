import { ChevronDown, ChevronRight } from 'lucide-react';
import { Input } from '@/components/ui/input';

export interface OptimizeOptions {
  seeding_mode: 'historical_failures' | 'fresh_trials';
  num_candidates: number;
  trials_per_candidate: number;
  worst_cases_k: number;
  comprehension_weight: number;
}

export const DEFAULT_OPTIMIZE_OPTIONS: OptimizeOptions = {
  seeding_mode: 'historical_failures',
  num_candidates: 5,
  trials_per_candidate: 10,
  worst_cases_k: 5,
  comprehension_weight: 1,
};

interface Props {
  value: OptimizeOptions;
  onChange: (value: OptimizeOptions) => void;
  expanded: boolean;
  onToggle: () => void;
}

export function OptimizeOptionsForm({ value, onChange, expanded, onToggle }: Props) {
  const update = <K extends keyof OptimizeOptions>(key: K, v: OptimizeOptions[K]) =>
    onChange({ ...value, [key]: v });

  return (
    <div className="rounded-md border border-border/60 bg-muted/20 px-3 py-2 space-y-2">
      <button
        type="button"
        onClick={onToggle}
        className="flex items-center gap-1.5 text-xs font-medium text-foreground w-full text-left"
      >
        {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        Optimize options
      </button>
      {expanded && (
        <div className="grid grid-cols-2 gap-2 text-xs pt-1">
          <label className="col-span-2 flex flex-col gap-0.5">
            <span className="text-muted-foreground">Seeding mode</span>
            <select
              className="h-8 rounded-md border border-input bg-background px-2"
              value={value.seeding_mode}
              onChange={(e) => update('seeding_mode', e.target.value as OptimizeOptions['seeding_mode'])}
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
              value={value.num_candidates}
              onChange={(e) => update('num_candidates', Number(e.target.value))}
            />
          </label>
          <label className="flex flex-col gap-0.5">
            <span className="text-muted-foreground">Trials / candidate</span>
            <Input
              type="number"
              min={1}
              max={100}
              className="h-8 text-xs"
              value={value.trials_per_candidate}
              onChange={(e) => update('trials_per_candidate', Number(e.target.value))}
            />
          </label>
          <label className="flex flex-col gap-0.5">
            <span className="text-muted-foreground">Worst cases (k)</span>
            <Input
              type="number"
              min={0}
              max={50}
              className="h-8 text-xs"
              value={value.worst_cases_k}
              onChange={(e) => update('worst_cases_k', Number(e.target.value))}
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
              value={value.comprehension_weight}
              onChange={(e) => update('comprehension_weight', Number(e.target.value))}
            />
          </label>
        </div>
      )}
    </div>
  );
}

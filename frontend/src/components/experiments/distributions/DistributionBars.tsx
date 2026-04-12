import type { Distribution } from '@/types/simulation';

interface Props {
  dist: Distribution;
}

export function DistributionBars({ dist }: Props) {
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

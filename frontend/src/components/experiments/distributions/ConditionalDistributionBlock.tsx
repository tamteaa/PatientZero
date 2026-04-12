import type { ConditionalDistribution } from '@/types/simulation';
import { DistributionBars } from './DistributionBars';

interface Props {
  cond: ConditionalDistribution;
}

export function ConditionalDistributionBlock({ cond }: Props) {
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

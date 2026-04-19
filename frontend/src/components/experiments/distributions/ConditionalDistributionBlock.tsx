import type { ConditionalNode } from '@/types/simulation';
import { DistributionBars } from './DistributionBars';

interface Props {
  node: ConditionalNode;
}

export function ConditionalDistributionBlock({ node }: Props) {
  return (
    <div className="space-y-3">
      {Object.entries(node.table).map(([parentValue, childWeights]) => (
        <div key={parentValue} className="space-y-1">
          <div className="text-xs font-medium">
            {node.parent} = <span className="font-mono">{parentValue}</span>
          </div>
          <DistributionBars dist={{ weights: childWeights }} />
        </div>
      ))}
    </div>
  );
}

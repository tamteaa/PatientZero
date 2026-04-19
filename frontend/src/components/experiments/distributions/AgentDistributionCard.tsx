import type { ReactNode } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { AgentDistribution } from '@/types/simulation';
import { DistributionBars } from './DistributionBars';
import { ConditionalDistributionBlock } from './ConditionalDistributionBlock';

interface Props {
  agentName: string;
  distribution: AgentDistribution;
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold">{title}</h3>
      {children}
    </div>
  );
}

export function AgentDistributionCard({ agentName, distribution }: Props) {
  const traits = Object.entries(distribution);

  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle className="capitalize">{agentName} distribution</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {traits.length === 0 && (
          <p className="text-xs text-muted-foreground">No traits declared.</p>
        )}
        {traits.map(([trait, node]) =>
          node.kind === 'marginal' ? (
            <Section key={trait} title={trait}>
              <DistributionBars dist={{ weights: node.weights }} />
            </Section>
          ) : (
            <Section key={trait} title={`${trait} | ${node.parent}`}>
              <ConditionalDistributionBlock node={node} />
            </Section>
          ),
        )}
      </CardContent>
    </Card>
  );
}

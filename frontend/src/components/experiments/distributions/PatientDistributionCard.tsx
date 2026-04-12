import type { ReactNode } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { Distribution, PatientDistribution } from '@/types/simulation';
import { DistributionBars } from './DistributionBars';
import { ConditionalDistributionBlock } from './ConditionalDistributionBlock';

interface Props {
  dist: PatientDistribution;
  ageRanges: Record<string, [number, number]>;
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold">{title}</h3>
      {children}
    </div>
  );
}

export function PatientDistributionCard({ dist, ageRanges }: Props) {
  const ageWithRanges: Distribution = {
    weights: Object.fromEntries(
      Object.entries(dist.age.weights).map(([label, w]) => {
        const range = ageRanges[label];
        const key = range ? `${label} (${range[0]}–${range[1]})` : label;
        return [key, w];
      }),
    ),
  };

  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle>Patient distribution</CardTitle>
        <p className="text-xs text-muted-foreground">
          US adult baseline — Census ACS, NAAL, NHIS
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <Section title="Age">
          <DistributionBars dist={ageWithRanges} />
        </Section>
        <Section title="Education | age">
          <ConditionalDistributionBlock cond={dist.education_by_age} />
        </Section>
        <Section title="Literacy | education (NAAL)">
          <ConditionalDistributionBlock cond={dist.literacy_by_education} />
        </Section>
        <Section title="Anxiety | age (NHIS)">
          <ConditionalDistributionBlock cond={dist.anxiety_by_age} />
        </Section>
        <Section title="Tendency | literacy">
          <ConditionalDistributionBlock cond={dist.tendency_by_literacy} />
        </Section>
      </CardContent>
    </Card>
  );
}

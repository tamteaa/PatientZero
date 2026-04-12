import type { ReactNode } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { DoctorDistribution } from '@/types/simulation';
import { DistributionBars } from './DistributionBars';
import { ConditionalDistributionBlock } from './ConditionalDistributionBlock';

interface Props {
  dist: DoctorDistribution;
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold">{title}</h3>
      {children}
    </div>
  );
}

export function DoctorDistributionCard({ dist }: Props) {
  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle>Doctor distribution</CardTitle>
        <p className="text-xs text-muted-foreground">US physician baseline — RIAS, CAHPS</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <Section title="Setting">
          <DistributionBars dist={dist.setting} />
        </Section>
        <Section title="Time pressure | setting">
          <ConditionalDistributionBlock cond={dist.time_pressure_by_setting} />
        </Section>
        <Section title="Verbosity | time pressure (RIAS)">
          <ConditionalDistributionBlock cond={dist.verbosity_by_time_pressure} />
        </Section>
        <Section title="Empathy (CAHPS)">
          <DistributionBars dist={dist.empathy} />
        </Section>
        <Section title="Comprehension checking | empathy (RIAS)">
          <ConditionalDistributionBlock cond={dist.comprehension_check_by_empathy} />
        </Section>
      </CardContent>
    </Card>
  );
}

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { SimulationsTab } from './tabs/SimulationsTab';
import { TargetsTab } from './tabs/TargetsTab';
import { DistributionsTab } from './tabs/DistributionsTab';
import { ReproducibilityTab } from './tabs/ReproducibilityTab';

interface Props {
  experimentId: string;
  refreshKey: number;
  onRefresh: () => void;
}

export function ExperimentTabs({ experimentId, refreshKey, onRefresh }: Props) {
  return (
    <Tabs defaultValue="simulations">
      <TabsList>
        <TabsTrigger value="simulations">Simulations</TabsTrigger>
        <TabsTrigger value="targets">Targets</TabsTrigger>
        <TabsTrigger value="distributions">Distributions</TabsTrigger>
        <TabsTrigger value="reproducibility">Reproducibility</TabsTrigger>
      </TabsList>
      <TabsContent value="simulations" className="pt-4">
        <SimulationsTab
          experimentId={experimentId}
          refreshKey={refreshKey}
          onRefresh={onRefresh}
        />
      </TabsContent>
      <TabsContent value="targets" className="pt-4">
        <TargetsTab experimentId={experimentId} />
      </TabsContent>
      <TabsContent value="distributions" className="pt-4">
        <DistributionsTab experimentId={experimentId} />
      </TabsContent>
      <TabsContent value="reproducibility" className="pt-4">
        <ReproducibilityTab experimentId={experimentId} />
      </TabsContent>
    </Tabs>
  );
}

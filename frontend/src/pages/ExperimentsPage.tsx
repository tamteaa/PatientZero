import { useEffect, useState } from 'react';
import { useAtom } from 'jotai';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ExperimentHeader } from '@/components/experiments/ExperimentHeader';
import { ExperimentSummary } from '@/components/experiments/ExperimentSummary';
import { ExperimentTabs } from '@/components/experiments/ExperimentTabs';
import { deleteExperiment, listExperiments } from '@/api/sessions';
import { activeExperimentIdAtom, experimentsAtom } from '@/atoms/experiment';
import { useError } from '@/contexts/ErrorContext';

export function ExperimentsPage() {
  const [experiments, setExperiments] = useAtom(experimentsAtom);
  const [activeId, setActiveId] = useAtom(activeExperimentIdAtom);
  const [refreshKey, setRefreshKey] = useState(0);
  const { handleError } = useError();

  useEffect(() => {
    listExperiments()
      .then((exps) => {
        setExperiments(exps);
        if (!activeId || !exps.find((e) => e.id === activeId)) {
          setActiveId(exps[0]?.id ?? null);
        }
      })
      .catch((err) => handleError(err, 'Failed to load experiments'));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleDelete = async () => {
    if (!activeId) return;
    if (!confirm('Delete this experiment and all its simulations?')) return;
    try {
      await deleteExperiment(activeId);
      const exps = await listExperiments();
      setExperiments(exps);
      setActiveId(exps[0]?.id ?? null);
    } catch (err) {
      handleError(err, 'Failed to delete experiment');
    }
  };

  const selectedExperiment = experiments.find((e) => e.id === activeId) ?? null;

  return (
    <ScrollArea className="flex-1 min-h-0 h-full">
      {selectedExperiment ? (
        <div className="p-4 w-full space-y-3">
          <ExperimentHeader experiment={selectedExperiment} onDelete={handleDelete} />
          <ExperimentSummary
            experimentId={selectedExperiment.id}
            refreshKey={refreshKey}
          />
          <ExperimentTabs
            experimentId={selectedExperiment.id}
            refreshKey={refreshKey}
            onRefresh={() => setRefreshKey((k) => k + 1)}
          />
        </div>
      ) : (
        <div className="flex items-center justify-center h-full p-4 text-sm text-muted-foreground">
          Create an experiment from the sidebar.
        </div>
      )}
    </ScrollArea>
  );
}

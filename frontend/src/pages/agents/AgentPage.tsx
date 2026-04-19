import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useAtom, useAtomValue } from 'jotai';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AgentView, JudgeView } from '@/components/agents/AgentConfigView';
import { getExperimentAgents } from '@/api/sessions';
import { agentsConfigAtom } from '@/atoms/agents';
import { activeExperimentIdAtom } from '@/atoms/experiment';
import { useError } from '@/contexts/ErrorContext';

export function AgentPage() {
  const { agentName } = useParams<{ agentName: string }>();
  const activeExperimentId = useAtomValue(activeExperimentIdAtom);
  const [config, setConfig] = useAtom(agentsConfigAtom);
  const { handleError } = useError();

  useEffect(() => {
    if (!activeExperimentId) return;
    setConfig(null);
    getExperimentAgents(activeExperimentId)
      .then(setConfig)
      .catch((err: unknown) => handleError(err, 'Failed to load agent config'));
  }, [activeExperimentId, setConfig, handleError]);

  if (!activeExperimentId) {
    return (
      <div className="flex-1 p-4 text-sm text-muted-foreground">
        Select an experiment in the sidebar to view its agents.
      </div>
    );
  }

  if (!config) {
    return (
      <div className="flex-1 p-4 text-sm text-muted-foreground">Loading…</div>
    );
  }

  const isJudge = agentName === 'judge';
  const agent = config.agents.find((a) => a.name === agentName);

  return (
    <ScrollArea className="flex-1 min-h-0 h-full">
      <div className="p-4 max-w-4xl mx-auto">
        {isJudge ? (
          <JudgeView
            rubric={config.judge.rubric}
            instructions={config.judge.instructions}
            model={config.judge.model}
          />
        ) : agent ? (
          <AgentView name={agent.name} prompt={agent.prompt} model={agent.model} />
        ) : (
          <p className="text-sm text-muted-foreground">
            No agent named <span className="font-mono">{agentName}</span> in this experiment.
          </p>
        )}
      </div>
    </ScrollArea>
  );
}

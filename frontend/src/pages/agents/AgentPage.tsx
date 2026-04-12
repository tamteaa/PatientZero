import { useEffect } from 'react';
import { useAtom } from 'jotai';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AgentConfigView } from '@/components/agents/AgentConfigView';
import { getAgentsConfig } from '@/api/sessions';
import { agentsConfigAtom } from '@/atoms/agents';
import { useError } from '@/contexts/ErrorContext';
import type { AgentName } from '@/types/agents';

interface Props {
  agent: AgentName;
}

export function AgentPage({ agent }: Props) {
  const [config, setConfig] = useAtom(agentsConfigAtom);
  const { handleError } = useError();

  useEffect(() => {
    if (config) return;
    getAgentsConfig()
      .then(setConfig)
      .catch((err) => handleError(err, 'Failed to load agent config'));
  }, [config, setConfig, handleError]);

  return (
    <ScrollArea className="flex-1 min-h-0 h-full">
      <div className="p-4 max-w-4xl mx-auto">
        {config ? (
          <AgentConfigView agent={config[agent]} />
        ) : (
          <p className="text-sm text-muted-foreground">Loading…</p>
        )}
      </div>
    </ScrollArea>
  );
}

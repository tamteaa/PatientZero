import { useEffect, useState } from 'react';
import { useAtomValue } from 'jotai';
import { getAgentDistribution } from '@/api/sessions';
import { experimentsAtom } from '@/atoms/experiment';
import { useError } from '@/contexts/ErrorContext';
import type { AgentDistribution } from '@/types/simulation';
import { AgentDistributionCard } from '../distributions/AgentDistributionCard';

interface Props {
  experimentId: string;
}

export function DistributionsTab({ experimentId }: Props) {
  const { handleError } = useError();
  const experiments = useAtomValue(experimentsAtom);
  const experiment = experiments.find((e) => e.id === experimentId) ?? null;
  const [fetched, setFetched] = useState<Record<string, AgentDistribution>>({});

  useEffect(() => {
    if (!experiment) return;
    setFetched({});
    Promise.all(
      experiment.config.agents.map((a) =>
        getAgentDistribution(experimentId, a.name)
          .then((r) => [a.name, r.distribution] as const)
          .catch((err) => {
            handleError(err, `Failed to load distribution for ${a.name}`);
            return null;
          }),
      ),
    ).then((pairs) => {
      const next: Record<string, AgentDistribution> = {};
      for (const p of pairs) if (p) next[p[0]] = p[1];
      setFetched(next);
    });
  }, [experimentId, experiment?.config.agents.length]);

  if (!experiment) {
    return <p className="text-xs text-muted-foreground">Loading distributions…</p>;
  }

  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <h3 className="text-sm font-semibold">Target distributions</h3>
        <p className="text-xs text-muted-foreground">
          Profiles for simulations in this experiment are sampled from these tables.
        </p>
      </div>
      {experiment.config.agents.map((a) => {
        const dist = fetched[a.name] ?? a.distribution;
        return (
          <AgentDistributionCard
            key={a.name}
            agentName={a.name}
            distribution={dist}
          />
        );
      })}
    </div>
  );
}

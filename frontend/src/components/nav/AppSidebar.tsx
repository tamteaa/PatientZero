import { useEffect } from 'react';
import { useAtom } from 'jotai';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { NavItem } from './NavItem';
import {
  Play,
  LayoutDashboard,
  MessageSquare,
  Scale,
  BarChart2,
  Settings,
  FlaskConical,
} from 'lucide-react';
import { listModels, listExperiments } from '@/api/sessions';
import { availableModelsAtom, globalModelAtom } from '@/atoms/model';
import { activeExperimentIdAtom, experimentsAtom } from '@/atoms/experiment';

export function AppSidebar() {
  const [models, setModels] = useAtom(availableModelsAtom);
  const [model, setModel] = useAtom(globalModelAtom);
  const [experiments, setExperiments] = useAtom(experimentsAtom);
  const [activeExperimentId, setActiveExperimentId] = useAtom(activeExperimentIdAtom);

  useEffect(() => {
    if (models.length === 0) {
      listModels()
        .then((ms) => {
          setModels(ms);
          if (ms.length > 0 && !ms.includes(model)) setModel(ms[0]);
        })
        .catch(() => {});
    }
    listExperiments()
      .then((exps) => {
        setExperiments(exps);
        // If current active id is missing from the list, fall back to the first one (or null).
        if (!activeExperimentId || !exps.find((e) => e.id === activeExperimentId)) {
          setActiveExperimentId(exps[0]?.id ?? null);
        }
      })
      .catch(() => {});
  }, []);

  const hasExperiments = experiments.length > 0;

  return (
    <div className="flex h-full w-64 flex-col border-r border-border bg-muted/30">
      <div className="flex h-12 items-center border-b border-border px-4">
        <span className="text-sm font-bold">PatientZero</span>
      </div>
      <div className="border-b border-border p-3">
        <label className="text-xs text-muted-foreground">Experiment</label>
        <Select
          value={activeExperimentId ?? ''}
          onValueChange={(v) => { if (v) setActiveExperimentId(v); }}
          disabled={!hasExperiments}
        >
          <SelectTrigger className="w-full h-9 text-xs mt-1">
            <SelectValue placeholder={hasExperiments ? 'Select…' : 'No experiments'}>
              {(value: string) =>
                experiments.find((e) => e.id === value)?.name ?? (hasExperiments ? 'Select…' : 'No experiments')
              }
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {experiments.map((e) => (
              <SelectItem key={e.id} value={e.id}>{e.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-1 p-3">
          <NavItem to="/dashboard" icon={LayoutDashboard} label="Dashboard" />
          <NavItem to="/experiments" icon={FlaskConical} label="Experiments" />
          <NavItem to="/simulations" icon={Play} label="Simulations" />
          <NavItem to="/judge" icon={Scale} label="Judge" />
          <NavItem to="/analysis" icon={BarChart2} label="Analysis" />
        </div>
      </ScrollArea>
      <div className="flex flex-col gap-1 px-3 pb-3">
        <NavItem to="/chat" icon={MessageSquare} label="Chat" />
        <NavItem to="/settings" icon={Settings} label="Settings" />
      </div>
      <div className="border-t border-border p-3">
        <label className="text-xs text-muted-foreground">Model</label>
        <Select value={model} onValueChange={(v) => { if (v) setModel(v); }}>
          <SelectTrigger className="w-full h-9 text-xs mt-1">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {models.map((m) => (
              <SelectItem key={m} value={m}>{m}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}

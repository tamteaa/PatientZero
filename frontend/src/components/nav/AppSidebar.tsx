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
  MessageSquare,
  Settings,
  LayoutDashboard,
  Stethoscope,
  User,
  Gavel,
} from 'lucide-react';
import { listModels, listExperiments } from '@/api/sessions';
import { availableModelsAtom, globalModelAtom } from '@/atoms/model';
import { activeExperimentIdAtom, experimentsAtom } from '@/atoms/experiment';
import { NewExperimentDialog } from '@/components/experiments/NewExperimentDialog';

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
    <div className="flex h-full w-56 flex-col border-r border-border bg-muted/30">
      <div className="flex h-10 items-center border-b border-border px-3">
        <span className="text-sm font-bold">PatientZero</span>
      </div>
      <div className="border-b border-border p-2 space-y-1">
        <label className="text-[10px] text-muted-foreground">Experiment</label>
        <Select
          value={activeExperimentId ?? ''}
          onValueChange={(v) => { if (v) setActiveExperimentId(v); }}
          disabled={!hasExperiments}
        >
          <SelectTrigger className="w-full h-8 text-xs">
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
        <NewExperimentDialog />
      </div>
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-0.5 p-2">
          <NavItem to="/experiments" icon={LayoutDashboard} label="Dashboard" />
          <div className="mt-2 px-2 pb-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            Agents
          </div>
          <NavItem to="/agents/doctor" icon={Stethoscope} label="Doctor" />
          <NavItem to="/agents/patient" icon={User} label="Patient" />
          <NavItem to="/agents/judge" icon={Gavel} label="Judge" />
        </div>
      </ScrollArea>
      <div className="flex flex-col gap-0.5 px-2 pb-2">
        <NavItem to="/chat" icon={MessageSquare} label="Chat" />
        <NavItem to="/settings" icon={Settings} label="Settings" />
      </div>
      <div className="border-t border-border p-2">
        <label className="text-[10px] text-muted-foreground">Model</label>
        <Select value={model} onValueChange={(v) => { if (v) setModel(v); }}>
          <SelectTrigger className="w-full h-8 text-xs mt-0.5">
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

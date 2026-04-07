import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useError } from '@/contexts/ErrorContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Play, Loader2, Trash2, Shuffle } from 'lucide-react';
import {
  startSimulation,
  listModels,
  listScenarios,
  listSimulations,
  deleteSimulation,
} from '@/api/sessions';
import type { Scenario, SimulationSummary } from '@/types/simulation';

const STATUS_COLOR: Record<string, string> = {
  running: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  error: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
};

const ANY = 'any';

function TraitSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs text-muted-foreground">{label}</label>
      <Select value={value} onValueChange={(v) => onChange(v ?? ANY)}>
        <SelectTrigger className="w-32 h-9 text-xs capitalize">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ANY}>
            <span className="flex items-center gap-1.5 text-muted-foreground">
              <Shuffle className="h-3 w-3" /> any
            </span>
          </SelectItem>
          {options.map((o) => (
            <SelectItem key={o} value={o} className="capitalize">{o}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

export function SimulationsPage() {
  const navigate = useNavigate();
  const { handleError } = useError();

  const [scenariosList, setScenariosList] = useState<Scenario[]>([]);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [simulations, setSimulations] = useState<SimulationSummary[]>([]);

  const [scenarioName, setScenarioName] = useState('random');
  const [model, setModel] = useState('');
  const [maxTurns, setMaxTurns] = useState('');
  const [patientLiteracy, setPatientLiteracy] = useState(ANY);
  const [patientAnxiety, setPatientAnxiety] = useState(ANY);
  const [doctorEmpathy, setDoctorEmpathy] = useState(ANY);
  const [doctorVerbosity, setDoctorVerbosity] = useState(ANY);
  const [isLaunching, setIsLaunching] = useState(false);

  const fetchSimulations = useCallback(() => {
    listSimulations().then(setSimulations).catch((err) => handleError(err, 'Failed to load simulations'));
  }, [handleError]);

  useEffect(() => {
    listScenarios().then(setScenariosList).catch(() => {});
    listModels().then((m) => {
      setAvailableModels(m);
      if (m.length > 0) setModel(m[0]);
    }).catch(() => {});
    fetchSimulations();
  }, []);

  const handleRun = useCallback(async () => {
    if (!scenarioName || !model) return;
    const parsedMaxTurns = maxTurns ? parseInt(maxTurns, 10) : undefined;
    setIsLaunching(true);
    try {
      const simId = await startSimulation({
        ...(scenarioName !== 'random' ? { scenario_name: scenarioName } : {}),
        model,
        ...(parsedMaxTurns && !isNaN(parsedMaxTurns) ? { max_turns: parsedMaxTurns } : {}),
        ...(patientLiteracy !== ANY ? { patient_literacy: patientLiteracy } : {}),
        ...(patientAnxiety  !== ANY ? { patient_anxiety:  patientAnxiety  } : {}),
        ...(doctorEmpathy   !== ANY ? { doctor_empathy:   doctorEmpathy   } : {}),
        ...(doctorVerbosity !== ANY ? { doctor_verbosity: doctorVerbosity } : {}),
      });
      navigate(`/simulations/${simId}`);
    } catch (err) {
      handleError(err, 'Failed to start simulation');
      setIsLaunching(false);
    }
  }, [scenarioName, model, maxTurns, patientLiteracy, patientAnxiety, doctorEmpathy, doctorVerbosity, navigate, handleError]);

  const handleDelete = useCallback(async (id: string) => {
    try {
      await deleteSimulation(id);
      fetchSimulations();
    } catch {
      alert('Failed to delete simulation.');
    }
  }, [fetchSimulations]);

  const canRun = !!model && !isLaunching;

  return (
    <ScrollArea className="flex-1 min-h-0">
      <div className="p-6 max-w-5xl mx-auto space-y-6">

        {/* New simulation form */}
        <Card>
          <CardContent className="pt-5 pb-4 space-y-4">
            <h3 className="text-sm font-semibold">New Simulation</h3>

            {/* Scenario + model + max turns */}
            <div className="flex items-end gap-3 flex-wrap">
              <div className="flex flex-col gap-1">
                <label className="text-xs text-muted-foreground">Scenario</label>
                <Select value={scenarioName} onValueChange={(v) => setScenarioName(v ?? 'random')}>
                  <SelectTrigger className="w-64 h-9 text-xs"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="random">
                      <span className="flex items-center gap-1.5 text-muted-foreground">
                        <Shuffle className="h-3 w-3" /> random
                      </span>
                    </SelectItem>
                    {scenariosList.map((s) => (
                      <SelectItem key={s.name} value={s.name}>{s.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-muted-foreground">Model</label>
                <Select value={model} onValueChange={(v) => { if (v) setModel(v); }}>
                  <SelectTrigger className="w-44 h-9 text-xs"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {availableModels.map((m) => (
                      <SelectItem key={m} value={m}>{m}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-muted-foreground">Max turns</label>
                <Input
                  type="number"
                  min={1}
                  max={20}
                  placeholder="8"
                  value={maxTurns}
                  onChange={(e) => setMaxTurns(e.target.value)}
                  className="w-20 h-9 text-xs"
                />
              </div>
            </div>

            {/* Trait constraints */}
            <div className="border-t border-border pt-3">
              <p className="text-xs text-muted-foreground mb-2.5">
                Trait constraints <span className="italic">(any = sampled from real distributions)</span>
              </p>
              <div className="flex items-end gap-3 flex-wrap">
                <div className="flex flex-col gap-2">
                  <span className="text-xs font-medium">Patient</span>
                  <div className="flex gap-2">
                    <TraitSelect
                      label="Literacy"
                      value={patientLiteracy}
                      onChange={setPatientLiteracy}
                      options={['low', 'moderate', 'high']}
                    />
                    <TraitSelect
                      label="Anxiety"
                      value={patientAnxiety}
                      onChange={setPatientAnxiety}
                      options={['low', 'moderate', 'high']}
                    />
                  </div>
                </div>

                <div className="flex flex-col gap-2">
                  <span className="text-xs font-medium">Doctor</span>
                  <div className="flex gap-2">
                    <TraitSelect
                      label="Empathy"
                      value={doctorEmpathy}
                      onChange={setDoctorEmpathy}
                      options={['low', 'moderate', 'high']}
                    />
                    <TraitSelect
                      label="Verbosity"
                      value={doctorVerbosity}
                      onChange={setDoctorVerbosity}
                      options={['terse', 'moderate', 'thorough']}
                    />
                  </div>
                </div>

                <Button onClick={handleRun} disabled={!canRun} size="sm" className="gap-1.5 h-9 self-end">
                  {isLaunching
                    ? <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Running...</>
                    : <><Play className="h-3.5 w-3.5" /> Run</>
                  }
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Simulation list */}
        {simulations.length === 0 ? (
          <p className="text-muted-foreground text-sm">No simulations yet. Configure and run one above.</p>
        ) : (
          <div className="flex flex-col gap-3">
            {simulations.map((sim) => (
              <Card
                key={sim.id}
                className="cursor-pointer hover:bg-muted/40 transition-colors"
                onClick={() => navigate(`/simulations/${sim.id}`)}
              >
                <CardContent className="flex items-center justify-between py-3">
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{sim.persona_name}</span>
                      <span className="text-muted-foreground text-xs">—</span>
                      <span className="text-sm text-muted-foreground">{sim.scenario_name}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{sim.model}</span>
                      <span>·</span>
                      <span>{new Date(sim.created_at).toLocaleString()}</span>
                      {sim.duration_ms != null && (
                        <>
                          <span>·</span>
                          <span>{(sim.duration_ms / 1000).toFixed(1)}s</span>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={STATUS_COLOR[sim.state] || ''}>{sim.state}</Badge>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 text-muted-foreground hover:text-red-500"
                      onClick={(e) => { e.stopPropagation(); handleDelete(sim.id); }}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </ScrollArea>
  );
}

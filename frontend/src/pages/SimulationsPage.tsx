import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '@/components/common/Header';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Play, Loader2, Trash2 } from 'lucide-react';
import {
  runSimulation,
  listModels,
  listPersonas,
  listScenarios,
  listSimulations,
  deleteSimulation,
} from '@/api/sessions';
import type {
  Persona,
  Scenario,
  SimulationSummary,
  Style,
  Mode,
} from '@/types/simulation';

const conditions: { id: string; label: string; style: Style; mode: Mode }[] = [
  { id: 'clinical-static', label: 'Clinical + Static', style: 'clinical', mode: 'static' },
  { id: 'clinical-dialog', label: 'Clinical + Dialog', style: 'clinical', mode: 'dialog' },
  { id: 'analogy-static', label: 'Analogy + Static', style: 'analogy', mode: 'static' },
  { id: 'analogy-dialog', label: 'Analogy + Dialog', style: 'analogy', mode: 'dialog' },
];

const statusColor: Record<string, string> = {
  running: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  error: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
};

export function SimulationsPage() {
  const navigate = useNavigate();

  const [personas, setPersonas] = useState<Persona[]>([]);
  const [scenariosList, setScenariosList] = useState<Scenario[]>([]);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [simulations, setSimulations] = useState<SimulationSummary[]>([]);

  const [personaIdx, setPersonaIdx] = useState<number>(0);
  const [conditionIdx, setConditionIdx] = useState<number>(0);
  const [scenarioIdx, setScenarioIdx] = useState<number>(0);
  const [model, setModel] = useState<string>('');
  const [isLaunching, setIsLaunching] = useState(false);

  const fetchSimulations = useCallback(() => {
    listSimulations().then(setSimulations).catch(() => {});
  }, []);

  useEffect(() => {
    listPersonas().then(setPersonas).catch(() => {});
    listScenarios().then(setScenariosList).catch(() => {});
    listModels().then((models) => {
      setAvailableModels(models);
      if (models.length > 0 && !model) setModel(models[0]);
    }).catch(() => {});
    fetchSimulations();
  }, []);

  const handleRun = useCallback(async () => {
    if (personas.length === 0 || scenariosList.length === 0) return;

    const condition = conditions[conditionIdx];
    const config = {
      persona: personas[personaIdx],
      style: condition.style,
      mode: condition.mode,
      scenario: scenariosList[scenarioIdx],
      model,
    };

    setIsLaunching(true);

    try {
      await runSimulation(
        config,
        (_role, _turn) => {},
        (_token) => {},
        (_role, _turn) => {},
        (simulationId) => {
          setIsLaunching(false);
          fetchSimulations();
          navigate(`/simulations/${simulationId}`);
        },
      );
    } catch {
      setIsLaunching(false);
    }
  }, [personas, scenariosList, personaIdx, conditionIdx, scenarioIdx, model, navigate, fetchSimulations]);

  const handleDelete = useCallback(async (id: string) => {
    await deleteSimulation(id);
    fetchSimulations();
  }, [fetchSimulations]);

  const dataLoaded = personas.length > 0 && scenariosList.length > 0;

  return (
    <>
      <Header title="Simulations" />
      <div className="flex flex-1 overflow-hidden">
        {/* Config panel */}
        <div className="flex w-80 shrink-0 flex-col border-r border-border bg-muted/20 p-4 gap-5 overflow-y-auto">
          <Card size="sm">
            <CardHeader>
              <CardTitle>New Simulation</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-muted-foreground">Persona</label>
                <Select value={String(personaIdx)} onValueChange={(v) => setPersonaIdx(Number(v))}>
                  <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {personas.map((p, i) => (
                      <SelectItem key={i} value={String(i)}>{p.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-muted-foreground">Condition</label>
                <Select value={String(conditionIdx)} onValueChange={(v) => setConditionIdx(Number(v))}>
                  <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {conditions.map((c, i) => (
                      <SelectItem key={i} value={String(i)}>{c.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-muted-foreground">Scenario</label>
                <Select value={String(scenarioIdx)} onValueChange={(v) => setScenarioIdx(Number(v))}>
                  <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {scenariosList.map((s, i) => (
                      <SelectItem key={i} value={String(i)}>{s.test_name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-muted-foreground">Model</label>
                <Select value={model} onValueChange={setModel}>
                  <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {availableModels.map((m) => (
                      <SelectItem key={m} value={m}>{m}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              <Button onClick={handleRun} disabled={isLaunching || !dataLoaded} className="w-full gap-2">
                {isLaunching ? (
                  <><Loader2 className="h-4 w-4 animate-spin" /> Running...</>
                ) : (
                  <><Play className="h-4 w-4" /> Run Simulation</>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Simulation list */}
        <ScrollArea className="flex-1">
          <div className="p-6 max-w-4xl mx-auto">
            <h2 className="text-lg font-semibold mb-4">Past Simulations</h2>

            {simulations.length === 0 ? (
              <p className="text-muted-foreground text-sm">No simulations yet. Run one using the panel on the left.</p>
            ) : (
              <div className="flex flex-col gap-3">
                {simulations.map((sim) => (
                  <Card
                    key={sim.id}
                    size="sm"
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
                          <span>{sim.style} + {sim.mode}</span>
                          <span>·</span>
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
                        <Badge className={statusColor[sim.state] || ''}>{sim.state}</Badge>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0 text-muted-foreground hover:text-red-500"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(sim.id);
                          }}
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
      </div>
    </>
  );
}

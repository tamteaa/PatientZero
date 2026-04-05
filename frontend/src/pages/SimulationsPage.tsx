import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
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
import { Play, Loader2, Trash2 } from 'lucide-react';
import {
  startSimulation,
  listModels,
  listPersonas,
  listDoctors,
  listScenarios,
  listStyles,
  listSimulations,
  deleteSimulation,
} from '@/api/sessions';
import type {
  AgentProfile,
  Scenario,
  SimulationSummary,
} from '@/types/simulation';

const statusColor: Record<string, string> = {
  running: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  error: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
};

export function SimulationsPage() {
  const navigate = useNavigate();

  const [personas, setPersonas] = useState<AgentProfile[]>([]);
  const [doctors, setDoctors] = useState<AgentProfile[]>([]);
  const [scenariosList, setScenariosList] = useState<Scenario[]>([]);
  const [styles, setStyles] = useState<string[]>([]);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [simulations, setSimulations] = useState<SimulationSummary[]>([]);

  const [patientName, setPatientName] = useState<string>('');
  const [doctorName, setDoctorName] = useState<string>('');
  const [scenarioName, setScenarioName] = useState<string>('');
  const [style, setStyle] = useState<string>('');
  const [model, setModel] = useState<string>('');
  const [maxTurns, setMaxTurns] = useState<string>('');
  const [isLaunching, setIsLaunching] = useState(false);

  const fetchSimulations = useCallback(() => {
    listSimulations().then(setSimulations).catch(() => {});
  }, []);

  useEffect(() => {
    listPersonas().then((p) => { setPersonas(p); if (p.length > 0 && !patientName) setPatientName(p[0].name); }).catch(() => {});
    listDoctors().then((d) => { setDoctors(d); if (d.length > 0 && !doctorName) setDoctorName(d[0].name); }).catch(() => {});
    listScenarios().then((s) => { setScenariosList(s); if (s.length > 0 && !scenarioName) setScenarioName(s[0].test_name); }).catch(() => {});
    listStyles().then((s) => { setStyles(s); if (s.length > 0 && !style) setStyle(s[0]); }).catch(() => {});
    listModels().then((m) => { setAvailableModels(m); if (m.length > 0 && !model) setModel(m[0]); }).catch(() => {});
    fetchSimulations();
  }, []);

  const handleRun = useCallback(async () => {
    if (!patientName || !doctorName || !scenarioName || !style || !model) return;

    const parsedMaxTurns = maxTurns ? parseInt(maxTurns, 10) : undefined;
    const config = {
      patient_name: patientName,
      doctor_name: doctorName,
      scenario_name: scenarioName,
      style,
      model,
      ...(parsedMaxTurns && !isNaN(parsedMaxTurns) ? { max_turns: parsedMaxTurns } : {}),
    };

    setIsLaunching(true);
    try {
      const simId = await startSimulation(config);
      navigate(`/simulations/${simId}`);
    } catch {
      setIsLaunching(false);
    }
  }, [patientName, doctorName, scenarioName, style, model, maxTurns, navigate]);

  const handleDelete = useCallback(async (id: string) => {
    try {
      await deleteSimulation(id);
      fetchSimulations();
    } catch {
      alert('Failed to delete simulation. Please try again.');
    }
  }, [fetchSimulations]);

  const dataLoaded = personas.length > 0 && doctors.length > 0 && scenariosList.length > 0 && styles.length > 0;

  return (
    <ScrollArea className="flex-1">
      <div className="p-6 max-w-5xl mx-auto space-y-6">
        {/* New simulation card */}
        <Card>
          <CardContent className="pt-5 pb-4">
            <h3 className="text-sm font-semibold mb-3">New Simulation</h3>
            <div className="flex items-end gap-3 flex-wrap">
              <div className="flex flex-col gap-1">
                <label className="text-xs text-muted-foreground">Patient</label>
                <Select value={patientName} onValueChange={setPatientName}>
                  <SelectTrigger className="w-44 h-9 text-xs"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {personas.map((p) => (
                      <SelectItem key={p.name} value={p.name}>{p.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-muted-foreground">Doctor</label>
                <Select value={doctorName} onValueChange={setDoctorName}>
                  <SelectTrigger className="w-44 h-9 text-xs"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {doctors.map((d) => (
                      <SelectItem key={d.name} value={d.name}>{d.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-muted-foreground">Scenario</label>
                <Select value={scenarioName} onValueChange={setScenarioName}>
                  <SelectTrigger className="w-52 h-9 text-xs"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {scenariosList.map((s) => (
                      <SelectItem key={s.test_name} value={s.test_name}>{s.test_name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-muted-foreground">Style</label>
                <Select value={style} onValueChange={setStyle}>
                  <SelectTrigger className="w-32 h-9 text-xs"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {styles.map((s) => (
                      <SelectItem key={s} value={s}>{s}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-muted-foreground">Model</label>
                <Select value={model} onValueChange={(v) => { if (v) setModel(v); }}>
                  <SelectTrigger className="w-40 h-9 text-xs"><SelectValue /></SelectTrigger>
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

              <Button onClick={handleRun} disabled={isLaunching || !dataLoaded} size="sm" className="gap-1.5 h-9">
                {isLaunching ? (
                  <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Running...</>
                ) : (
                  <><Play className="h-3.5 w-3.5" /> Run</>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Simulation list */}
        <div>
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
                        <span>{sim.style}</span>
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
      </div>
    </ScrollArea>
  );
}

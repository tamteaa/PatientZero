import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Header } from '@/components/common/Header';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { getSimulation, runSimulation, listModels, listPersonas, listScenarios } from '@/api/sessions';
import type {
  Persona,
  Scenario,
  SimulationDetail,
  SimulationMessage,
  SimulationRole,
  SimulationState,
} from '@/types/simulation';

const INITIAL_STATE: SimulationState = {
  status: 'idle',
  simulationId: null,
  config: null,
  messages: [],
  streamingRole: null,
  streamingContent: '',
  currentTurn: 0,
  error: null,
};

function MessageBubble({ message, isStreaming }: { message: SimulationMessage; isStreaming?: boolean }) {
  const isExplainer = message.role === 'explainer';
  return (
    <div className={`flex flex-col gap-1 ${isExplainer ? 'items-start' : 'items-end'}`}>
      <span className={`text-xs font-medium ${isExplainer ? 'text-blue-600 dark:text-blue-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
        {isExplainer ? 'Explainer' : 'Patient'}
      </span>
      <div
        className={`max-w-[85%] rounded-lg px-4 py-3 text-sm whitespace-pre-wrap ${
          isExplainer
            ? 'bg-blue-50 text-blue-950 dark:bg-blue-950/30 dark:text-blue-100'
            : 'bg-emerald-50 text-emerald-950 dark:bg-emerald-950/30 dark:text-emerald-100'
        }`}
      >
        {message.content}
        {isStreaming && <span className="inline-block w-1.5 h-4 ml-0.5 bg-current animate-pulse" />}
      </div>
    </div>
  );
}

export function SimulationDetailPage() {
  const { simId } = useParams<{ simId: string }>();
  const navigate = useNavigate();
  const scrollRef = useRef<HTMLDivElement>(null);

  const [sim, setSim] = useState<SimulationState>(INITIAL_STATE);
  const [detail, setDetail] = useState<SimulationDetail | null>(null);
  const [loading, setLoading] = useState(true);

  // Load existing simulation from DB
  useEffect(() => {
    if (!simId || simId === 'new') {
      setLoading(false);
      return;
    }

    getSimulation(simId)
      .then((data) => {
        setDetail(data);
        setSim({
          status: data.state as SimulationState['status'],
          simulationId: data.id,
          config: null,
          messages: data.turns.map((t) => ({ role: t.role, content: t.content })),
          streamingRole: null,
          streamingContent: '',
          currentTurn: data.turns.length,
          error: null,
        });
      })
      .catch(() => {
        setSim({ ...INITIAL_STATE, status: 'error', error: 'Simulation not found' });
      })
      .finally(() => setLoading(false));
  }, [simId]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [sim.messages, sim.streamingContent]);

  if (loading) {
    return (
      <>
        <Header title="Simulation" />
        <div className="flex flex-1 items-center justify-center text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
        </div>
      </>
    );
  }

  const statusColor: Record<string, string> = {
    idle: 'bg-gray-100 text-gray-700',
    running: 'bg-blue-100 text-blue-700',
    paused: 'bg-yellow-100 text-yellow-700',
    completed: 'bg-green-100 text-green-700',
    error: 'bg-red-100 text-red-700',
  };

  return (
    <>
      <Header title={detail ? `${detail.persona_name} — ${detail.scenario_name}` : 'Simulation'} />
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar info */}
        <div className="flex w-72 shrink-0 flex-col border-r border-border bg-muted/20 p-4 gap-4 overflow-y-auto">
          <Button variant="ghost" size="sm" className="w-fit gap-1.5" onClick={() => navigate('/simulations')}>
            <ArrowLeft className="h-4 w-4" /> Back to list
          </Button>

          {detail && (
            <>
              <div className="space-y-2 text-xs">
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">Status:</span>
                  <Badge className={statusColor[detail.state] || ''}>{detail.state}</Badge>
                </div>
                <div><span className="text-muted-foreground">Persona:</span> {detail.persona_name}</div>
                <div><span className="text-muted-foreground">Scenario:</span> {detail.scenario_name}</div>
                <div><span className="text-muted-foreground">Style:</span> {detail.style}</div>
                <div><span className="text-muted-foreground">Mode:</span> {detail.mode}</div>
                <div><span className="text-muted-foreground">Model:</span> {detail.model}</div>
                <div><span className="text-muted-foreground">Turns:</span> {detail.turns.length}</div>
                {detail.duration_ms != null && (
                  <div><span className="text-muted-foreground">Duration:</span> {(detail.duration_ms / 1000).toFixed(1)}s</div>
                )}
                <div><span className="text-muted-foreground">Created:</span> {new Date(detail.created_at).toLocaleString()}</div>
              </div>
            </>
          )}
        </div>

        {/* Transcript */}
        <ScrollArea className="flex-1">
          <div className="flex flex-col gap-4 p-6 max-w-3xl mx-auto">
            {/* Persona info card */}
            {detail && (() => {
              try {
                const config = JSON.parse(detail.config_json);
                const p = config.persona;
                if (!p) return null;
                return (
                  <Card size="sm" className="bg-muted/30">
                    <CardContent className="py-4">
                      <div className="flex items-baseline gap-2 mb-2">
                        <span className="font-semibold text-sm">{p.name}</span>
                        <span className="text-xs text-muted-foreground">{p.age} · {p.education}</span>
                      </div>
                      <div className="grid grid-cols-4 gap-2 text-xs mb-2">
                        <div><span className="text-muted-foreground">Literacy:</span> {p.literacy_level}</div>
                        <div><span className="text-muted-foreground">Anxiety:</span> {p.anxiety}</div>
                        <div><span className="text-muted-foreground">Knowledge:</span> {p.prior_knowledge}</div>
                        <div><span className="text-muted-foreground">Style:</span> {p.communication_style}</div>
                      </div>
                      <p className="text-xs text-muted-foreground">{p.backstory}</p>
                    </CardContent>
                  </Card>
                );
              } catch { return null; }
            })()}

            {sim.messages.length === 0 && sim.status !== 'running' && (
              <div className="flex flex-1 items-center justify-center py-20 text-muted-foreground">
                {sim.error ? (
                  <p className="text-red-500">{sim.error}</p>
                ) : (
                  <p>No messages.</p>
                )}
              </div>
            )}

            {sim.messages.map((msg, i) => (
              <MessageBubble key={i} message={msg} />
            ))}

            {sim.streamingRole && (
              <MessageBubble
                message={{ role: sim.streamingRole, content: sim.streamingContent }}
                isStreaming
              />
            )}

            <div ref={scrollRef} />
          </div>
        </ScrollArea>
      </div>
    </>
  );
}

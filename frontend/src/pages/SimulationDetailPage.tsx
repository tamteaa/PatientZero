import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Header } from '@/components/common/Header';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { getSimulation, getSimulationEvaluation, listScenarios } from '@/api/sessions';
import type {
  Evaluation,
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

function QuizBubble({ index, question, content }: { index: number; question?: string; content: string }) {
  return (
    <div className="flex flex-col gap-2">
      {question && (
        <div className="flex flex-col gap-1 items-start">
          <span className="text-xs font-medium text-amber-700 dark:text-amber-300">
            Question {index + 1}
          </span>
          <div className="max-w-[85%] rounded-lg px-4 py-3 text-sm bg-amber-100/60 text-amber-900 dark:bg-amber-900/20 dark:text-amber-200 border border-amber-200 dark:border-amber-800">
            {question}
          </div>
        </div>
      )}
      <div className="flex flex-col gap-1 items-end">
        <span className="text-xs font-medium text-amber-600 dark:text-amber-400">
          Patient Answer {index + 1}
        </span>
        <div className="max-w-[85%] rounded-lg px-4 py-3 text-sm whitespace-pre-wrap bg-amber-50 text-amber-950 dark:bg-amber-950/30 dark:text-amber-100 border border-amber-200 dark:border-amber-800">
          {content}
        </div>
      </div>
    </div>
  );
}

function ScoreBar({ label, value }: { label: string; value: number | null }) {
  const pct = value != null ? Math.max(0, Math.min(100, value)) : null;
  const color =
    pct == null ? 'bg-muted'
    : pct >= 70 ? 'bg-green-500'
    : pct >= 50 ? 'bg-amber-500'
    : 'bg-red-500';
  const textColor =
    pct == null ? 'text-muted-foreground'
    : pct >= 70 ? 'text-green-600 dark:text-green-400'
    : pct >= 50 ? 'text-amber-600 dark:text-amber-400'
    : 'text-red-600 dark:text-red-400';
  return (
    <div className="flex items-center gap-2">
      <span className="w-32 shrink-0 text-xs text-muted-foreground text-right">{label}</span>
      <div className="flex-1 h-2.5 bg-muted rounded overflow-hidden">
        {pct != null && <div className={`h-full rounded ${color}`} style={{ width: `${pct}%` }} />}
      </div>
      <span className={`w-8 text-xs tabular-nums text-right ${textColor}`}>
        {pct != null ? pct : '—'}
      </span>
    </div>
  );
}

function EvaluationPanel({ evaluation }: { evaluation: Evaluation }) {
  return (
    <Card size="sm" className="bg-muted/30">
      <CardContent className="py-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold">Judge Evaluation</span>
          <span className="text-xs text-muted-foreground font-mono">{evaluation.model}</span>
        </div>
        <div className="space-y-1.5">
          <ScoreBar label="Comprehension" value={evaluation.comprehension_score} />
          <ScoreBar label="Factual Recall" value={evaluation.factual_recall} />
          <ScoreBar label="Applied Reasoning" value={evaluation.applied_reasoning} />
          <ScoreBar label="Explanation Quality" value={evaluation.explanation_quality} />
          <ScoreBar label="Interaction Quality" value={evaluation.interaction_quality} />
        </div>
        {evaluation.confidence_comprehension_gap && (
          <p className="text-xs text-muted-foreground mt-2">
            <span className="font-medium">Confidence gap:</span> {evaluation.confidence_comprehension_gap}
          </p>
        )}
        {evaluation.justification && (
          <p className="text-xs text-muted-foreground mt-1">
            <span className="font-medium">Justification:</span> {evaluation.justification}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

export function SimulationDetailPage() {
  const { simId } = useParams<{ simId: string }>();
  const navigate = useNavigate();
  const scrollRef = useRef<HTMLDivElement>(null);

  const [sim, setSim] = useState<SimulationState>(INITIAL_STATE);
  const [detail, setDetail] = useState<SimulationDetail | null>(null);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDetail = useCallback(() => {
    if (!simId || simId === 'new') return;
    return getSimulation(simId)
      .then((data) => {
        setDetail(data);
        setSim({
          status: data.state as SimulationState['status'],
          simulationId: data.id,
          config: null,
          messages: data.turns.map((t) => ({
            role: t.role as SimulationRole,
            content: t.content,
            agent_type: t.agent_type,
          })),
          streamingRole: null,
          streamingContent: '',
          currentTurn: data.turns.length,
          error: null,
        });
        return data;
      })
      .catch(() => {
        setSim({ ...INITIAL_STATE, status: 'error', error: 'Simulation not found' });
        return null;
      });
  }, [simId]);

  useEffect(() => {
    if (!simId || simId === 'new') {
      setLoading(false);
      return;
    }
    Promise.all([
      fetchDetail(),
      getSimulationEvaluation(simId).catch(() => null),
      listScenarios().catch(() => []),
    ]).then(([, eval_, scens]) => {
      setEvaluation(eval_);
      setScenarios(scens);
    }).finally(() => setLoading(false));
  }, [simId, fetchDetail]);

  useEffect(() => {
    if (!detail || detail.state !== 'running') return;
    const interval = setInterval(() => {
      fetchDetail()?.then((data) => {
        if (data && data.state !== 'running') clearInterval(interval);
      });
    }, 2000);
    return () => clearInterval(interval);
  }, [detail?.state, fetchDetail]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [sim.messages, sim.streamingContent]);

  if (loading) {
    return (
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header title="Simulation" />
        <div className="flex flex-1 items-center justify-center text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
        </div>
      </div>
    );
  }

  const statusColor: Record<string, string> = {
    idle: 'bg-gray-100 text-gray-700',
    running: 'bg-blue-100 text-blue-700',
    paused: 'bg-yellow-100 text-yellow-700',
    completed: 'bg-green-100 text-green-700',
    error: 'bg-red-100 text-red-700',
  };

  const conversationMessages = sim.messages.filter((m) => m.role !== 'quiz');
  const quizMessages = sim.messages.filter((m) => m.role === 'quiz');

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="border-b border-border bg-muted/20 px-4 py-3">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" className="gap-1.5 shrink-0" onClick={() => navigate('/simulations')}>
            <ArrowLeft className="h-4 w-4" /> Back
          </Button>

          {detail && (
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
              <Badge className={statusColor[detail.state] || ''}>{detail.state}</Badge>
              <span><span className="text-muted-foreground">Persona:</span> {detail.persona_name}</span>
              <span><span className="text-muted-foreground">Scenario:</span> {detail.scenario_name}</span>
              <span><span className="text-muted-foreground">Style:</span> {detail.style}</span>
              <span><span className="text-muted-foreground">Mode:</span> {detail.mode}</span>
              <span><span className="text-muted-foreground">Model:</span> {detail.model}</span>
              <span><span className="text-muted-foreground">Turns:</span> {conversationMessages.length}</span>
              {quizMessages.length > 0 && (
                <span><span className="text-muted-foreground">Quiz:</span> {quizMessages.length}q</span>
              )}
              {detail.duration_ms != null && (
                <span><span className="text-muted-foreground">Duration:</span> {(detail.duration_ms / 1000).toFixed(1)}s</span>
              )}
              {evaluation && (
                <Badge className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                  score: {evaluation.comprehension_score ?? '—'}
                </Badge>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        <ScrollArea className="flex-1">
          <div className="flex flex-col gap-4 p-6 max-w-3xl mx-auto">
            {/* Persona info */}
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

            {/* Evaluation scores */}
            {evaluation && <EvaluationPanel evaluation={evaluation} />}

            {conversationMessages.length === 0 && sim.status !== 'running' && (
              <div className="flex flex-1 items-center justify-center py-20 text-muted-foreground">
                {sim.error ? (
                  <p className="text-red-500">{sim.error}</p>
                ) : (
                  <p>No messages.</p>
                )}
              </div>
            )}

            {/* Conversation */}
            {conversationMessages.map((msg, i) => (
              <MessageBubble key={i} message={msg} />
            ))}

            {sim.streamingRole && sim.streamingRole !== 'quiz' && (
              <MessageBubble
                message={{ role: sim.streamingRole, content: sim.streamingContent }}
                isStreaming
              />
            )}

            {/* Quiz section */}
            {quizMessages.length > 0 && (
              <>
                <div className="flex items-center gap-3 my-2">
                  <Separator className="flex-1" />
                  <span className="text-xs font-semibold text-amber-600 dark:text-amber-400 shrink-0">
                    Comprehension Quiz
                  </span>
                  <Separator className="flex-1" />
                </div>
                {(() => {
                  const scenarioQuiz = detail
                    ? scenarios.find((s) => s.test_name === detail.scenario_name)?.quiz ?? []
                    : [];
                  return quizMessages.map((msg, i) => (
                    <QuizBubble
                      key={i}
                      index={i}
                      question={scenarioQuiz[i]?.question}
                      content={msg.content}
                    />
                  ));
                })()}
              </>
            )}

            <div ref={scrollRef} />
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
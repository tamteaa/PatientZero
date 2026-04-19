import { useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAtom, useAtomValue } from 'jotai';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Loader2, Pause, Play, Square } from 'lucide-react';
import {
  getSimulation,
  pauseSimulation,
  resumeSimulation,
  stopSimulation,
  subscribeToSimulation,
} from '@/api/sessions';
import { useError } from '@/contexts/ErrorContext';
import {
  simulationDetailAtom,
  simulationStatusAtom,
  simulationTextStatusAtom,
  simulationMessagesAtom,
  streamingRoleAtom,
  streamingContentAtom,
  isSimulationActiveAtom,
} from '@/atoms/simulation';
import type { SimulationMessage } from '@/types/simulation';

const ROLE_STYLES: Array<[string, string, string]> = [
  ['blue', 'text-blue-600 dark:text-blue-400', 'bg-blue-50 text-blue-950 dark:bg-blue-950/30 dark:text-blue-100'],
  ['emerald', 'text-emerald-600 dark:text-emerald-400', 'bg-emerald-50 text-emerald-950 dark:bg-emerald-950/30 dark:text-emerald-100'],
  ['amber', 'text-amber-700 dark:text-amber-300', 'bg-amber-50 text-amber-950 dark:bg-amber-950/30 dark:text-amber-100'],
  ['purple', 'text-purple-600 dark:text-purple-400', 'bg-purple-50 text-purple-950 dark:bg-purple-950/30 dark:text-purple-100'],
];

function styleForRole(role: string): { label: string; text: string; bubble: string; alignStart: boolean } {
  // Stable hash → index
  let h = 0;
  for (let i = 0; i < role.length; i++) h = (h * 31 + role.charCodeAt(i)) | 0;
  const idx = Math.abs(h) % ROLE_STYLES.length;
  const [, text, bubble] = ROLE_STYLES[idx];
  return {
    label: role.charAt(0).toUpperCase() + role.slice(1),
    text,
    bubble,
    alignStart: idx % 2 === 0,
  };
}

function MessageBubble({ message, isStreaming }: { message: SimulationMessage; isStreaming?: boolean }) {
  const s = styleForRole(message.role);
  return (
    <div className={`flex flex-col gap-1 ${s.alignStart ? 'items-start' : 'items-end'}`}>
      <span className={`text-xs font-medium ${s.text}`}>{s.label}</span>
      <div className={`max-w-[85%] rounded-lg px-4 py-3 text-sm whitespace-pre-wrap ${s.bubble}`}>
        {message.content}
        {isStreaming && <span className="inline-block w-1.5 h-4 ml-0.5 bg-current animate-pulse" />}
      </div>
    </div>
  );
}

const statusColor: Record<string, string> = {
  idle: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-200',
  running: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-200',
  paused: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-200',
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-200',
  error: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-200',
};

export function SimulationDetailPage() {
  const { simId } = useParams<{ simId: string }>();
  const navigate = useNavigate();
  const { handleError } = useError();
  const scrollRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const [detail, setDetail] = useAtom(simulationDetailAtom);
  const [status, setStatus] = useAtom(simulationStatusAtom);
  const [textStatus, setTextStatus] = useAtom(simulationTextStatusAtom);
  const [messages, setMessages] = useAtom(simulationMessagesAtom);
  const [streamingRole, setStreamingRole] = useAtom(streamingRoleAtom);
  const [streamingContent, setStreamingContent] = useAtom(streamingContentAtom);
  const isActive = useAtomValue(isSimulationActiveAtom);

  const fetchDetail = useCallback(() => {
    if (!simId) return;
    return getSimulation(simId)
      .then((data) => {
        setDetail(data);
        setStatus(data.state);
        setTextStatus(data.text_status || '');
        setMessages(data.turns.map((t) => ({ role: t.role, content: t.content })));
        return data;
      })
      .catch(() => {
        setStatus('error');
        setTextStatus('Simulation not found');
        return null;
      });
  }, [simId, setDetail, setStatus, setTextStatus, setMessages]);

  useEffect(() => {
    if (!simId) return;

    // Reset state
    setDetail(null);
    setStatus('idle');
    setTextStatus('');
    setMessages([]);
    setStreamingRole(null);
    setStreamingContent('');

    fetchDetail()?.then((data) => {
      if (!data) return;

      if (data.state === 'running' || data.state === 'paused' || data.state === 'idle') {
        const abort = new AbortController();
        abortRef.current = abort;

        const knownTurns = new Set(data.turns.map((t) => t.turn_number));
        const maxTurns = data.max_turns ?? 8;

        subscribeToSimulation(simId, {
          onTurnStart: (role, turn) => {
            if (knownTurns.has(turn)) return;
            setStreamingRole(role);
            setStreamingContent('');
            setStatus('running');
            setTextStatus(`Turn ${turn + 1}/${maxTurns} — ${role.charAt(0).toUpperCase() + role.slice(1)} is responding…`);
          },
          onToken: (token) => {
            setStreamingContent((prev) => prev + token);
          },
          onTurnEnd: (role, turn) => {
            if (knownTurns.has(turn)) return;
            knownTurns.add(turn);
            setStreamingContent((prev) => {
              const content = prev;
              setMessages((msgs) => [...msgs, { role, content }]);
              return '';
            });
            setStreamingRole(null);
            setTextStatus(`Turn ${turn + 1}/${maxTurns} complete`);
          },
          onDone: () => {
            setStreamingRole(null);
            setStreamingContent('');
            fetchDetail();
          },
        }, abort.signal);
      }
    });

    return () => {
      abortRef.current?.abort();
    };
  }, [simId]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const isRunning = status === 'running';
  const isPaused = status === 'paused';

  const handlePause = useCallback(async () => {
    if (!simId) return;
    try {
      await pauseSimulation(simId);
      setStatus('paused');
      setTextStatus(`Paused at turn ${messages.length + 1}`);
    } catch (err) {
      handleError(err, 'Failed to pause simulation');
    }
  }, [simId, messages.length, setStatus, setTextStatus, handleError]);

  const handleResume = useCallback(async () => {
    if (!simId) return;
    try {
      await resumeSimulation(simId);
      setStatus('running');
      setTextStatus('Resuming...');
    } catch (err) {
      handleError(err, 'Failed to resume simulation');
    }
  }, [simId, setStatus, setTextStatus, handleError]);

  const handleStop = useCallback(async () => {
    if (!simId) return;
    try {
      await stopSimulation(simId);
      setStatus('completed');
      setTextStatus(`Stopped at turn ${messages.length}`);
      fetchDetail();
    } catch (err) {
      handleError(err, 'Failed to stop simulation');
    }
  }, [simId, messages.length, setStatus, setTextStatus, fetchDetail, handleError]);

  if (!detail && status !== 'error') {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Top bar */}
      <div className="border-b border-border bg-muted/20 px-4 py-2">
        <Button variant="ghost" size="sm" className="gap-1.5" onClick={() => navigate('/experiments')}>
          <ArrowLeft className="h-3.5 w-3.5" /> Back
        </Button>
      </div>

      {/* Control bar */}
      <div className="border-b border-border bg-muted/20 px-4 py-3">
        <div className="flex items-center justify-between">
          {detail && (
            <div className="flex items-center gap-3 text-xs text-muted-foreground flex-wrap">
              <Badge className={statusColor[status] || ''}>{status}</Badge>
              {textStatus && (
                <span className="font-medium text-foreground">{textStatus}</span>
              )}
              <span className="font-mono">{detail.config.model}</span>
              {Object.entries(detail.config.profiles ?? {}).map(([agent, traits]) => (
                <span key={agent} className="flex items-center gap-1">
                  <span>·</span>
                  <span>
                    <span className="font-medium text-foreground">{agent}</span>
                    {Object.keys(traits).length > 0 && (
                      <span>
                        {' ('}
                        {Object.entries(traits).slice(0, 3).map(([k, v]) => `${k}=${v}`).join(', ')}
                        {')'}
                      </span>
                    )}
                  </span>
                </span>
              ))}
              {!isActive && (
                <>
                  <span>·</span>
                  <span>{messages.length} turns</span>
                </>
              )}
              {detail.duration_ms != null && (
                <>
                  <span>·</span>
                  <span>{(detail.duration_ms / 1000).toFixed(1)}s</span>
                </>
              )}
            </div>
          )}

          {isActive && (
            <div className="flex items-center gap-1.5">
              {isRunning && (
                <Button variant="outline" size="sm" className="h-8 gap-1.5 text-xs" onClick={handlePause}>
                  <Pause className="h-3.5 w-3.5" /> Pause
                </Button>
              )}
              {isPaused && (
                <Button variant="outline" size="sm" className="h-8 gap-1.5 text-xs" onClick={handleResume}>
                  <Play className="h-3.5 w-3.5" /> Resume
                </Button>
              )}
              <Button variant="outline" size="sm" className="h-8 gap-1.5 text-xs text-red-600 hover:text-red-700" onClick={handleStop}>
                <Square className="h-3.5 w-3.5" /> Stop
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Transcript */}
      <div className="flex-1 overflow-y-auto">
        <div className="flex flex-col gap-4 p-6 max-w-3xl mx-auto">
          {messages.length === 0 && !streamingRole && !isRunning && (
            <div className="flex flex-1 items-center justify-center py-20 text-muted-foreground">
              {status === 'error' ? (
                <p className="text-red-500">{textStatus || 'Error'}</p>
              ) : (
                <p>No messages.</p>
              )}
            </div>
          )}

          {messages.map((msg, i) => (
            <MessageBubble key={i} message={msg} />
          ))}

          {streamingRole && (
            <MessageBubble
              message={{ role: streamingRole, content: streamingContent }}
              isStreaming
            />
          )}

          <div ref={scrollRef} />
        </div>
      </div>

    </div>
  );
}

import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react';
import { useAtomValue } from 'jotai';
import { createSession, listSessions, getSession, sendMessage, updateSessionModel, deleteSession } from '@/api/sessions';
import { useError } from '@/contexts/ErrorContext';
import { globalModelAtom } from '@/atoms/model';
import type { Session, Turn } from '@/types/chat';

interface ChatContextValue {
  sessions: Session[];
  activeSessionId: string | null;
  turns: Turn[];
  streamingContent: string | null;
  isStreaming: boolean;
  selectSession: (id: string) => void;
  newChat: () => void;
  send: (message: string) => void;
  removeSession: (id: string) => void;
}

const ChatContext = createContext<ChatContextValue | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
  const { handleError } = useError();
  const activeModel = useAtomValue(globalModelAtom);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [streamingContent, setStreamingContent] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);

  const refreshSessions = useCallback(async () => {
    try {
      const data = await listSessions();
      setSessions(data);
    } catch (e) {
      handleError(e, 'Failed to load sessions');
    }
  }, [handleError]);

  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  const selectSession = useCallback(async (id: string) => {
    try {
      setActiveSessionId(id);
      const session = await getSession(id);
      setTurns(session.turns);
    } catch (e) {
      handleError(e, 'Failed to load session');
    }
  }, [handleError]);

  const newChat = useCallback(async () => {
    try {
      const session = await createSession(activeModel);
      setActiveSessionId(session.id);
      setTurns([]);
      await refreshSessions();
    } catch (e) {
      handleError(e, 'Failed to create session');
    }
  }, [activeModel, refreshSessions, handleError]);

  useEffect(() => {
    if (!activeSessionId) return;
    updateSessionModel(activeSessionId, activeModel)
      .then(refreshSessions)
      .catch(() => {});
  }, [activeModel, activeSessionId, refreshSessions]);

  const removeSession = useCallback(async (id: string) => {
    try {
      await deleteSession(id);
      if (activeSessionId === id) {
        setActiveSessionId(null);
        setTurns([]);
      }
      await refreshSessions();
    } catch (e) {
      handleError(e, 'Failed to delete session');
    }
  }, [activeSessionId, refreshSessions, handleError]);

  const send = useCallback(async (message: string) => {
    if (!activeSessionId || isStreaming) return;

    const userTurn: Turn = {
      id: Date.now(),
      role: 'user',
      content: message,
      turn_number: turns.length,
      created_at: new Date().toISOString(),
    };
    setTurns((prev) => [...prev, userTurn]);
    setIsStreaming(true);
    setStreamingContent('');

    let accumulated = '';
    try {
      await sendMessage(
        activeSessionId,
        message,
        (token) => {
          accumulated += token;
          setStreamingContent(accumulated);
        },
        () => {
          const assistantTurn: Turn = {
            id: Date.now() + 1,
            role: 'assistant',
            content: accumulated,
            turn_number: turns.length + 1,
            created_at: new Date().toISOString(),
          };
          setTurns((prev) => [...prev, assistantTurn]);
          setStreamingContent(null);
          setIsStreaming(false);
          refreshSessions();
        },
        (error) => {
          setStreamingContent(null);
          setIsStreaming(false);
          handleError(new Error(error), 'Chat error');
        },
      );
    } catch (e) {
      setStreamingContent(null);
      setIsStreaming(false);
      handleError(e, 'Failed to send message');
    }
  }, [activeSessionId, isStreaming, turns.length, refreshSessions, handleError]);

  return (
    <ChatContext.Provider
      value={{
        sessions, activeSessionId, turns, streamingContent,
        isStreaming, selectSession, newChat, send, removeSession,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error('useChat must be used within ChatProvider');
  return ctx;
}

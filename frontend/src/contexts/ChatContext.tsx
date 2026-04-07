import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react';
import { createSession, listSessions, getSession, sendMessage, listModels, updateSessionModel, deleteSession } from '@/api/sessions';
import { useError } from '@/contexts/ErrorContext';
import type { Session, Turn } from '@/types/chat';

interface ChatContextValue {
  sessions: Session[];
  activeSessionId: string | null;
  activeModel: string;
  turns: Turn[];
  streamingContent: string | null;
  isStreaming: boolean;
  availableModels: string[];
  selectSession: (id: string) => void;
  newChat: () => void;
  send: (message: string) => void;
  setModel: (model: string) => void;
  removeSession: (id: string) => void;
}

const ChatContext = createContext<ChatContextValue | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
  const { handleError } = useError();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [activeModel, setActiveModel] = useState('mock:default');
  const [turns, setTurns] = useState<Turn[]>([]);
  const [streamingContent, setStreamingContent] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [availableModels, setAvailableModels] = useState<string[]>([]);

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
    listModels()
      .then(setAvailableModels)
      .catch((e) => handleError(e, 'Failed to load models'));
  }, [refreshSessions, handleError]);

  const selectSession = useCallback(async (id: string) => {
    try {
      setActiveSessionId(id);
      const session = await getSession(id);
      setTurns(session.turns);
      setActiveModel(session.model);
    } catch (e) {
      handleError(e, 'Failed to load session');
    }
  }, [handleError]);

  const newChat = useCallback(async () => {
    try {
      const session = await createSession(activeModel);
      setActiveSessionId(session.id);
      setTurns([]);
      setActiveModel(session.model);
      await refreshSessions();
    } catch (e) {
      handleError(e, 'Failed to create session');
    }
  }, [activeModel, refreshSessions, handleError]);

  const setModel = useCallback(async (model: string) => {
    try {
      setActiveModel(model);
      if (activeSessionId) {
        await updateSessionModel(activeSessionId, model);
        await refreshSessions();
      }
    } catch (e) {
      handleError(e, 'Failed to update model');
    }
  }, [activeSessionId, refreshSessions, handleError]);

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
        sessions, activeSessionId, activeModel, turns, streamingContent,
        isStreaming, availableModels, selectSession, newChat, send, setModel, removeSession,
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

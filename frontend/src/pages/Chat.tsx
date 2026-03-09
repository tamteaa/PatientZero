import { useEffect, useState, useCallback } from 'react';
import { Sidebar } from '@/components/chat/Sidebar';
import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';
import { createSession, listSessions, getSession, sendMessage } from '@/api/sessions';
import type { Session, Turn } from '@/types/chat';

export function Chat() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [streamingContent, setStreamingContent] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);

  const refreshSessions = useCallback(async () => {
    const data = await listSessions();
    setSessions(data);
  }, []);

  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  const handleSelectSession = async (id: string) => {
    setActiveSessionId(id);
    const session = await getSession(id);
    setTurns(session.turns);
  };

  const handleNewChat = async () => {
    const session = await createSession();
    setActiveSessionId(session.id);
    setTurns([]);
    await refreshSessions();
  };

  const handleSend = async (message: string) => {
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
    );
  };

  return (
    <div className="flex h-screen bg-background">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
      />
      <div className="flex flex-1 flex-col">
        {activeSessionId ? (
          <>
            <MessageList turns={turns} streamingContent={streamingContent} />
            <ChatInput onSend={handleSend} disabled={isStreaming} />
          </>
        ) : (
          <div className="flex flex-1 items-center justify-center text-muted-foreground">
            Create a new chat or select one from the sidebar.
          </div>
        )}
      </div>
    </div>
  );
}

import { useChat } from '@/contexts/ChatContext';
import { Header } from '@/components/common/Header';
import { Sidebar } from '@/components/chat/Sidebar';
import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';

export function ChatContainer() {
  const {
    sessions, activeSessionId, turns, streamingContent,
    isStreaming, selectSession, newChat, send, removeSession,
  } = useChat();

  const activeTitle = sessions.find((s) => s.id === activeSessionId)?.title ?? '';

  return (
    <div className="flex flex-1 overflow-hidden">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={selectSession}
        onNewChat={newChat}
        onDeleteSession={removeSession}
      />
      <div className="flex flex-1 flex-col">
        <Header title={activeTitle} />
        {activeSessionId ? (
          <>
            <MessageList turns={turns} streamingContent={streamingContent} />
            <ChatInput onSend={send} disabled={isStreaming} />
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

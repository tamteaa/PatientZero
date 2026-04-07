import { useChat } from '@/contexts/ChatContext';
import { Header } from '@/components/common/Header';
import { Sidebar } from '@/components/chat/Sidebar';
import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';
import { ModelSelector } from '@/components/chat/ModelSelector';

export function ChatContainer() {
  const {
    sessions, activeSessionId, activeModel, turns, streamingContent,
    isStreaming, availableModels, selectSession, newChat, send, setModel, removeSession,
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
        <Header title={activeTitle}>
          {activeSessionId && (
            <ModelSelector
              models={availableModels}
              selected={activeModel}
              onSelect={setModel}
              disabled={isStreaming}
            />
          )}
        </Header>
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

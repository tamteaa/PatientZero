import { useEffect, useRef } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageBubble } from './MessageBubble';
import type { Turn } from '@/types/chat';

interface MessageListProps {
  turns: Turn[];
  streamingContent: string | null;
}

export function MessageList({ turns, streamingContent }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns, streamingContent]);

  return (
    <ScrollArea className="flex-1 p-4">
      <div className="mx-auto flex max-w-3xl flex-col gap-4">
        {turns.map((turn) => (
          <MessageBubble key={turn.id ?? turn.turn_number} role={turn.role} content={turn.content} />
        ))}
        {streamingContent !== null && (
          <MessageBubble role="assistant" content={streamingContent || '...'} />
        )}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}

import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import type { Session } from '@/types/chat';
import { Plus, MessageSquare } from 'lucide-react';

interface SidebarProps {
  sessions: Session[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
}

export function Sidebar({ sessions, activeSessionId, onSelectSession, onNewChat }: SidebarProps) {
  return (
    <div className="flex h-full w-64 flex-col border-r border-border bg-muted/30">
      <div className="p-3">
        <Button onClick={onNewChat} className="w-full justify-start gap-2" variant="outline">
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
      </div>
      <Separator />
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-1 p-2">
          {sessions.map((session) => (
            <button
              key={session.id}
              onClick={() => onSelectSession(session.id)}
              className={`flex items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors hover:bg-accent ${
                activeSessionId === session.id ? 'bg-accent text-accent-foreground' : 'text-muted-foreground'
              }`}
            >
              <MessageSquare className="h-4 w-4 shrink-0" />
              <span className="truncate">{session.title}</span>
            </button>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}

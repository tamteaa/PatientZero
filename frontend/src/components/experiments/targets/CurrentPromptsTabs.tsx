import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ChevronDown, ChevronRight, FileText } from 'lucide-react';
import type { OptimizationTarget } from '@/types/simulation';

interface Props {
  target: OptimizationTarget;
}

function formatRoleLabel(role: string): string {
  return role
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function CurrentPromptsTabs({ target }: Props) {
  const [expanded, setExpanded] = useState(false);
  const roles = Object.keys(target.prompts);

  if (roles.length === 0) {
    return null;
  }

  return (
    <div className="rounded-md border border-border bg-card overflow-hidden">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex items-center gap-2 w-full text-left px-4 py-2.5 hover:bg-muted/40 transition-colors"
      >
        {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        <FileText className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium">Current prompts</span>
        <span className="text-[11px] text-muted-foreground">
          {target.kind} · {roles.length} role{roles.length !== 1 ? 's' : ''}
        </span>
      </button>
      {expanded && (
        <div className="px-4 pb-4 pt-1 border-t border-border">
          <Tabs defaultValue={roles[0]} className="pt-3">
            <TabsList>
              {roles.map((role) => (
                <TabsTrigger key={role} value={role}>
                  {formatRoleLabel(role)}
                </TabsTrigger>
              ))}
            </TabsList>
            {roles.map((role) => (
              <TabsContent key={role} value={role} className="pt-3">
                <pre className="text-[11px] whitespace-pre-wrap break-words rounded bg-muted/40 p-3 border border-border/60 font-mono max-h-[min(50vh,28rem)] overflow-y-auto leading-relaxed">
                  {target.prompts[role]}
                </pre>
              </TabsContent>
            ))}
          </Tabs>
        </div>
      )}
    </div>
  );
}

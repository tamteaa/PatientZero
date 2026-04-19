import { useState } from 'react';
import { ChevronDown, ChevronRight, Sparkles, X } from 'lucide-react';
import type { OptimizationResult } from '@/types/simulation';

interface Props {
  result: OptimizationResult;
  onDismiss: () => void;
}

function PromptDiffList({
  previous,
  next,
}: {
  previous: Record<string, string>;
  next: Record<string, string>;
}) {
  const keys = Array.from(new Set([...Object.keys(previous), ...Object.keys(next)]));
  return (
    <div className="space-y-3">
      {keys.map((k) => {
        const prev = previous[k] ?? '';
        const cur = next[k] ?? '';
        const changed = prev !== cur;
        return (
          <div key={k} className="rounded border border-border/60 overflow-hidden">
            <div className="flex items-baseline justify-between px-3 py-1.5 bg-muted/30 border-b border-border/60">
              <span className="text-xs font-medium">{k}</span>
              <span className={`text-[10px] uppercase tracking-wide ${changed ? 'text-emerald-600 dark:text-emerald-400' : 'text-muted-foreground'}`}>
                {changed ? 'updated' : 'unchanged'}
              </span>
            </div>
            {changed && (
              <div className="grid grid-cols-2 divide-x divide-border/60">
                <div className="p-2">
                  <div className="text-[10px] uppercase tracking-wide text-muted-foreground mb-1">Before</div>
                  <pre className="whitespace-pre-wrap break-words font-mono text-[11px] leading-relaxed text-muted-foreground max-h-40 overflow-y-auto">
                    {prev || '(empty)'}
                  </pre>
                </div>
                <div className="p-2">
                  <div className="text-[10px] uppercase tracking-wide text-muted-foreground mb-1">After</div>
                  <pre className="whitespace-pre-wrap break-words font-mono text-[11px] leading-relaxed max-h-40 overflow-y-auto">
                    {cur || '(empty)'}
                  </pre>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export function OptimizationResultCard({ result, onDismiss }: Props) {
  const [showDiff, setShowDiff] = useState(false);

  return (
    <div className="rounded-md border border-border bg-card overflow-hidden">
      <div className="flex items-start gap-3 px-4 py-3 bg-gradient-to-r from-primary/5 to-transparent border-b border-border">
        <Sparkles className="h-4 w-4 text-primary mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2 flex-wrap">
            <h4 className="text-sm font-semibold">Last optimization</h4>
            <span className="text-[11px] text-muted-foreground tabular-nums">
              {new Date(result.new_target.created_at).toLocaleString()}
            </span>
          </div>
        </div>
        <button
          onClick={onDismiss}
          className="text-muted-foreground hover:text-foreground shrink-0"
          aria-label="Dismiss"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="grid grid-cols-3 divide-x divide-border">
        <div className="px-4 py-3">
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Previous</p>
          <p className="text-xs font-mono mt-1 truncate" title={result.previous_target.id}>
            {result.previous_target.id.slice(0, 8)}…
          </p>
          <p className="text-[11px] text-muted-foreground mt-0.5">
            {new Date(result.previous_target.created_at).toLocaleDateString()}
          </p>
        </div>
        <div className="px-4 py-3">
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground">New</p>
          <p className="text-xs font-mono mt-1 truncate" title={result.new_target.id}>
            {result.new_target.id.slice(0, 8)}…
          </p>
          <p className="text-[11px] text-muted-foreground mt-0.5">active</p>
        </div>
        <div className="px-4 py-3">
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Traces used</p>
          <p className="text-xl font-semibold tabular-nums mt-1">{result.traces_considered}</p>
          <p className="text-[11px] text-muted-foreground mt-0.5">evaluated sims</p>
        </div>
      </div>

      {result.rationale && (
        <div className="border-t border-border px-4 py-3">
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground mb-1">Rationale</p>
          <p className="text-xs whitespace-pre-wrap leading-relaxed">{result.rationale}</p>
        </div>
      )}

      <div className="border-t border-border">
        <button
          onClick={() => setShowDiff((v) => !v)}
          className="flex items-center gap-1.5 w-full text-left px-4 py-2 text-xs font-medium hover:bg-muted/40 transition-colors"
        >
          {showDiff ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
          Prompt changes
        </button>
        {showDiff && (
          <div className="px-4 pb-3">
            <PromptDiffList
              previous={result.previous_target.prompts}
              next={result.new_target.prompts}
            />
          </div>
        )}
      </div>
    </div>
  );
}

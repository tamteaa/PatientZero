import { Loader2, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { OptimizationTarget } from '@/types/simulation';
import type { ScoreStats } from '@/api/sessions';

interface Props {
  targets: OptimizationTarget[];
  currentTargetId: string | null;
  loading: boolean;
  activatingTargetId: string | null;
  scoresByTargetId: Record<string, ScoreStats>;
  onActivate: (targetId: string) => void;
}

interface LineageNode {
  target: OptimizationTarget;
  depth: number;
  isLastChild: boolean;
  hasSiblingBelow: boolean[];  // for each ancestor depth, whether there's a sibling line to draw
}

/**
 * Walk the parent→child tree in DFS order, tagging each node with its depth
 * and the path of "has sibling below" flags so we can draw connector lines.
 * Roots are ordered newest-first; children follow creation order.
 */
function buildLineage(targets: OptimizationTarget[]): LineageNode[] {
  const childrenByParent = new Map<string | null, OptimizationTarget[]>();
  for (const t of targets) {
    const key = t.parent_id;
    const list = childrenByParent.get(key) ?? [];
    list.push(t);
    childrenByParent.set(key, list);
  }
  // Order children oldest-first so the chain reads top-to-bottom
  for (const list of childrenByParent.values()) {
    list.sort((a, b) => a.created_at.localeCompare(b.created_at));
  }

  // Roots: targets whose parent is null OR whose parent isn't in the set.
  const targetIds = new Set(targets.map((t) => t.id));
  const roots = targets
    .filter((t) => t.parent_id == null || !targetIds.has(t.parent_id))
    .sort((a, b) => a.created_at.localeCompare(b.created_at));

  const out: LineageNode[] = [];
  const walk = (node: OptimizationTarget, depth: number, ancestorHasMore: boolean[], isLastChild: boolean) => {
    out.push({ target: node, depth, isLastChild, hasSiblingBelow: ancestorHasMore });
    const kids = childrenByParent.get(node.id) ?? [];
    kids.forEach((child, i) => {
      const last = i === kids.length - 1;
      walk(child, depth + 1, [...ancestorHasMore, !isLastChild], last);
    });
  };
  roots.forEach((root, i) => {
    walk(root, 0, [], i === roots.length - 1);
  });
  return out;
}

function LineageConnector({ node }: { node: LineageNode }) {
  if (node.depth === 0) return null;
  return (
    <div className="flex items-stretch shrink-0" aria-hidden>
      {node.hasSiblingBelow.slice(1).map((more, i) => (
        <div key={i} className="w-4 flex justify-center">
          {more && <div className="w-px bg-border" />}
        </div>
      ))}
      <div className="w-4 flex flex-col items-center">
        <div className="w-px bg-border h-3" />
        <div className="text-muted-foreground text-[10px] -mt-1">
          {node.isLastChild ? '└' : '├'}
        </div>
        {!node.isLastChild && <div className="w-px bg-border flex-1" />}
      </div>
    </div>
  );
}

export function OptimizationTargetsList({
  targets,
  currentTargetId,
  loading,
  activatingTargetId,
  scoresByTargetId,
  onActivate,
}: Props) {
  if (loading && targets.length === 0) {
    return (
      <div className="rounded-md border border-border bg-card px-4 py-6 text-center">
        <Loader2 className="h-4 w-4 animate-spin inline-block text-muted-foreground" />
      </div>
    );
  }
  if (targets.length === 0) {
    return (
      <div className="rounded-md border border-border bg-card px-4 py-6 text-center">
        <p className="text-xs text-muted-foreground">No optimization targets yet.</p>
      </div>
    );
  }

  const nodes = buildLineage(targets);
  const targetsById = new Map(targets.map((t) => [t.id, t]));

  const meanFor = (id: string): number | null => {
    const s = scoresByTargetId[id];
    return s?.comprehension_score?.mean ?? null;
  };
  const nFor = (id: string): number => {
    const s = scoresByTargetId[id];
    return s?.comprehension_score?.n ?? 0;
  };

  return (
    <div className="rounded-md border border-border bg-card overflow-hidden">
      <div className="flex items-baseline justify-between px-4 py-2.5 border-b border-border">
        <h4 className="text-sm font-medium">Version history</h4>
        <span className="text-[11px] text-muted-foreground tabular-nums">
          {targets.length} version{targets.length !== 1 ? 's' : ''}
        </span>
      </div>
      <ul className="divide-y divide-border">
        {nodes.map((node) => {
          const t = node.target;
          const isCurrent = t.id === currentTargetId;
          const mean = meanFor(t.id);
          const n = nFor(t.id);
          const parent = t.parent_id ? targetsById.get(t.parent_id) : null;
          const parentMean = parent ? meanFor(parent.id) : null;
          const delta = mean != null && parentMean != null ? mean - parentMean : null;

          return (
            <li
              key={t.id}
              className={`flex items-stretch gap-0 ${isCurrent ? 'bg-emerald-50/40 dark:bg-emerald-900/10' : 'hover:bg-muted/30'} transition-colors`}
            >
              <LineageConnector node={node} />
              <div className="flex-1 min-w-0 flex items-center gap-3 pl-2 pr-4 py-2.5">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono text-[11px] text-muted-foreground" title={t.id}>
                      {t.id.slice(0, 8)}…
                    </span>
                    {isCurrent && (
                      <span className="inline-flex items-center gap-0.5 text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300 font-medium uppercase tracking-wide">
                        <Check className="h-2.5 w-2.5" /> current
                      </span>
                    )}
                    <span className="text-[11px] text-muted-foreground">
                      {t.kind}
                    </span>
                  </div>
                  <div className="text-[11px] text-muted-foreground tabular-nums mt-0.5">
                    {new Date(t.created_at).toLocaleString()}
                  </div>
                </div>

                <div className="shrink-0 text-right tabular-nums min-w-[90px]">
                  {mean != null ? (
                    <>
                      <div className="text-sm font-semibold">{mean.toFixed(1)}</div>
                      <div className="text-[10px] text-muted-foreground">mean · n={n}</div>
                    </>
                  ) : (
                    <div className="text-[11px] text-muted-foreground italic">no evals</div>
                  )}
                </div>

                <div className="shrink-0 text-right tabular-nums min-w-[70px]">
                  {delta != null ? (
                    <span
                      className={`text-xs font-medium ${delta > 0.5 ? 'text-emerald-600 dark:text-emerald-400' : delta < -0.5 ? 'text-red-600 dark:text-red-400' : 'text-muted-foreground'}`}
                    >
                      {delta >= 0 ? '+' : ''}{delta.toFixed(1)}
                    </span>
                  ) : (
                    <span className="text-[11px] text-muted-foreground">—</span>
                  )}
                  <div className="text-[10px] text-muted-foreground">vs parent</div>
                </div>

                <div className="shrink-0">
                  {isCurrent ? (
                    <span className="text-[11px] text-muted-foreground px-2">active</span>
                  ) : (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="h-7 text-[11px]"
                      disabled={activatingTargetId !== null}
                      onClick={() => onActivate(t.id)}
                    >
                      {activatingTargetId === t.id ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        'Activate'
                      )}
                    </Button>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

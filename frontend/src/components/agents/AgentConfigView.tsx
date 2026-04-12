import { Fragment } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { AgentConfig } from '@/types/agents';

interface Props {
  agent: AgentConfig;
}

const PLACEHOLDER_RE = /\{([a-zA-Z_][a-zA-Z0-9_]*)\}/g;

function HighlightedTemplate({ template }: { template: string }) {
  const parts: Array<{ text: string; placeholder: boolean }> = [];
  let lastIndex = 0;
  for (const match of template.matchAll(PLACEHOLDER_RE)) {
    const idx = match.index ?? 0;
    if (idx > lastIndex) parts.push({ text: template.slice(lastIndex, idx), placeholder: false });
    parts.push({ text: match[0], placeholder: true });
    lastIndex = idx + match[0].length;
  }
  if (lastIndex < template.length) parts.push({ text: template.slice(lastIndex), placeholder: false });

  return (
    <pre className="whitespace-pre-wrap break-words rounded-md bg-muted/60 p-4 text-xs font-mono leading-relaxed">
      {parts.map((p, i) => (
        <Fragment key={i}>
          {p.placeholder ? (
            <span className="rounded bg-amber-200/60 px-1 py-0.5 text-amber-950 dark:bg-amber-400/20 dark:text-amber-200">
              {p.text}
            </span>
          ) : (
            p.text
          )}
        </Fragment>
      ))}
    </pre>
  );
}

export function AgentConfigView({ agent }: Props) {
  const { variables, extras } = agent;
  const hasStyles = extras.styles && Object.keys(extras.styles).length > 0;
  const hasPolicies = extras.policies && Object.keys(extras.policies).length > 0;

  return (
    <div className="space-y-3">
      <Card size="sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            System Prompt Template
            <Badge variant="outline" className="text-[10px] font-normal">
              {variables.length} variable{variables.length === 1 ? '' : 's'}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <HighlightedTemplate template={agent.template} />
          <p className="mt-2 text-xs text-muted-foreground">
            Highlighted <code className="font-mono">{'{tokens}'}</code> are substituted at runtime.
          </p>
        </CardContent>
      </Card>

      <Card size="sm">
        <CardHeader>
          <CardTitle>Variables</CardTitle>
        </CardHeader>
        <CardContent>
          {variables.length === 0 ? (
            <p className="text-xs text-muted-foreground">
              No template variables — this prompt is fully static.
            </p>
          ) : (
            <ul className="space-y-3">
              {variables.map((v) => (
                <li key={v.name} className="space-y-1">
                  <div className="flex items-center gap-2">
                    <code className="rounded bg-amber-200/60 px-1.5 py-0.5 text-xs font-mono text-amber-950 dark:bg-amber-400/20 dark:text-amber-200">
                      {`{${v.name}}`}
                    </code>
                    <span className="text-[11px] text-muted-foreground">{v.source}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">{v.description}</p>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card size="sm">
        <CardHeader>
          <CardTitle>Model</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground">{agent.model_note}</p>
        </CardContent>
      </Card>

      {extras.profile_block && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Profile block format</CardTitle>
          </CardHeader>
          <CardContent>
            <HighlightedTemplate template={extras.profile_block} />
            <p className="mt-2 text-xs text-muted-foreground">
              How a sampled persona is rendered into the <code className="font-mono">{'{profile}'}</code> variable.
            </p>
          </CardContent>
        </Card>
      )}

      {hasStyles && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Explanation styles</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(extras.styles!).map(([name, text]) => (
              <div key={name}>
                <div className="text-xs font-medium capitalize">{name}</div>
                <pre className="mt-1 whitespace-pre-wrap break-words rounded bg-muted/60 p-3 text-[11px] font-mono leading-relaxed text-muted-foreground">
                  {text}
                </pre>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {hasPolicies && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Policy overrides</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(extras.policies!).map(([name, text]) => (
              <div key={name}>
                <div className="text-xs font-medium font-mono">{name}</div>
                <pre className="mt-1 whitespace-pre-wrap break-words rounded bg-muted/60 p-3 text-[11px] font-mono leading-relaxed text-muted-foreground">
                  {text || '(none — baseline prompt, no override appended)'}
                </pre>
              </div>
            ))}
            <p className="text-xs text-muted-foreground">
              Selected per-simulation and appended to the rendered prompt.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

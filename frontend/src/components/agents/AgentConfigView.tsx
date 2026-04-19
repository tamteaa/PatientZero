import { Fragment } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

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

function uniquePlaceholders(template: string): string[] {
  return Array.from(new Set(Array.from(template.matchAll(PLACEHOLDER_RE), (m) => m[1])));
}

interface AgentProps {
  name: string;
  prompt: string;
  model: string | null;
}

export function AgentView({ name, prompt, model }: AgentProps) {
  const vars = uniquePlaceholders(prompt);
  return (
    <div className="space-y-3">
      <Card size="sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 capitalize">
            {name}
            <Badge variant="outline" className="text-[10px] font-normal">
              {vars.length} variable{vars.length === 1 ? '' : 's'}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <HighlightedTemplate template={prompt} />
          <p className="mt-2 text-xs text-muted-foreground">
            Highlighted <code className="font-mono">{'{tokens}'}</code> are substituted at runtime
            from the sampled agent profile.
          </p>
        </CardContent>
      </Card>

      <Card size="sm">
        <CardHeader>
          <CardTitle>Model</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground">
            {model ? (
              <>Overrides experiment default with <span className="font-mono text-foreground">{model}</span>.</>
            ) : (
              <>Uses the experiment's default model.</>
            )}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

interface JudgeProps {
  rubric: Record<string, string>;
  instructions: string;
  model: string | null;
}

export function JudgeView({ rubric, instructions, model }: JudgeProps) {
  const rubricEntries = Object.entries(rubric);
  return (
    <div className="space-y-3">
      <Card size="sm">
        <CardHeader>
          <CardTitle>Judge instructions</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="whitespace-pre-wrap break-words rounded-md bg-muted/60 p-4 text-xs font-mono leading-relaxed">
            {instructions || '(none)'}
          </pre>
        </CardContent>
      </Card>

      <Card size="sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Rubric
            <Badge variant="outline" className="text-[10px] font-normal">
              {rubricEntries.length} metric{rubricEntries.length === 1 ? '' : 's'}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {rubricEntries.length === 0 ? (
            <p className="text-xs text-muted-foreground">No metrics defined.</p>
          ) : (
            <ul className="space-y-3">
              {rubricEntries.map(([metric, description]) => (
                <li key={metric} className="space-y-0.5">
                  <code className="text-xs font-mono font-medium">{metric}</code>
                  <p className="text-xs text-muted-foreground">{description}</p>
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
          <p className="text-xs text-muted-foreground">
            {model ? (
              <>Judge uses <span className="font-mono text-foreground">{model}</span>.</>
            ) : (
              <>Judge uses the experiment's default model.</>
            )}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

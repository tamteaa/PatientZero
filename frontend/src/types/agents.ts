export interface AgentVariable {
  name: string;
  source: string;
  description: string;
}

export interface AgentConfig {
  name: string;
  template: string;
  variables: AgentVariable[];
  extras: {
    styles?: Record<string, string>;
    policies?: Record<string, string>;
    profile_block?: string;
  };
  model_note: string;
}

export interface AgentsConfig {
  doctor: AgentConfig;
  patient: AgentConfig;
  judge: AgentConfig;
}

export type AgentName = keyof AgentsConfig;

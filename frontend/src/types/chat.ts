export interface Session {
  id: string;
  title: string;
  created_at: string;
}

export interface Turn {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  turn_number: number;
  created_at: string;
}

export interface SessionDetail extends Session {
  turns: Turn[];
}

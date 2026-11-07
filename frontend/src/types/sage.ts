/**
 * TypeScript types for SAGE frontend.
 * Strictly aligns with backend Pydantic models.
 */

export type ScaffoldingMove = 'QUESTION' | 'HINT' | 'EXPLANATION' | 'WRAP_UP';

export type TopicStatus = 'IN_PROGRESS' | 'DONE';

export interface CitationItem {
  chunk_id: string;
  source_title: string;
  slide_or_section: string;
  excerpt?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  scaffolding_move?: ScaffoldingMove | null;
  citations?: CitationItem[];
  created_at?: string;
}

export interface LearnerState {
  active_topic_id?: string | null;
  struggle_turn_count: number;
  scaffolding_stage: ScaffoldingMove;
  overall_lcc_score: number;
  accumulated_correct_score: number;
  accumulated_wrong_score: number;
  topic_status: TopicStatus;
  active_misconceptions: Record<string, number>;
}

export interface TurnTrace {
  id?: string;
  session_id: string;
  turn_index: number;
  analyzer_output?: any;
  retriever_output?: any;
  tutor_output?: any;
  latency_ms: number;
  created_at?: string;
}

export interface UnitSummary {
  unit_id: string;
  title: string;
}

export interface SessionSummary {
  session_id: string;
  unit_id: string;
  title: string;
  created_at: string;
}

export interface SessionDetail {
  session_id: string;
  unit_id: string;
  messages: Message[];
  learner_state: LearnerState;
  traces: TurnTrace[];
}

export interface TurnResponse {
  message: Message;
  learner_state: LearnerState;
  trace: TurnTrace;
}

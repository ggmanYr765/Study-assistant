export type DocType = "handwritten" | "professor" | "pyq" | "textbook" | "syllabus" | "other";
export type QuestionType = "long" | "short" | "derivation" | "numerical";
export type SkipCategory = "SAFE TO SKIP" | "SKIM ONLY" | "MUST STUDY" | "HIGH RISK";

export interface Session {
  id: string;
  name: string;
  subject: string;
  exam_date: string;
  created_at: string;
}

export interface Document {
  id: string;
  session_id: string;
  filename: string;
  doc_type: DocType;
  page_count: number;
  status: "processing" | "ready" | "error";
  uploaded_at: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface SourceChunk {
  content: string;
  source: string;
  doc_type: string;
  page: number | null;
  relevance: number;
}

export interface ChatResponse {
  answer: string;
  sources: SourceChunk[];
  confidence: "high" | "medium" | "low";
}

export interface PredictedQuestion {
  question: string;
  question_type: QuestionType;
  confidence: number;
  frequency: number;
  estimated_marks: number;
  answer_outline: string;
  topics: string[];
  source_hint: string;
}

export interface QuestionsResponse {
  session_id: string;
  questions: PredictedQuestion[];
  generated_at: string;
}

export interface TopicAnalysis {
  topic: string;
  category: SkipCategory;
  reason: string;
  pyq_frequency: number;
  estimated_marks: number;
  time_to_study_mins: number;
}

export interface SkipResponse {
  session_id: string;
  topics: TopicAnalysis[];
  summary: string;
  generated_at: string;
}

export interface RevisionSheet {
  title: string;
  formulas: string[];
  definitions: string[];
  key_concepts: string[];
  common_mistakes: string[];
  memory_triggers: string[];
  expected_questions: string[];
}

export interface StudyBlock {
  time_slot: string;
  activity: string;
  topic: string;
  duration_mins: number;
  priority: string;
}

export interface EmergencyPlan {
  total_hours: number;
  expected_score_range: string;
  study_blocks: StudyBlock[];
  skip_topics: string[];
  must_cover: string[];
  tips: string[];
}

export interface ExamAnalysis {
  questions: PredictedQuestion[];
  skip_analysis: TopicAnalysis[];
  revision_sheet: RevisionSheet;
  summary: string;
}

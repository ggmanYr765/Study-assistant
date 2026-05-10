import type {
  ChatMessage, ChatResponse, Document, DocType,
  EmergencyPlan, ExamAnalysis, QuestionsResponse,
  Session, SkipResponse, RevisionSheet,
} from "./types";

const BASE = (process.env.NEXT_PUBLIC_API_URL || "") + "/api/v1";

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

// ── Sessions ──────────────────────────────────────────────────────────────────

export const createSession = (name: string, subject: string, exam_date: string) =>
  req<Session>("/sessions", {
    method: "POST",
    body: JSON.stringify({ name, subject, exam_date }),
  });

export const listSessions = () => req<Session[]>("/sessions");

export const getSession = (id: string) => req<Session>(`/sessions/${id}`);

export const deleteSession = (id: string) =>
  fetch(`${BASE}/sessions/${id}`, { method: "DELETE" });

// ── Documents ─────────────────────────────────────────────────────────────────

export async function uploadDocument(sessionId: string, file: File, docType: DocType): Promise<Document> {
  const form = new FormData();
  form.append("file", file);
  form.append("doc_type", docType);
  const res = await fetch(`${BASE}/sessions/${sessionId}/documents`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export const listDocuments = (sessionId: string) =>
  req<Document[]>(`/sessions/${sessionId}/documents`);

// ── Chat ──────────────────────────────────────────────────────────────────────

export const chat = (sessionId: string, message: string, history: ChatMessage[]) =>
  req<ChatResponse>(`/sessions/${sessionId}/chat`, {
    method: "POST",
    body: JSON.stringify({ message, history }),
  });

export function chatStream(sessionId: string, message: string, history: ChatMessage[]) {
  return fetch(`${BASE}/sessions/${sessionId}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });
}

// ── Analysis ──────────────────────────────────────────────────────────────────

export const analyzeExam = (sessionId: string) =>
  req<ExamAnalysis>(`/sessions/${sessionId}/analyze`, { method: "POST" });

export const generateQuestions = (sessionId: string) =>
  req<QuestionsResponse>(`/sessions/${sessionId}/questions/generate`, { method: "POST" });

export const getQuestions = (sessionId: string) =>
  req<QuestionsResponse>(`/sessions/${sessionId}/questions`);

export const analyzeSkip = (sessionId: string) =>
  req<SkipResponse>(`/sessions/${sessionId}/skip/analyze`, { method: "POST" });

export const getSkip = (sessionId: string) =>
  req<SkipResponse>(`/sessions/${sessionId}/skip`);

export const getRevisionSheet = (sessionId: string, topic = "") =>
  req<RevisionSheet>(`/sessions/${sessionId}/revision`, {
    method: "POST",
    body: JSON.stringify({ topic }),
  });

export const getEmergencyPlan = (
  sessionId: string,
  exam_date: string,
  preparation_level: number,
  available_hours: number
) =>
  req<EmergencyPlan>(`/sessions/${sessionId}/plan`, {
    method: "POST",
    body: JSON.stringify({ exam_date, preparation_level, available_hours }),
  });

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { BookOpen, Plus, Trash2 } from "lucide-react";
import { createSession, deleteSession, listSessions } from "@/lib/api";
import type { Session } from "@/lib/types";
import { useEffect } from "react";

export default function HomePage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ name: "", subject: "", exam_date: "" });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    listSessions().then(setSessions).catch(() => {});
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) return;
    setLoading(true);
    try {
      const session = await createSession(form.name, form.subject, form.exam_date);
      router.push(`/session/${session.id}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: string) {
    await deleteSession(id);
    setSessions((prev) => prev.filter((s) => s.id !== id));
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8 gap-12">
      {/* Hero */}
      <div className="text-center space-y-3 max-w-lg">
        <div className="flex items-center justify-center gap-2 text-primary">
          <BookOpen className="w-8 h-8" />
          <span className="text-2xl font-bold tracking-tight">Study Assistant</span>
        </div>
        <p className="text-muted-foreground text-sm leading-relaxed">
          Upload your notes, PYQs, and syllabus. Get probable questions, skip analysis, and a revision plan — optimized for <span className="text-foreground font-medium">marks per minute</span>.
        </p>
      </div>

      {/* New Session */}
      {creating ? (
        <form onSubmit={handleCreate} className="w-full max-w-sm space-y-3 bg-card rounded-xl p-6 border border-border">
          <h2 className="font-semibold text-sm">New Study Session</h2>
          <input
            required
            placeholder="Session name (e.g. OS Exam 2025)"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full bg-input rounded-lg px-3 py-2 text-sm outline-none border border-border focus:border-primary transition-colors"
          />
          <input
            placeholder="Subject (optional)"
            value={form.subject}
            onChange={(e) => setForm({ ...form, subject: e.target.value })}
            className="w-full bg-input rounded-lg px-3 py-2 text-sm outline-none border border-border focus:border-primary transition-colors"
          />
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Exam Date</label>
            <input
              type="date"
              value={form.exam_date}
              onChange={(e) => setForm({ ...form, exam_date: e.target.value })}
              className="w-full bg-input rounded-lg px-3 py-2 text-sm outline-none border border-border focus:border-primary transition-colors"
            />
          </div>
          <div className="flex gap-2 pt-1">
            <button
              type="button"
              onClick={() => setCreating(false)}
              className="flex-1 px-4 py-2 rounded-lg text-sm bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 rounded-lg text-sm bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {loading ? "Creating…" : "Create"}
            </button>
          </div>
        </form>
      ) : (
        <button
          onClick={() => setCreating(true)}
          className="flex items-center gap-2 px-5 py-3 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Session
        </button>
      )}

      {/* Existing sessions */}
      {sessions.length > 0 && (
        <div className="w-full max-w-sm space-y-2">
          <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium">Recent Sessions</p>
          {sessions.map((s) => (
            <div
              key={s.id}
              className="flex items-center gap-3 p-4 bg-card border border-border rounded-xl hover:border-primary/50 transition-colors cursor-pointer group"
              onClick={() => router.push(`/session/${s.id}`)}
            >
              <BookOpen className="w-4 h-4 text-primary shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{s.name}</p>
                {s.subject && <p className="text-xs text-muted-foreground">{s.subject}</p>}
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); handleDelete(s.id); }}
                className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition-all"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}

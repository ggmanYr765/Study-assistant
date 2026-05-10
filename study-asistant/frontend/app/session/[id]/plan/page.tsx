"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Calendar, Loader2, Trash2 } from "lucide-react";
import { getEmergencyPlan } from "@/lib/api";
import type { EmergencyPlan } from "@/lib/types";

const PRIORITY_COLOR: Record<string, string> = {
  HIGH: "border-l-red-500",
  MEDIUM: "border-l-orange-400",
  LOW: "border-l-zinc-600",
};

export default function PlanPage() {
  const { id } = useParams<{ id: string }>();
  const storageKey = `study-plan-${id}`;
  const formKey = `study-plan-form-${id}`;

  const [plan, setPlan] = useState<EmergencyPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem(formKey);
      if (saved) try { return JSON.parse(saved); } catch {}
    }
    return { exam_date: "", preparation_level: 5, available_hours: 8 };
  });

  useEffect(() => {
    const saved = localStorage.getItem(storageKey);
    if (saved) {
      try { setPlan(JSON.parse(saved)); } catch {}
    }
  }, [storageKey]);

  function updateForm(patch: Partial<typeof form>) {
    const next = { ...form, ...patch };
    setForm(next);
    localStorage.setItem(formKey, JSON.stringify(next));
  }

  async function generate(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const result = await getEmergencyPlan(
        id,
        form.exam_date,
        form.preparation_level,
        form.available_hours
      );
      setPlan(result);
      localStorage.setItem(storageKey, JSON.stringify(result));
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  }

  function clear() {
    setPlan(null);
    localStorage.removeItem(storageKey);
  }

  return (
    <div className="p-8 max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Calendar className="w-5 h-5 text-primary" />
            Emergency Study Plan
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Minute-by-minute plan optimized for maximum marks in minimum time
          </p>
        </div>
        {plan && (
          <button
            onClick={clear}
            className="flex items-center gap-1.5 px-3 py-2 border border-border text-muted-foreground rounded-xl text-sm hover:text-red-400 hover:border-red-400/50 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Clear
          </button>
        )}
      </div>

      <form onSubmit={generate} className="bg-card border border-border rounded-xl p-5 space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Exam Date/Time</label>
            <input
              type="datetime-local"
              value={form.exam_date}
              onChange={(e) => updateForm({ exam_date: e.target.value })}
              className="w-full bg-input border border-border rounded-lg px-3 py-2 text-sm outline-none focus:border-primary transition-colors"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">
              Available Hours: {form.available_hours}h
            </label>
            <input
              type="range"
              min={1}
              max={24}
              value={form.available_hours}
              onChange={(e) => updateForm({ available_hours: +e.target.value })}
              className="w-full mt-2"
            />
          </div>
        </div>
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">
            Preparation Level: {form.preparation_level}/10
          </label>
          <input
            type="range"
            min={1}
            max={10}
            value={form.preparation_level}
            onChange={(e) => updateForm({ preparation_level: +e.target.value })}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>Starting fresh</span>
            <span>Well prepared</span>
          </div>
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Calendar className="w-4 h-4" />}
          {loading ? "Generating plan…" : plan ? "Regenerate Plan" : "Generate Plan"}
        </button>
      </form>

      {plan && !loading && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-card border border-border rounded-xl p-4">
              <p className="text-xs text-muted-foreground">Expected Score</p>
              <p className="text-2xl font-bold text-primary">{plan.expected_score_range}</p>
            </div>
            <div className="bg-card border border-border rounded-xl p-4">
              <p className="text-xs text-muted-foreground">Study Hours</p>
              <p className="text-2xl font-bold">{plan.total_hours}h</p>
            </div>
          </div>

          {plan.must_cover.length > 0 && (
            <div className="space-y-2">
              <h2 className="text-sm font-semibold text-orange-400">Must Cover</h2>
              <div className="space-y-1">
                {plan.must_cover.map((t, i) => (
                  <div key={i} className="text-sm px-3 py-1.5 bg-orange-400/5 border border-orange-400/20 rounded-lg">{t}</div>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-2">
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Schedule</h2>
            {plan.study_blocks.map((block, i) => (
              <div
                key={i}
                className={`flex items-center gap-4 p-3 bg-card border border-border border-l-2 rounded-lg ${PRIORITY_COLOR[block.priority] ?? "border-l-zinc-600"}`}
              >
                <div className="shrink-0 text-right w-28">
                  <p className="text-xs font-mono text-muted-foreground">{block.time_slot}</p>
                  <p className="text-xs text-muted-foreground">{block.duration_mins}min</p>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{block.topic || block.activity}</p>
                  {block.topic && <p className="text-xs text-muted-foreground capitalize">{block.activity}</p>}
                </div>
              </div>
            ))}
          </div>

          {plan.skip_topics.length > 0 && (
            <div className="space-y-2">
              <h2 className="text-sm font-semibold text-green-400">Safe to Skip</h2>
              <div className="flex flex-wrap gap-2">
                {plan.skip_topics.map((t, i) => (
                  <span key={i} className="text-xs px-3 py-1 bg-green-400/5 border border-green-400/20 text-green-400 rounded-full line-through">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}

          {plan.tips.length > 0 && (
            <div className="space-y-2">
              <h2 className="text-sm font-semibold text-muted-foreground">Exam Tips</h2>
              <ul className="space-y-1">
                {plan.tips.map((tip, i) => (
                  <li key={i} className="text-sm text-muted-foreground pl-3 border-l border-border">{tip}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

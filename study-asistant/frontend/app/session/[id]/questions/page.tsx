"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { HelpCircle, Loader2, RefreshCw, ChevronDown, ChevronUp, Trash2 } from "lucide-react";
import { generateQuestions, getQuestions } from "@/lib/api";
import type { PredictedQuestion, QuestionsResponse } from "@/lib/types";

const TYPE_LABEL: Record<string, string> = {
  long: "10M", short: "5M", derivation: "Derivation", numerical: "Numerical",
};

export default function QuestionsPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<QuestionsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState("all");
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    getQuestions(id).then(setData).catch(() => {});
  }, [id]);

  async function generate() {
    setLoading(true);
    try {
      const result = await generateQuestions(id);
      setData(result);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  }

  function clear() {
    setData(null);
    setExpanded(null);
    setFilter("all");
  }

  const questions = data?.questions ?? [];
  const filtered = filter === "all" ? questions : questions.filter((q) => q.question_type === filter);

  return (
    <div className="p-8 max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold flex items-center gap-2">
            <HelpCircle className="w-5 h-5 text-primary" />
            Predicted Questions
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Based on PYQ patterns and syllabus emphasis
          </p>
        </div>
        <div className="flex gap-2">
          {data && (
            <button
              onClick={clear}
              className="flex items-center gap-1.5 px-3 py-2 border border-border text-muted-foreground rounded-xl text-sm hover:text-red-400 hover:border-red-400/50 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Clear
            </button>
          )}
          <button
            onClick={generate}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            {data ? "Regenerate" : "Generate"}
          </button>
        </div>
      </div>

      {/* Filter tabs */}
      {questions.length > 0 && (
        <div className="flex gap-1.5">
          {["all", "long", "short", "derivation", "numerical"].map((t) => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              className={`px-3 py-1 rounded-full text-xs capitalize transition-colors ${
                filter === t ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground hover:text-foreground"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center gap-3 py-20 text-muted-foreground">
          <Loader2 className="w-6 h-6 animate-spin text-primary" />
          <span className="text-sm">Predicting questions…</span>
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="text-center text-muted-foreground text-sm py-20">
          <p>No questions yet. Click Generate to predict exam questions from your materials.</p>
        </div>
      )}

      <div className="space-y-2">
        {filtered.map((q, i) => (
          <div key={i} className="bg-card border border-border rounded-xl overflow-hidden">
            <button
              className="w-full text-left p-4 flex items-start gap-3"
              onClick={() => setExpanded(expanded === i ? null : i)}
            >
              <div className="flex-1 min-w-0">
                <div className="flex gap-2 mb-2 flex-wrap">
                  <span className="text-xs px-2 py-0.5 bg-primary/10 text-primary rounded-full font-medium">
                    {TYPE_LABEL[q.question_type] ?? q.question_type}
                  </span>
                  {q.frequency > 1 && (
                    <span className="text-xs px-2 py-0.5 bg-orange-500/10 text-orange-400 rounded-full">
                      Asked {q.frequency}x
                    </span>
                  )}
                  <span className="text-xs px-2 py-0.5 bg-secondary rounded-full">
                    {Math.round(q.confidence * 100)}% likely
                  </span>
                </div>
                <p className="text-sm leading-snug">{q.question}</p>
              </div>
              {expanded === i ? <ChevronUp className="w-4 h-4 shrink-0 text-muted-foreground mt-0.5" /> : <ChevronDown className="w-4 h-4 shrink-0 text-muted-foreground mt-0.5" />}
            </button>
            {expanded === i && q.answer_outline && (
              <div className="px-4 pb-4 border-t border-border pt-3 space-y-2">
                <p className="text-xs font-medium text-muted-foreground">Answer outline</p>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">{q.answer_outline}</p>
                {q.source_hint && (
                  <p className="text-xs text-primary">{q.source_hint}</p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

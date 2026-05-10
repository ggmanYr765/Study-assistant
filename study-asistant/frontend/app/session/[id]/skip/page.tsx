"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { FileText, Loader2, RefreshCw, Trash2 } from "lucide-react";
import { analyzeSkip, getSkip } from "@/lib/api";
import type { SkipCategory, SkipResponse } from "@/lib/types";

const CATEGORY_STYLE: Record<SkipCategory, { pill: string; bar: string }> = {
  "HIGH RISK":    { pill: "text-red-400 bg-red-400/10 border-red-400/30", bar: "bg-red-500" },
  "MUST STUDY":   { pill: "text-orange-400 bg-orange-400/10 border-orange-400/30", bar: "bg-orange-500" },
  "SKIM ONLY":    { pill: "text-yellow-400 bg-yellow-400/10 border-yellow-400/30", bar: "bg-yellow-500" },
  "SAFE TO SKIP": { pill: "text-green-400 bg-green-400/10 border-green-400/30", bar: "bg-green-500" },
};

const ORDER: SkipCategory[] = ["HIGH RISK", "MUST STUDY", "SKIM ONLY", "SAFE TO SKIP"];

export default function SkipPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<SkipResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getSkip(id).then(setData).catch(() => {});
  }, [id]);

  async function analyze() {
    setLoading(true);
    try {
      const result = await analyzeSkip(id);
      setData(result);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  }

  function clear() {
    setData(null);
  }

  const grouped = ORDER.reduce(
    (acc, cat) => {
      acc[cat] = data?.topics.filter((t) => t.category === cat) ?? [];
      return acc;
    },
    {} as Record<SkipCategory, typeof data extends null ? never : SkipResponse["topics"]>
  );

  return (
    <div className="p-8 max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold flex items-center gap-2">
            <FileText className="w-5 h-5 text-primary" />
            Skip Analysis
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            What to study, skim, and safely skip
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
            onClick={analyze}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            {data ? "Reanalyze" : "Analyze"}
          </button>
        </div>
      </div>

      {data && (
        <div className="p-4 bg-card border border-border rounded-xl text-sm text-muted-foreground">
          {data.summary}
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center gap-3 py-20 text-muted-foreground">
          <Loader2 className="w-6 h-6 animate-spin text-primary" />
          <span className="text-sm">Analyzing topics…</span>
        </div>
      )}

      {!loading && !data && (
        <div className="text-center text-muted-foreground text-sm py-20">
          Click Analyze to classify which topics to study and which to skip.
        </div>
      )}

      {data && !loading && ORDER.map((cat) => {
        const topics = grouped[cat];
        if (!topics || topics.length === 0) return null;
        const style = CATEGORY_STYLE[cat];
        return (
          <section key={cat} className="space-y-2">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${style.bar}`} />
              <h2 className="text-sm font-semibold">{cat}</h2>
              <span className="text-xs text-muted-foreground">({topics.length})</span>
            </div>
            <div className="space-y-1.5">
              {topics.map((t, i) => (
                <div key={i} className="flex items-center gap-3 p-3 bg-card border border-border rounded-lg">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{t.topic}</p>
                    <p className="text-xs text-muted-foreground">{t.reason}</p>
                  </div>
                  <div className="text-right shrink-0 space-y-0.5">
                    <p className="text-xs text-muted-foreground">{t.estimated_marks}M</p>
                    <p className="text-xs text-muted-foreground">{t.time_to_study_mins}min</p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}

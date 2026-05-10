"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { Zap, Loader2, ChevronDown, ChevronUp, Trash2, Youtube, ExternalLink } from "lucide-react";
import { analyzeExam } from "@/lib/api";
import { searchYouTube, type YTVideo } from "@/lib/youtube";
import type { ExamAnalysis } from "@/lib/types";

const YOUTUBE_KEY = process.env.NEXT_PUBLIC_YOUTUBE_API_KEY;

export default function ExamModePage() {
  const { id } = useParams<{ id: string }>();
  const storageKey = `exam-analysis-${id}`;
  const videosKey = `exam-videos-${id}`;

  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<ExamAnalysis | null>(null);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState<number | null>(null);
  const [videos, setVideos] = useState<Record<string, YTVideo | null>>({});
  const [videosLoading, setVideosLoading] = useState(false);
  const fetchedRef = useRef(false);

  useEffect(() => {
    const saved = localStorage.getItem(storageKey);
    if (saved) {
      try { setAnalysis(JSON.parse(saved)); } catch {}
    }
    const savedVideos = localStorage.getItem(videosKey);
    if (savedVideos) {
      try { setVideos(JSON.parse(savedVideos)); } catch {}
    }
  }, [storageKey, videosKey]);

  // fetch videos whenever analysis topics change and we have a key
  useEffect(() => {
    if (!analysis || !YOUTUBE_KEY || fetchedRef.current) return;
    const topics = analysis.skip_analysis.map((t) => t.topic);
    if (topics.length === 0) return;

    const existingKeys = Object.keys(videos);
    const missing = topics.filter((t) => !existingKeys.includes(t));
    if (missing.length === 0) return;

    fetchedRef.current = true;
    setVideosLoading(true);

    Promise.allSettled(
      missing.map(async (topic) => {
        const video = await searchYouTube(topic);
        return { topic, video };
      })
    ).then((results) => {
      const newVideos: Record<string, YTVideo | null> = { ...videos };
      for (const r of results) {
        if (r.status === "fulfilled") {
          newVideos[r.value.topic] = r.value.video;
        }
      }
      setVideos(newVideos);
      localStorage.setItem(videosKey, JSON.stringify(newVideos));
      setVideosLoading(false);
    });
  }, [analysis]);

  async function run() {
    setLoading(true);
    setError("");
    fetchedRef.current = false;
    try {
      const result = await analyzeExam(id);
      setAnalysis(result);
      localStorage.setItem(storageKey, JSON.stringify(result));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function clear() {
    setAnalysis(null);
    setVideos({});
    setError("");
    setExpanded(null);
    fetchedRef.current = false;
    localStorage.removeItem(storageKey);
    localStorage.removeItem(videosKey);
  }

  const topics = analysis?.skip_analysis ?? [];

  return (
    <div className="p-8 max-w-3xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Zap className="w-5 h-5 text-primary" />
            Exam Mode
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Predicted questions + study videos + revision sheet
          </p>
        </div>
        <div className="flex gap-2">
          {analysis && (
            <button
              onClick={clear}
              className="flex items-center gap-1.5 px-3 py-2 border border-border text-muted-foreground rounded-xl text-sm hover:text-red-400 hover:border-red-400/50 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Clear
            </button>
          )}
          <button
            onClick={run}
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
            {loading ? "Analyzing…" : analysis ? "Re-run" : "Run Analysis"}
          </button>
        </div>
      </div>

      {error && (
        <div className="text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-xl p-4">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex flex-col items-center gap-3 py-20 text-muted-foreground">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-sm">Analyzing your materials — this may take 30–60 seconds…</p>
        </div>
      )}

      {analysis && !loading && (
        <div className="space-y-8">
          {/* Summary */}
          <div className="p-4 bg-primary/10 border border-primary/20 rounded-xl text-sm text-primary">
            {analysis.summary}
          </div>

          {/* Predicted Questions */}
          <section className="space-y-3">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              Predicted Questions ({analysis.questions.length})
            </h2>
            {analysis.questions.slice(0, 10).map((q, i) => (
              <div key={i} className="bg-card border border-border rounded-xl overflow-hidden">
                <button
                  className="w-full text-left p-4 flex items-start gap-3"
                  onClick={() => setExpanded(expanded === i ? null : i)}
                >
                  <span className="shrink-0 text-xs font-bold text-primary bg-primary/10 rounded-full w-6 h-6 flex items-center justify-center">
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm leading-snug">{q.question}</p>
                    <div className="flex gap-2 mt-2 flex-wrap">
                      <span className="text-xs px-2 py-0.5 bg-secondary rounded-full">{q.question_type}</span>
                      <span className="text-xs px-2 py-0.5 bg-secondary rounded-full">{q.estimated_marks}M</span>
                      <span className="text-xs px-2 py-0.5 bg-secondary rounded-full">
                        {Math.round(q.confidence * 100)}% confidence
                      </span>
                    </div>
                  </div>
                  {expanded === i
                    ? <ChevronUp className="w-4 h-4 shrink-0 text-muted-foreground" />
                    : <ChevronDown className="w-4 h-4 shrink-0 text-muted-foreground" />}
                </button>
                {expanded === i && (
                  <div className="px-4 pb-4 border-t border-border pt-3 text-sm text-muted-foreground space-y-2">
                    <p className="whitespace-pre-wrap">{q.answer_outline}</p>
                    {q.source_hint && <p className="text-xs text-primary">{q.source_hint}</p>}
                  </div>
                )}
              </div>
            ))}
          </section>

          {/* Study Videos */}
          <section className="space-y-3">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                Study Videos
              </h2>
              {videosLoading && <Loader2 className="w-3.5 h-3.5 animate-spin text-muted-foreground" />}
              {!YOUTUBE_KEY && (
                <span className="text-xs text-muted-foreground">(add NEXT_PUBLIC_YOUTUBE_API_KEY to enable)</span>
              )}
            </div>

            {YOUTUBE_KEY && topics.length > 0 && (
              <div className="grid grid-cols-1 gap-3">
                {topics.map((t) => {
                  const video = videos[t.topic];
                  const isLoading = videosLoading && video === undefined;

                  return (
                    <div key={t.topic} className="bg-card border border-border rounded-xl overflow-hidden">
                      {isLoading ? (
                        <div className="flex items-center gap-3 p-4">
                          <div className="w-28 h-16 bg-secondary rounded-lg animate-pulse shrink-0" />
                          <div className="flex-1 space-y-2">
                            <div className="h-3 bg-secondary rounded animate-pulse w-3/4" />
                            <div className="h-3 bg-secondary rounded animate-pulse w-1/2" />
                          </div>
                        </div>
                      ) : video ? (
                        <a
                          href={video.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-3 p-3 hover:bg-secondary/50 transition-colors group"
                        >
                          <div className="relative shrink-0">
                            <img
                              src={video.thumbnail}
                              alt={video.title}
                              className="w-28 h-16 object-cover rounded-lg"
                            />
                            <div className="absolute inset-0 flex items-center justify-center">
                              <div className="w-8 h-8 bg-red-600 rounded-full flex items-center justify-center opacity-90 group-hover:opacity-100 transition-opacity">
                                <Youtube className="w-4 h-4 text-white" />
                              </div>
                            </div>
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-semibold text-primary mb-0.5">{t.topic}</p>
                            <p className="text-sm leading-snug line-clamp-2">{video.title}</p>
                            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                              {video.channel}
                              <ExternalLink className="w-3 h-3" />
                            </p>
                          </div>
                        </a>
                      ) : (
                        <div className="flex items-center gap-3 p-4">
                          <div className="w-28 h-16 bg-secondary rounded-lg shrink-0 flex items-center justify-center">
                            <Youtube className="w-5 h-5 text-muted-foreground" />
                          </div>
                          <div>
                            <p className="text-xs font-semibold text-primary mb-0.5">{t.topic}</p>
                            <p className="text-xs text-muted-foreground">No video found</p>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </section>

          {/* Revision Sheet */}
          <section className="space-y-4">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              Revision Sheet — {analysis.revision_sheet.title}
            </h2>
            {[
              { label: "Key Concepts", items: analysis.revision_sheet.key_concepts },
              { label: "Formulas", items: analysis.revision_sheet.formulas },
              { label: "Definitions", items: analysis.revision_sheet.definitions },
              { label: "Common Mistakes", items: analysis.revision_sheet.common_mistakes },
              { label: "Memory Triggers", items: analysis.revision_sheet.memory_triggers },
            ].map(({ label, items }) =>
              items.length > 0 ? (
                <div key={label} className="space-y-1">
                  <p className="text-xs font-semibold text-muted-foreground">{label}</p>
                  <ul className="space-y-1">
                    {items.map((item, i) => (
                      <li key={i} className="text-sm pl-3 border-l border-border">{item}</li>
                    ))}
                  </ul>
                </div>
              ) : null
            )}
          </section>
        </div>
      )}
    </div>
  );
}

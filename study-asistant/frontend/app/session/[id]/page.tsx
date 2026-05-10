"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { CheckCircle, Clock, FileText, Loader2, Upload } from "lucide-react";
import { getSession, listDocuments, uploadDocument } from "@/lib/api";
import type { DocType, Document, Session } from "@/lib/types";

const DOC_TYPE_OPTIONS: { value: DocType; label: string }[] = [
  { value: "handwritten", label: "Handwritten Notes" },
  { value: "professor", label: "Professor Slides" },
  { value: "pyq", label: "Previous Year Papers" },
  { value: "syllabus", label: "Syllabus" },
  { value: "textbook", label: "Textbook" },
  { value: "other", label: "Other" },
];

export default function SessionPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [docs, setDocs] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [docType, setDocType] = useState<DocType>("other");
  const [dragOver, setDragOver] = useState(false);

  useEffect(() => {
    getSession(id).then(setSession).catch(() => router.push("/"));
    listDocuments(id).then(setDocs).catch(() => {});
  }, [id]);

  // poll for processing docs
  useEffect(() => {
    const processing = docs.some((d) => d.status === "processing");
    if (!processing) return;
    const timer = setInterval(() => {
      listDocuments(id).then(setDocs);
    }, 3000);
    return () => clearInterval(timer);
  }, [docs, id]);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        const doc = await uploadDocument(id, file, docType);
        setDocs((prev) => [doc, ...prev]);
      }
    } finally {
      setUploading(false);
    }
  }

  const readyCount = docs.filter((d) => d.status === "ready").length;

  return (
    <div className="p-8 max-w-2xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">{session?.name ?? "Loading…"}</h1>
        {session?.subject && (
          <p className="text-muted-foreground text-sm mt-1">{session.subject}</p>
        )}
        {session?.exam_date && (
          <p className="text-xs text-primary mt-1">Exam: {session.exam_date}</p>
        )}
      </div>

      {/* Upload zone */}
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <select
            value={docType}
            onChange={(e) => setDocType(e.target.value as DocType)}
            className="bg-input border border-border rounded-lg px-3 py-1.5 text-sm outline-none focus:border-primary"
          >
            {DOC_TYPE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
          <span className="text-xs text-muted-foreground">Select type, then drop files</span>
        </div>

        <label
          className={`flex flex-col items-center justify-center gap-3 border-2 border-dashed rounded-xl p-10 cursor-pointer transition-colors ${
            dragOver ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"
          }`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
        >
          {uploading ? (
            <Loader2 className="w-6 h-6 animate-spin text-primary" />
          ) : (
            <Upload className="w-6 h-6 text-muted-foreground" />
          )}
          <div className="text-center">
            <p className="text-sm font-medium">{uploading ? "Uploading & processing…" : "Drop files here"}</p>
            <p className="text-xs text-muted-foreground mt-1">PDF, PNG, JPG supported</p>
          </div>
          <input
            type="file"
            multiple
            accept=".pdf,.png,.jpg,.jpeg,.webp"
            className="hidden"
            onChange={(e) => handleFiles(e.target.files)}
          />
        </label>
      </div>

      {/* Documents */}
      {docs.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium">
              Uploaded Materials
            </p>
            <span className="text-xs text-muted-foreground">{readyCount}/{docs.length} ready</span>
          </div>
          {docs.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center gap-3 p-3 bg-card border border-border rounded-lg"
            >
              <FileText className="w-4 h-4 text-muted-foreground shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm truncate">{doc.filename}</p>
                <p className="text-xs text-muted-foreground capitalize">{doc.doc_type}</p>
              </div>
              {doc.status === "ready" && <CheckCircle className="w-4 h-4 text-green-500 shrink-0" />}
              {doc.status === "processing" && <Loader2 className="w-4 h-4 animate-spin text-primary shrink-0" />}
              {doc.status === "error" && <span className="text-xs text-red-400">Error</span>}
            </div>
          ))}
        </div>
      )}

      {/* CTA */}
      {readyCount > 0 && (
        <div className="pt-2 border-t border-border">
          <p className="text-sm text-muted-foreground mb-3">
            {readyCount} document{readyCount > 1 ? "s" : ""} ready. Choose a workflow:
          </p>
          <div className="grid grid-cols-2 gap-2">
            {[
              { href: `/session/${id}/exam-mode`, label: "Exam Mode", desc: "Full analysis" },
              { href: `/session/${id}/chat`, label: "Ask a Question", desc: "Source-grounded chat" },
              { href: `/session/${id}/questions`, label: "Predicted Questions", desc: "What will be asked" },
              { href: `/session/${id}/skip`, label: "Skip Analysis", desc: "What to skip" },
            ].map((cta) => (
              <a
                key={cta.href}
                href={cta.href}
                className="p-3 bg-card border border-border rounded-lg hover:border-primary/50 transition-colors"
              >
                <p className="text-sm font-medium">{cta.label}</p>
                <p className="text-xs text-muted-foreground">{cta.desc}</p>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

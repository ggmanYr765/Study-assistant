"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { Send, Trash2 } from "lucide-react";
import { chatStream } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

export default function ChatPage() {
  const { id } = useParams<{ id: string }>();
  const storageKey = `chat-history-${id}`;
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const saved = localStorage.getItem(storageKey);
    if (saved) {
      try { setMessages(JSON.parse(saved)); } catch {}
    }
  }, [storageKey]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function saveMessages(msgs: ChatMessage[]) {
    setMessages(msgs);
    localStorage.setItem(storageKey, JSON.stringify(msgs));
  }

  function clear() {
    setMessages([]);
    localStorage.removeItem(storageKey);
  }

  async function send() {
    if (!input.trim() || loading) return;
    const userMsg: ChatMessage = { role: "user", content: input };
    const next = [...messages, userMsg];
    saveMessages(next);
    setInput("");
    setLoading(true);

    const assistantMsg: ChatMessage = { role: "assistant", content: "" };
    const withAssistant = [...next, assistantMsg];
    setMessages(withAssistant);

    try {
      const res = await chatStream(id, userMsg.content, next);
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let fullContent = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        for (const line of chunk.split("\n")) {
          if (!line.startsWith("data: ")) continue;
          const data = line.slice(6);
          if (data === "[DONE]") break;
          fullContent += data;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = { role: "assistant", content: fullContent };
            return updated;
          });
        }
      }

      // persist completed response
      const final = [...next, { role: "assistant" as const, content: fullContent }];
      localStorage.setItem(storageKey, JSON.stringify(final));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-muted-foreground text-sm pt-20 space-y-2">
            <p className="font-medium text-foreground">Source-grounded chat</p>
            <p>Ask about your uploaded materials. I only answer from your notes.</p>
            <div className="flex flex-wrap gap-2 justify-center pt-4">
              {[
                "What are the most important topics?",
                "Summarize unit 3",
                "What can I skip?",
                "Generate 10-mark questions",
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="px-3 py-1.5 text-xs bg-secondary border border-border rounded-full hover:border-primary/50 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-card border border-border"
              }`}
            >
              {msg.content || (loading && i === messages.length - 1 ? "…" : "")}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-border p-4">
        <div className="flex gap-2 max-w-3xl mx-auto">
          {messages.length > 0 && (
            <button
              onClick={clear}
              title="Clear chat"
              className="px-3 py-2.5 border border-border text-muted-foreground rounded-xl hover:text-red-400 hover:border-red-400/50 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
          <textarea
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
            placeholder="Ask about your study materials…"
            className="flex-1 bg-input border border-border rounded-xl px-4 py-2.5 text-sm resize-none outline-none focus:border-primary transition-colors"
          />
          <button
            onClick={send}
            disabled={loading || !input.trim()}
            className="px-4 py-2.5 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 transition-colors disabled:opacity-40"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

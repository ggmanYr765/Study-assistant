"use client";

import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { BookOpen, MessageSquare, Zap, HelpCircle, FileText, Calendar } from "lucide-react";

const NAV = [
  { href: "", label: "Overview", icon: BookOpen },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/exam-mode", label: "Exam Mode", icon: Zap },
  { href: "/questions", label: "Questions", icon: HelpCircle },
  { href: "/skip", label: "Skip Analysis", icon: FileText },
  { href: "/plan", label: "Study Plan", icon: Calendar },
];

export default function SessionLayout({ children }: { children: React.ReactNode }) {
  const { id } = useParams<{ id: string }>();
  const pathname = usePathname();
  const base = `/session/${id}`;

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar */}
      <aside className="w-52 shrink-0 border-r border-border flex flex-col">
        <div className="p-4 border-b border-border">
          <Link href="/" className="flex items-center gap-2 text-primary">
            <BookOpen className="w-4 h-4" />
            <span className="text-sm font-semibold">Study Assistant</span>
          </Link>
        </div>
        <nav className="flex-1 p-3 space-y-0.5">
          {NAV.map(({ href, label, icon: Icon }) => {
            const full = base + href;
            const active = pathname === full;
            return (
              <Link
                key={href}
                href={full}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                  active
                    ? "bg-primary/15 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary"
                }`}
              >
                <Icon className="w-3.5 h-3.5 shrink-0" />
                {label}
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}

import type { ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`card ${className}`}>{children}</section>;
}

export function ProgressBar({ value, label }: { value: number; label: string }) {
  const width = Math.min(100, Math.max(0, Math.round(value * 100)));
  return (
    <div
      className="progress-track"
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={width}
    >
      <span style={{ width: `${width}%` }} />
    </div>
  );
}

export function Badge({ children, tone = "indigo" }: { children: ReactNode; tone?: string }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export function LoadingState({ label = "Loading your learning space" }: { label?: string }) {
  return (
    <div className="space-y-5" role="status" aria-label={label}>
      <span className="sr-only">{label}</span>
      <div className="skeleton h-9 w-56" />
      <div className="skeleton h-40 w-full" />
      <div className="grid gap-4 md:grid-cols-3">
        <div className="skeleton h-28" />
        <div className="skeleton h-28" />
        <div className="skeleton h-28" />
      </div>
    </div>
  );
}

export function ErrorState({ message, onRetry, secondaryAction }: { message: string; onRetry: () => void; secondaryAction?: ReactNode }) {
  return (
    <Card className="state-card" >
      <Icon name="warning" />
      <h2>We couldn’t load this section</h2>
      <p>{message}</p>
      <button className="button-primary" onClick={onRetry}>Try again</button>
      {secondaryAction}
    </Card>
  );
}

export function EmptyState({ title, body, action }: { title: string; body: string; action?: ReactNode }) {
  return (
    <Card className="state-card">
      <Icon name="book" />
      <h2>{title}</h2>
      <p>{body}</p>
      {action}
    </Card>
  );
}

type IconName = "home" | "learn" | "progress" | "research" | "settings" | "users" | "wifi" | "warning" | "book" | "menu" | "close" | "arrow" | "check";

export function Icon({ name, className = "" }: { name: IconName; className?: string }) {
  const paths: Record<IconName, ReactNode> = {
    home: <><path d="m3 11 9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M9 20v-6h6v6"/></>,
    learn: <><path d="M4 5.5A3.5 3.5 0 0 1 7.5 2H20v17H7.5A3.5 3.5 0 0 0 4 22Z"/><path d="M4 5.5V22"/></>,
    progress: <><path d="M4 20V10"/><path d="M10 20V4"/><path d="M16 20v-7"/><path d="M22 20H2"/></>,
    research: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/><path d="M8 11h6M11 8v6"/></>,
    settings: <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3V2.8h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z"/></>,
    users: <><circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0"/><path d="M16 3.3a4 4 0 0 1 0 7.4M18 14a7 7 0 0 1 4 7"/></>,
    wifi: <><path d="M5 12.6a10 10 0 0 1 14 0M8.5 16a5 5 0 0 1 7 0"/><circle cx="12" cy="20" r="1"/></>,
    warning: <><path d="M12 3 2.5 20h19Z"/><path d="M12 9v4M12 17h.01"/></>,
    book: <><path d="M3 5a3 3 0 0 1 3-3h6v18H6a3 3 0 0 0-3 3Z"/><path d="M21 5a3 3 0 0 0-3-3h-6v18h6a3 3 0 0 1 3 3Z"/></>,
    menu: <path d="M4 6h16M4 12h16M4 18h16"/>,
    close: <path d="m6 6 12 12M18 6 6 18"/>,
    arrow: <path d="m9 18 6-6-6-6"/>,
    check: <path d="m5 12 4 4L19 6"/>,
  };
  return <svg className={`icon ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}

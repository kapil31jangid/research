import { useEffect, useState, type ReactNode } from "react";

import type { CurriculumContext, Learner, Subject } from "../../types";
import { Icon } from "../common/UI";

export type View = "dashboard" | "learn" | "progress" | "research" | "settings";

const primary: { id: View; label: string; icon: "home" | "learn" | "progress" }[] = [
  { id: "dashboard", label: "Dashboard", icon: "home" },
  { id: "learn", label: "Learn", icon: "learn" },
  { id: "progress", label: "Progress", icon: "progress" },
];
const secondary: { id: View; label: string; icon: "research" | "settings" }[] = [
  { id: "research", label: "Research", icon: "research" },
  { id: "settings", label: "Settings", icon: "settings" },
];

export function ApplicationShell({
  children,
  view,
  onNavigate,
  learner,
  learners,
  subjects,
  curriculum,
  onSwitchLearner,
  onSwitchPathway,
  onChooseLearner,
  online,
  pending,
}: {
  children: ReactNode;
  view: View;
  onNavigate: (view: View) => void;
  learner: Learner;
  learners: Learner[];
  subjects: Subject[];
  curriculum?: CurriculumContext;
  onSwitchLearner: (learner: Learner) => void;
  onSwitchPathway: (classLevel: number, subjectId: string) => void;
  onChooseLearner: () => void;
  online: boolean;
  pending: number;
}) {
  const [showResearch, setShowResearch] = useState(
    () => localStorage.getItem("rapid-show-research") !== "false",
  );
  useEffect(() => {
    const update = () => setShowResearch(localStorage.getItem("rapid-show-research") !== "false");
    window.addEventListener("rapid-settings-changed", update);
    return () => window.removeEventListener("rapid-settings-changed", update);
  }, []);
  const visibleSecondary = showResearch
    ? secondary
    : secondary.filter((item) => item.id !== "research");
  const nav = [...primary, ...visibleSecondary];
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Brand />
        <nav aria-label="Primary navigation" className="sidebar-nav">
          {primary.map((item) => <NavButton key={item.id} item={item} active={view === item.id} onNavigate={onNavigate} />)}
        </nav>
        <nav aria-label="Secondary navigation" className="sidebar-nav sidebar-nav-secondary">
          {visibleSecondary.map((item) => <NavButton key={item.id} item={item} active={view === item.id} onNavigate={onNavigate} />)}
        </nav>
        <div className="sidebar-note"><span>Class {learner.class_level}</span><strong>{curriculum?.subject_name ?? "Choose pathway"}</strong><small>{curriculum?.chapter_title}</small></div>
      </aside>
      <div className="app-frame">
        <header className="app-header">
          <div className="mobile-brand"><Brand /></div>
          <div className={`network-pill ${online ? "online" : "offline"}`} role="status">
            <Icon name="wifi" /> {online ? "Online" : "Offline"}
            {pending > 0 && <span>· {pending} to sync</span>}
          </div>
          <label className="curriculum-switcher">
            <span className="sr-only">Active learning pathway</span>
            <select
              aria-label="Active learning pathway"
              value={learner.active_subject_id ?? ""}
              onChange={(event) => {
                const selected = subjects.find((item) => item.id === event.target.value);
                if (selected) onSwitchPathway(selected.class_level, selected.id);
              }}
            >
              {subjects.filter((item) => item.content_status === "available").map((item) => <option key={item.id} value={item.id}>Class {item.class_level} · {item.name}</option>)}
            </select>
          </label>
          <label className="learner-switcher">
            <span className="sr-only">Current learner</span>
            <span className="avatar">{learner.name.charAt(0).toUpperCase()}</span>
            <select value={learner.id} onChange={(event) => {
              const selected = learners.find((item) => item.id === event.target.value);
              if (selected) onSwitchLearner(selected);
            }}>
              {learners.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </label>
          <button className="text-button header-switch" onClick={onChooseLearner}>Manage learners</button>
        </header>
        {!online && <div className="offline-banner">You’re offline. Saved lessons remain available, and answers will sync when your connection returns.</div>}
        <main className="page-container" id="main-content">{children}</main>
      </div>
      <nav className="mobile-nav" aria-label="Mobile navigation">
        {nav.map((item) => (
          <button key={item.id} className={view === item.id ? "active" : ""} onClick={() => onNavigate(item.id)}>
            <Icon name={item.icon} /><span>{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}

function Brand() {
  return <div className="brand"><span className="brand-mark">R</span><span><strong>RAPID-Learn</strong><small>Adaptive learning</small></span></div>;
}

function NavButton({ item, active, onNavigate }: { item: { id: View; label: string; icon: "home" | "learn" | "progress" | "research" | "settings" }; active: boolean; onNavigate: (view: View) => void }) {
  return <button className={active ? "active" : ""} aria-current={active ? "page" : undefined} onClick={() => onNavigate(item.id)}><Icon name={item.icon} /><span>{item.label}</span></button>;
}

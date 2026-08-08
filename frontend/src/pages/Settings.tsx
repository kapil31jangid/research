import { useEffect, useState } from "react";

import { Card } from "../components/common/UI";
import { useLearning } from "../contexts/LearningContext";

export function Settings() {
  const { learner, pending, online } = useLearning();
  const [reduceMotion, setReduceMotion] = useState(() => localStorage.getItem("rapid-reduce-motion") === "true");
  const [showResearch, setShowResearch] = useState(() => localStorage.getItem("rapid-show-research") !== "false");
  useEffect(() => { document.documentElement.dataset.reduceMotion = String(reduceMotion); localStorage.setItem("rapid-reduce-motion", String(reduceMotion)); }, [reduceMotion]);
  useEffect(() => {
    localStorage.setItem("rapid-show-research", String(showResearch));
    window.dispatchEvent(new Event("rapid-settings-changed"));
  }, [showResearch]);
  return <div className="page-stack settings-page"><header className="page-heading"><p className="eyebrow">Local preferences</p><h1>Settings</h1><p>These choices affect this browser only. Adaptive thresholds remain controlled by the validated backend configuration.</p></header><Card><h2>Learner</h2><div className="settings-row"><div><strong>Current profile</strong><p>{learner?.name} · Grade {learner?.grade}</p></div><span className="avatar">{learner?.name.charAt(0).toUpperCase()}</span></div></Card><Card><h2>Offline storage</h2><div className="settings-row"><div><strong>{online ? "Connected" : "Working offline"}</strong><p>Opened activities are cached automatically. {pending} answer{pending === 1 ? " is" : "s are"} waiting to sync.</p></div><span className={`status-dot ${online ? "online" : "offline"}`} /></div></Card><Card><h2>Accessibility</h2><Toggle label="Reduce motion" description="Minimize animated transitions and loading shimmer." checked={reduceMotion} onChange={setReduceMotion} /><Toggle label="Research diagnostics visibility" description="Keep technical explainability available in navigation." checked={showResearch} onChange={setShowResearch} /></Card><Card className="read-only-card"><h2>Adaptive configuration</h2><p>Controller priorities, BKT parameters, resource thresholds, and model versions are read-only here to protect research reproducibility.</p></Card></div>;
}

function Toggle({ label, description, checked, onChange }: { label: string; description: string; checked: boolean; onChange: (checked: boolean) => void }) { return <label className="toggle-row"><span><strong>{label}</strong><small>{description}</small></span><input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} /><i aria-hidden="true" /></label>; }

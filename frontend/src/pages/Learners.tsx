import { useMemo, useState, type FormEvent } from "react";

import { ErrorState, Icon, LoadingState } from "../components/common/UI";
import { useLearning } from "../contexts/LearningContext";

export function Learners({ onReady }: { onReady: () => void }) {
  const {
    learners,
    classes,
    subjects,
    loading,
    error,
    loadLearners,
    selectLearner,
    createLearner,
  } = useLearning();
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [classLevel, setClassLevel] = useState(5);
  const [subjectId, setSubjectId] = useState("ncert-c5-mathematics");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const classSubjects = useMemo(
    () => subjects.filter((subject) => subject.class_level === classLevel),
    [classLevel, subjects],
  );
  const selectedClass = classes.find((item) => item.class_level === classLevel);

  if (loading && learners.length === 0) {
    return <div className="welcome-page"><LoadingState label="Loading learners" /></div>;
  }
  if (error && learners.length === 0) {
    return <div className="welcome-page"><ErrorState message={error} onRetry={() => void loadLearners()} /></div>;
  }

  async function chooseLearner(id: string) {
    const selected = learners.find((item) => item.id === id);
    if (!selected) return;
    await selectLearner(selected);
    onReady();
  }

  function chooseClass(value: number) {
    setClassLevel(value);
    const firstAvailable = subjects.find(
      (subject) => subject.class_level === value && subject.content_status === "available",
    );
    setSubjectId(firstAvailable?.id ?? "");
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!name.trim() || !subjectId) return;
    setSaving(true);
    setFormError(null);
    try {
      await createLearner(name.trim(), classLevel, subjectId);
      setCreating(false);
      onReady();
    } catch {
      setFormError("We couldn’t create this profile. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="welcome-page">
      <header className="welcome-header">
        <div className="brand brand-large"><span className="brand-mark">R</span><span><strong>RAPID-Learn</strong><small>Resource-aware adaptive learning</small></span></div>
        <BadgeLine />
      </header>
      <section className="welcome-copy">
        <p className="eyebrow">Welcome to RAPID-Learn</p>
        <h1>Learning that adapts to each learner.</h1>
        <p>Choose a profile to continue, or create an NCERT-aligned learning space.</p>
      </section>
      {learners.length > 0 ? (
        <div className="learner-grid">
          {learners.map((item) => (
            <button className="learner-card" key={item.id} onClick={() => void chooseLearner(item.id)}>
              <span className="profile-avatar">{item.name.charAt(0).toUpperCase()}</span>
              <span><strong>{item.name}</strong><small>Class {item.class_level} · {item.active_subject_id ? "Mathematics" : "Choose pathway"}</small></span>
              <span className="continue-label">Continue <Icon name="arrow" /></span>
            </button>
          ))}
          <button className="learner-card create-card" onClick={() => setCreating(true)}><span className="profile-avatar plus">+</span><span><strong>Create learner</strong><small>Add a local profile</small></span></button>
        </div>
      ) : (
        <div className="first-learner"><Icon name="users" /><h2>Create your first learner profile</h2><p>Profiles and progress stay on your RAPID-Learn installation.</p><button className="button-primary" onClick={() => setCreating(true)}>Create learner</button></div>
      )}
      {creating && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setCreating(false)}>
          <section className="modal" role="dialog" aria-modal="true" aria-labelledby="create-title" onMouseDown={(event) => event.stopPropagation()}>
            <div className="modal-header"><div><p className="eyebrow">NCERT pathway</p><h2 id="create-title">Create a learner</h2></div><button className="icon-button" aria-label="Close" onClick={() => setCreating(false)}><Icon name="close" /></button></div>
            <form onSubmit={(event) => void submit(event)}>
              <label><span>Name</span><input autoFocus value={name} onChange={(event) => setName(event.target.value)} maxLength={120} placeholder="Learner name" required /></label>
              <label><span>Class</span><select value={classLevel} onChange={(event) => chooseClass(Number(event.target.value))}>{classes.map((item) => <option key={item.class_level} value={item.class_level}>Class {item.class_level}{item.content_status === "available" ? "" : " · coming soon"}</option>)}</select></label>
              <label><span>Board</span><input value="NCERT" readOnly /></label>
              <label><span>Subject</span><select value={subjectId} disabled={selectedClass?.content_status !== "available"} onChange={(event) => setSubjectId(event.target.value)}>{classSubjects.filter((item) => item.content_status === "available").map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
              {selectedClass?.content_status !== "available" && <p className="form-notice">This pathway is not available yet. Classes 5 and 6 Mathematics are currently available.</p>}
              {formError && <p className="form-error" role="alert">{formError}</p>}
              <div className="modal-actions"><button type="button" className="button-secondary" onClick={() => setCreating(false)}>Cancel</button><button className="button-primary" disabled={saving || !subjectId}>{saving ? "Creating…" : "Create learner"}</button></div>
            </form>
          </section>
        </div>
      )}
    </main>
  );
}

function BadgeLine() {
  return <div className="welcome-badge"><span /> Local-first learning</div>;
}

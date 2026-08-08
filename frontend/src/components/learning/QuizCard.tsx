import { useEffect, useState } from "react";

import type { Question } from "../../types";
import { humanize } from "../../utils/format";

export function QuizCard({ question, onSubmit, submitting }: { question: Question; onSubmit: (answer: string, hints: number, elapsedMs: number) => void; submitting: boolean }) {
  const [answer, setAnswer] = useState("");
  const [hints, setHints] = useState(0);
  const [startedAt, setStartedAt] = useState(() => performance.now());
  useEffect(() => { setAnswer(""); setHints(0); setStartedAt(performance.now()); }, [question.id]);
  const hasOptions = question.options.length > 0;
  return <section className="quiz-card"><div className="quiz-meta"><span>{humanize(question.concept_id)}</span><span>Quick check</span></div><h1>{question.text}</h1>{hasOptions ? <div className="answer-grid">{question.options.map((option) => <label key={option} className={answer === option ? "selected" : ""}><input type="radio" name="answer" value={option} checked={answer === option} onChange={() => setAnswer(option)} /><span>{option}</span></label>)}</div> : <label className="answer-input"><span>Your answer</span><input autoComplete="off" inputMode={question.answer_type === "text" ? "text" : "decimal"} value={answer} onChange={(event) => setAnswer(event.target.value)} placeholder="Type a number or fraction" /></label>}<div className="quiz-actions"><button type="button" className="button-secondary" onClick={() => setHints((value) => value + 1)}>Need a hint{hints > 0 ? ` (${hints})` : ""}</button><button type="button" className="button-primary" disabled={!answer.trim() || submitting} onClick={() => onSubmit(answer.trim(), hints, performance.now() - startedAt)}>{submitting ? "Checking…" : "Check answer"}</button></div>{hints > 0 && <p className="hint-box">Think about what the denominator says about the size of each equal part.</p>}</section>;
}

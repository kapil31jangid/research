import type { ActivityContent, ActivitySection, FractionVisualSection, NumberLineSection } from "../../types";

export function ActivityRenderer({ content }: { content: ActivityContent }) {
  return (
    <article className="lesson-content">
      <header className="lesson-heading">
        <p className="eyebrow">Learning goal</p>
        <h1>{content.title}</h1>
        {content.subtitle && <p className="lede">{content.subtitle}</p>}
        {content.learning_objective && <div className="objective">{content.learning_objective}</div>}
      </header>
      <div className="lesson-sections">
        {content.sections.map((section, index) => <Section key={`${section.type}-${index}`} section={section} />)}
      </div>
    </article>
  );
}

function Section({ section }: { section: ActivitySection }) {
  switch (section.type) {
    case "explanation":
      return <section className="content-block"><h2>{section.heading ?? "Understand the idea"}</h2><p>{section.body}</p></section>;
    case "worked_example":
      return <section className="worked-example"><p className="eyebrow">{section.heading}</p><h2>{section.problem}</h2><ol>{section.steps.map((step, index) => <li key={step}><span>{index + 1}</span><p>{step}</p></li>)}</ol><div className="worked-answer"><strong>Answer</strong><span>{section.answer}</span></div>{section.reasoning && <p className="reasoning">{section.reasoning}</p>}</section>;
    case "steps":
      return <section className="content-block"><h2>{section.heading}</h2><ol className="simple-steps">{section.steps.map((step) => <li key={step}>{step}</li>)}</ol></section>;
    case "tip":
    case "formula":
    case "reflection":
      return <aside className={`callout ${section.type}`}><strong>{section.heading ?? (section.type === "tip" ? "Helpful tip" : "Remember")}</strong><p>{section.body}</p></aside>;
    case "warning":
      return <aside className="callout warning"><strong>{section.heading ?? "Common mix-up"}</strong><p>{section.body}</p></aside>;
    case "fraction_bar":
    case "visual_model":
      return <FractionBars section={section} />;
    case "number_line":
      return <NumberLine section={section} />;
    case "checkpoint":
    case "practice":
      return <section className="checkpoint-preview"><p className="eyebrow">{section.heading}</p><h2>{section.prompt}</h2>{section.hint && <p>{section.hint}</p>}</section>;
    default:
      return <aside className="callout warning">This learning block is unavailable, but you can continue with the rest of the lesson.</aside>;
  }
}

function FractionBars({ section }: { section: FractionVisualSection }) {
  const rows = [{ numerator: section.numerator, denominator: section.denominator }];
  if (section.comparison_numerator !== undefined && section.comparison_denominator !== undefined) rows.push({ numerator: section.comparison_numerator, denominator: section.comparison_denominator });
  return <figure className="fraction-visual" aria-label={section.caption}><h2>{section.heading ?? "Fraction model"}</h2>{rows.map((row, rowIndex) => <div className="fraction-row" key={`${row.numerator}-${row.denominator}-${rowIndex}`}><strong>{row.numerator}/{row.denominator}</strong><div className="fraction-parts">{Array.from({ length: row.denominator }, (_, index) => <span key={index} className={index < row.numerator ? "filled" : ""} />)}</div></div>)}<figcaption>{section.caption}</figcaption></figure>;
}

function NumberLine({ section }: { section: NumberLineSection }) {
  return <figure className="number-line-visual"><h2>{section.heading ?? "Number line"}</h2><div className="number-line" aria-label={section.caption}>{Array.from({ length: section.denominator + 1 }, (_, index) => <span key={index} className={section.points.includes(index) ? "marked" : ""}><i /> <small>{index}</small></span>)}</div><figcaption>{section.caption}</figcaption></figure>;
}

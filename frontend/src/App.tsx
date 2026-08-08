import { useState } from "react";

import { ErrorState } from "./components/common/UI";
import { ApplicationShell, type View } from "./components/layout/ApplicationShell";
import { LearningProvider, useLearning } from "./contexts/LearningContext";
import { Dashboard } from "./pages/Dashboard";
import { Learn } from "./pages/Learn";
import { Learners } from "./pages/Learners";
import { Progress } from "./pages/Progress";
import { Research } from "./pages/Research";
import { Settings } from "./pages/Settings";

export default function App() {
  return <LearningProvider><RapidLearnApp /></LearningProvider>;
}

function RapidLearnApp() {
  const {
    learner,
    learners,
    subjects,
    curriculum,
    selectLearner,
    switchPathway,
    online,
    pending,
    error,
    refresh,
  } = useLearning();
  const [view, setView] = useState<View>("dashboard");
  const [choosingLearner, setChoosingLearner] = useState(false);
  if (!learner || choosingLearner) return <Learners onReady={() => { setChoosingLearner(false); setView("dashboard"); }} />;
  const page = error ? <ErrorState message={error} onRetry={() => void refresh()} /> : view === "dashboard" ? <Dashboard onLearn={() => setView("learn")} /> : view === "learn" ? <Learn onReturnDashboard={() => setView("dashboard")} /> : view === "progress" ? <Progress /> : view === "research" ? <Research /> : <Settings />;
  return <ApplicationShell view={view} onNavigate={setView} learner={learner} learners={learners} subjects={subjects} curriculum={curriculum} onSwitchLearner={(selected) => void selectLearner(selected)} onSwitchPathway={(classLevel, subjectId) => void switchPathway(classLevel, subjectId)} onChooseLearner={() => setChoosingLearner(true)} online={online} pending={pending}>{page}</ApplicationShell>;
}

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { useLearning } from "../contexts/LearningContext";
import { learningContext } from "../test/learningContext";
import { Learners } from "./Learners";

vi.mock("../contexts/LearningContext", async () => {
  const actual = await vi.importActual<typeof import("../contexts/LearningContext")>("../contexts/LearningContext");
  return { ...actual, useLearning: vi.fn() };
});

const mockedUseLearning = vi.mocked(useLearning);

describe("curriculum-aware learner onboarding", () => {
  it("renders all classes and keeps unavailable pathways safe", () => {
    mockedUseLearning.mockReturnValue(learningContext({
      learners: [],
      classes: [
        { board_id: "ncert", class_level: 1, content_status: "planned" },
        { board_id: "ncert", class_level: 5, content_status: "available" },
        { board_id: "ncert", class_level: 6, content_status: "available" },
      ],
    }));
    render(<Learners onReady={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "Create learner" }));
    const classSelect = screen.getByLabelText("Class");
    expect(screen.getByRole("option", { name: "Class 1 · coming soon" })).toBeInTheDocument();
    fireEvent.change(classSelect, { target: { value: "1" } });
    expect(screen.getByText("This pathway is not available yet. Classes 5 and 6 Mathematics are currently available.")).toBeInTheDocument();
    expect(screen.getByLabelText("Subject")).toBeDisabled();
  });
});

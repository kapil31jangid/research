import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useLearning } from "../contexts/LearningContext";
import { activityContent } from "../test/fixtures";
import { learningContext } from "../test/learningContext";
import { Dashboard } from "./Dashboard";

vi.mock("../contexts/LearningContext", () => ({ useLearning: vi.fn() }));

const mockedUseLearning = vi.mocked(useLearning);

describe("Dashboard", () => {
  beforeEach(() => {
    mockedUseLearning.mockReturnValue(learningContext());
  });

  it("shows the fresh recommendation and its supporting evidence", async () => {
    const onLearn = vi.fn();
    render(<Dashboard onLearn={onLearn} />);

    expect(await screen.findByRole("heading", { name: activityContent.content.title })).toBeInTheDocument();
    expect(screen.getByText("Here’s what RAPID-Learn recommends next.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Continue learning/ })).toBeInTheDocument();
    expect(screen.getByRole("progressbar", { name: "Recommended concept mastery" })).toHaveAttribute(
      "aria-valuenow",
      "63",
    );
    expect(screen.getByText("Why this lesson?")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Continue learning/ }));
    expect(onLearn).toHaveBeenCalledOnce();
  });

  it("labels a previous lesson honestly while an offline answer is pending", async () => {
    const onLearn = vi.fn();
    mockedUseLearning.mockReturnValue(learningContext({ pending: 1 }));
    render(<Dashboard onLearn={onLearn} />);

    expect(await screen.findByText("Pathway update pending")).toBeInTheDocument();
    expect(screen.getByText("1 answer is waiting to sync")).toBeInTheDocument();
    expect(screen.getByText("Previous saved lesson")).toBeInTheDocument();
    expect(screen.queryByText("Here’s what RAPID-Learn recommends next.")).not.toBeInTheDocument();
    expect(screen.queryByText("Continue learning")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Review previous lesson" }));
    expect(onLearn).toHaveBeenCalledOnce();
  });
});

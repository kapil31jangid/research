import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useLearning } from "../contexts/LearningContext";
import { activityContent, processedInteraction } from "../test/fixtures";
import { learningContext } from "../test/learningContext";
import { Learn } from "./Learn";

vi.mock("../contexts/LearningContext", () => ({ useLearning: vi.fn() }));

const mockedUseLearning = vi.mocked(useLearning);

async function answerCheckpoint() {
  fireEvent.click(await screen.findByRole("button", { name: "Start quick check" }));
  fireEvent.click(screen.getByRole("radio", { name: "3/4" }));
  fireEvent.click(screen.getByRole("button", { name: "Check answer" }));
}

describe("Learn", () => {
  beforeEach(() => {
    mockedUseLearning.mockReturnValue(learningContext());
  });

  it("moves through lesson, checkpoint, processed feedback, and continuation", async () => {
    const submitAnswer = vi.fn().mockResolvedValue(processedInteraction);
    mockedUseLearning.mockReturnValue(learningContext({ submitAnswer }));

    render(<Learn onReturnDashboard={vi.fn()} />);
    expect(await screen.findByRole("heading", { name: activityContent.content.title })).toBeInTheDocument();

    await answerCheckpoint();

    expect(await screen.findByRole("heading", { name: "Nice reasoning." })).toBeInTheDocument();
    expect(screen.getByText("Next adaptive path")).toBeInTheDocument();
    expect(screen.getByText("BKT Based Recommendation")).toBeInTheDocument();
    expect(submitAnswer).toHaveBeenCalledWith("3/4", 0, expect.any(Number));

    fireEvent.click(screen.getByRole("button", { name: "Continue learning" }));
    expect(await screen.findByRole("heading", { name: activityContent.content.title })).toBeInTheDocument();
  });

  it("describes queued offline work without presenting a stale pathway as new", async () => {
    const onReturnDashboard = vi.fn();
    mockedUseLearning.mockReturnValue(
      learningContext({
        online: false,
        loadActivity: vi.fn().mockResolvedValue({ payload: activityContent, source: "cache" }),
        submitAnswer: vi.fn().mockResolvedValue(null),
      }),
    );

    render(<Learn onReturnDashboard={onReturnDashboard} />);
    expect(await screen.findByText("Saved offline")).toBeInTheDocument();
    await answerCheckpoint();

    const status = await screen.findByRole("status");
    expect(status).toHaveTextContent("Saved on this device · Pending sync");
    expect(status).toHaveTextContent("Your answer will sync when you’re back online");
    expect(status).toHaveTextContent("needs that sync before it can calculate your next adaptive pathway");
    expect(screen.queryByText("Next adaptive path")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Return to dashboard" }));
    expect(onReturnDashboard).toHaveBeenCalledOnce();
  });

  it("lets an offline learner review the saved lesson after queueing an answer", async () => {
    mockedUseLearning.mockReturnValue(
      learningContext({
        online: false,
        loadActivity: vi.fn().mockResolvedValue({ payload: activityContent, source: "cache" }),
        submitAnswer: vi.fn().mockResolvedValue(null),
      }),
    );

    render(<Learn onReturnDashboard={vi.fn()} />);
    await answerCheckpoint();
    fireEvent.click(await screen.findByRole("button", { name: "Review saved lesson" }));

    expect(await screen.findByRole("heading", { name: activityContent.content.title })).toBeInTheDocument();
    expect(screen.getByText("Saved offline")).toBeInTheDocument();
  });

  it("shows the cached lesson when the network request falls back to local content", async () => {
    mockedUseLearning.mockReturnValue(
      learningContext({
        loadActivity: vi.fn().mockResolvedValue({ payload: activityContent, source: "cache" }),
      }),
    );

    render(<Learn onReturnDashboard={vi.fn()} />);

    expect(await screen.findByRole("heading", { name: activityContent.content.title })).toBeInTheDocument();
    expect(screen.getByText("Saved offline")).toBeInTheDocument();
  });

  it("offers a checkpoint when recommended content is unavailable offline", async () => {
    mockedUseLearning.mockReturnValue(
      learningContext({
        online: false,
        loadActivity: vi.fn().mockRejectedValue(
          new Error("This recommended activity has not been saved offline yet."),
        ),
      }),
    );

    render(<Learn onReturnDashboard={vi.fn()} />);

    expect(await screen.findByText("This recommended activity has not been saved offline yet.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Continue to the quick check" }));
    expect(await screen.findByRole("heading", { name: "What is 1/4 + 2/4?" })).toBeInTheDocument();
  });

  it("keeps the checkpoint recoverable when submission fails", async () => {
    mockedUseLearning.mockReturnValue(
      learningContext({ submitAnswer: vi.fn().mockRejectedValue(new Error("API unavailable")) }),
    );

    render(<Learn onReturnDashboard={vi.fn()} />);
    await answerCheckpoint();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Your answer could not be submitted. Please try again.",
    );
    await waitFor(() => expect(screen.getByRole("button", { name: "Check answer" })).toBeEnabled());
  });
});

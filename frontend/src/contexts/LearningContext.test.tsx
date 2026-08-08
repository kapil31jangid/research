import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  activityContent,
  learner,
  processedInteraction,
  recommendation,
  resource,
  selection,
  state,
} from "../test/fixtures";
import { LearningProvider, useLearning } from "./LearningContext";

const mocks = vi.hoisted(() => ({
  learners: vi.fn(),
  next: vi.fn(),
  state: vi.fn(),
  recommendations: vi.fn(),
  resources: vi.fn(),
  activity: vi.fn(),
  submit: vi.fn(),
  createLearner: vi.fn(),
  cacheActivityContent: vi.fn(),
  cachedActivityContent: vi.fn(),
  cachedContentMetadata: vi.fn(),
  flushQueue: vi.fn(),
  queueInteraction: vi.fn(),
  queuedCount: vi.fn(),
}));

vi.mock("../services/api", () => ({
  api: {
    learners: mocks.learners,
    next: mocks.next,
    state: mocks.state,
    recommendations: mocks.recommendations,
    resources: mocks.resources,
    activity: mocks.activity,
    submit: mocks.submit,
    createLearner: mocks.createLearner,
  },
}));

vi.mock("../offline/store", () => ({
  cacheActivityContent: mocks.cacheActivityContent,
  cachedActivityContent: mocks.cachedActivityContent,
  cachedContentMetadata: mocks.cachedContentMetadata,
  flushQueue: mocks.flushQueue,
  queueInteraction: mocks.queueInteraction,
  queuedCount: mocks.queuedCount,
}));

function setOnline(value: boolean) {
  Object.defineProperty(window.navigator, "onLine", { configurable: true, value });
}

function ActivityHarness() {
  const { loadActivity } = useLearning();
  const [result, setResult] = useState("");
  return (
    <div>
      <button
        onClick={() => {
          void loadActivity(activityContent.activity.id)
            .then(({ payload, source }) => setResult(`${source}:${payload.content.title}`))
            .catch((error: unknown) => setResult(error instanceof Error ? error.message : "unknown error"));
        }}
      >
        Load activity
      </button>
      <output>{result}</output>
    </div>
  );
}

function SyncHarness() {
  const { learner: selected, pending, recommendations, selectLearner, submitAnswer } = useLearning();
  return (
    <div>
      <button onClick={() => void selectLearner(learner)}>Select learner</button>
      <button onClick={() => void submitAnswer("3/4", 0, 1200)}>Submit answer</button>
      <output>selected:{selected?.id ?? "none"}</output>
      <output>pending:{pending}</output>
      <output>activity:{recommendations[0]?.selected_activity_id ?? "none"}</output>
    </div>
  );
}

describe("LearningProvider offline behavior", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setOnline(true);
    mocks.learners.mockResolvedValue([learner]);
    mocks.next.mockResolvedValue(selection);
    mocks.state.mockResolvedValue([state]);
    mocks.recommendations.mockResolvedValue([recommendation]);
    mocks.resources.mockResolvedValue(resource);
    mocks.activity.mockResolvedValue(activityContent);
    mocks.submit.mockResolvedValue(processedInteraction);
    mocks.cacheActivityContent.mockResolvedValue(undefined);
    mocks.cachedActivityContent.mockResolvedValue(undefined);
    mocks.cachedContentMetadata.mockResolvedValue({ activityIds: [], conceptIds: [] });
    mocks.flushQueue.mockResolvedValue(undefined);
    mocks.queueInteraction.mockResolvedValue(undefined);
    mocks.queuedCount.mockResolvedValue(0);
  });

  afterEach(() => setOnline(true));

  it("falls back to cached content after a network content request fails", async () => {
    mocks.activity.mockRejectedValue(new Error("network failed"));
    mocks.cachedActivityContent.mockResolvedValue(activityContent);
    render(<LearningProvider><ActivityHarness /></LearningProvider>);

    fireEvent.click(screen.getByRole("button", { name: "Load activity" }));

    expect(await screen.findByText(`cache:${activityContent.content.title}`)).toBeInTheDocument();
    expect(mocks.activity).toHaveBeenCalledWith(activityContent.activity.id);
    expect(mocks.cachedActivityContent).toHaveBeenCalledWith(activityContent.activity.id);
  });

  it("returns a clear error when offline content was never cached", async () => {
    setOnline(false);
    render(<LearningProvider><ActivityHarness /></LearningProvider>);

    fireEvent.click(screen.getByRole("button", { name: "Load activity" }));

    expect(
      await screen.findByText("This recommended activity has not been saved offline yet."),
    ).toBeInTheDocument();
    expect(mocks.activity).not.toHaveBeenCalled();
  });

  it("flushes queued answers and refreshes the selected learner after reconnect", async () => {
    setOnline(false);
    const refreshed = { ...recommendation, id: "recommendation-fresh", selected_activity_id: "fresh_activity" };
    mocks.recommendations
      .mockResolvedValueOnce([recommendation])
      .mockResolvedValueOnce([refreshed]);
    mocks.queuedCount
      .mockResolvedValueOnce(1)
      .mockResolvedValueOnce(0);

    render(<LearningProvider><SyncHarness /></LearningProvider>);
    await waitFor(() => expect(screen.getByText("pending:1")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Select learner" }));
    await waitFor(() => expect(screen.getByText("activity:addition_steps")).toBeInTheDocument());

    act(() => {
      setOnline(true);
      window.dispatchEvent(new Event("online"));
    });

    await waitFor(() => expect(mocks.flushQueue).toHaveBeenCalledWith(mocks.submit));
    await waitFor(() => expect(screen.getByText("pending:0")).toBeInTheDocument());
    expect(screen.getByText("activity:fresh_activity")).toBeInTheDocument();
  });

  it("refreshes the selected learner with a fresh recommendation after an online submission", async () => {
    const refreshed = { ...recommendation, id: "recommendation-fresh", selected_activity_id: "fresh_activity" };
    mocks.recommendations
      .mockResolvedValueOnce([recommendation])
      .mockResolvedValueOnce([refreshed]);

    render(<LearningProvider><SyncHarness /></LearningProvider>);
    fireEvent.click(screen.getByRole("button", { name: "Select learner" }));
    await waitFor(() => expect(screen.getByText("activity:addition_steps")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Submit answer" }));

    await waitFor(() => expect(mocks.submit).toHaveBeenCalledOnce());
    await waitFor(() => expect(screen.getByText("activity:fresh_activity")).toBeInTheDocument());
  });
});

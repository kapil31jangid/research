import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ActivitySection } from "../../types";
import { activityContent } from "../../test/fixtures";
import { ActivityRenderer } from "./ActivityRenderer";

describe("ActivityRenderer", () => {
  it("renders each supported lesson section with meaningful content", () => {
    render(<ActivityRenderer content={activityContent.content} />);

    expect(screen.getByRole("heading", { name: activityContent.content.title })).toBeInTheDocument();
    expect(screen.getByText("Fractions need equal-sized parts before they can be added.")).toBeInTheDocument();
    expect(screen.getByRole("figure", { name: "Both bars show the same amount." })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Find 1/2 + 1/4." })).toBeInTheDocument();
    expect(screen.getByText("Rename 1/2 as 2/4.")).toBeInTheDocument();
    expect(screen.getByText("3/4")).toBeInTheDocument();
    expect(screen.getByText("Find a shared denominator.")).toBeInTheDocument();
    expect(screen.getByText("Draw a fraction bar when you are unsure.")).toBeInTheDocument();
    expect(screen.getByText("Do not add the denominators.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "What is 1/4 + 2/4?" })).toBeInTheDocument();
  });

  it("keeps the rest of a lesson usable when a section type is unknown", () => {
    const unknownSection = { type: "future_learning_block" } as unknown as ActivitySection;
    render(
      <ActivityRenderer
        content={{ ...activityContent.content, sections: [unknownSection, ...activityContent.content.sections] }}
      />,
    );

    expect(
      screen.getByText("This learning block is unavailable, but you can continue with the rest of the lesson."),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Find 1/2 + 1/4." })).toBeInTheDocument();
  });
});

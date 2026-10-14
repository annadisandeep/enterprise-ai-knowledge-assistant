import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { Citations } from "./Citations";
import type { Citation } from "../types";

const citations: Citation[] = [
  {
    document_id: "d1",
    filename: "policy.md",
    chunk_id: "d1:0",
    chunk_index: 0,
    similarity: 0.82,
    snippet: "Employees may work remotely three days per week.",
  },
];

describe("Citations", () => {
  it("shows a source count and reveals snippets on toggle", async () => {
    const user = userEvent.setup();
    render(<Citations citations={citations} />);

    expect(screen.getByText(/1 source/i)).toBeInTheDocument();
    // Snippet hidden until expanded.
    expect(screen.queryByText(/work remotely three days/i)).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /1 source/i }));
    expect(screen.getByText(/work remotely three days/i)).toBeInTheDocument();
    expect(screen.getByText(/82% match/i)).toBeInTheDocument();
  });

  it("renders nothing when there are no citations", () => {
    const { container } = render(<Citations citations={[]} />);
    expect(container).toBeEmptyDOMElement();
  });
});

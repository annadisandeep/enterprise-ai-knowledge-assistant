import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ChatMessage } from "./ChatMessage";
import type { ChatMessage as Msg } from "../types";

describe("ChatMessage", () => {
  it("renders a user message verbatim", () => {
    const msg: Msg = { id: "1", role: "user", content: "What is the policy?" };
    render(<ChatMessage message={msg} />);
    expect(screen.getByText("What is the policy?")).toBeInTheDocument();
  });

  it("renders a grounded assistant answer with markdown and a grounded badge", () => {
    const msg: Msg = {
      id: "2",
      role: "assistant",
      content: "You may work **remotely** three days. [Source 1]",
      grounded: true,
      usedFallback: false,
      citations: [
        {
          document_id: "d1",
          filename: "policy.md",
          chunk_id: "d1:0",
          chunk_index: 0,
          similarity: 0.9,
          snippet: "remote three days",
        },
      ],
      model: "mock-model",
    };
    render(<ChatMessage message={msg} />);
    expect(screen.getByText(/grounded in your documents/i)).toBeInTheDocument();
    // Markdown bold is rendered as <strong>.
    expect(screen.getByText("remotely").tagName).toBe("STRONG");
    expect(screen.getByText(/1 source/i)).toBeInTheDocument();
  });

  it("shows the no-answer badge when the response used the fallback", () => {
    const msg: Msg = {
      id: "3",
      role: "assistant",
      content: "I don't have enough information…",
      grounded: false,
      usedFallback: true,
      citations: [],
    };
    render(<ChatMessage message={msg} />);
    expect(screen.getByText(/no grounded answer found/i)).toBeInTheDocument();
  });

  it("renders an error bubble for a failed request", () => {
    const msg: Msg = {
      id: "4",
      role: "assistant",
      content: "The AI service is unavailable.",
      error: true,
    };
    render(<ChatMessage message={msg} />);
    expect(screen.getByText(/the ai service is unavailable/i)).toBeInTheDocument();
    // No grounded/citation chrome on an error message.
    expect(screen.queryByText(/source/i)).not.toBeInTheDocument();
  });
});

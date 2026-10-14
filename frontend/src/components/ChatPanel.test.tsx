import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ChatPanel } from "./ChatPanel";
import { askQuestion } from "../lib/api";
import type { ChatResponse } from "../types";

vi.mock("../lib/api", () => {
  class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  }
  return { ApiError, askQuestion: vi.fn() };
});

const mockedAsk = vi.mocked(askQuestion);

const grounded: ChatResponse = {
  answer: "Employees may work remotely **three days** per week. [Source 1]",
  citations: [
    {
      document_id: "d1",
      filename: "policy.md",
      chunk_id: "d1:0",
      chunk_index: 0,
      similarity: 0.8,
      snippet: "work remotely three days per week",
    },
  ],
  grounded: true,
  model: "mock-model",
  used_fallback: false,
};

describe("ChatPanel", () => {
  beforeEach(() => mockedAsk.mockReset());

  it("sends a question and renders a grounded answer with a source", async () => {
    mockedAsk.mockResolvedValue(grounded);
    const user = userEvent.setup();
    render(<ChatPanel hasDocuments={true} />);

    await user.type(
      screen.getByLabelText(/ask a question/i),
      "How many remote days?",
    );
    await user.click(screen.getByRole("button", { name: /send question/i }));

    await waitFor(() => expect(mockedAsk).toHaveBeenCalledWith("How many remote days?"));
    expect(await screen.findByText(/three days/i)).toBeInTheDocument();
    expect(screen.getByText(/grounded in your documents/i)).toBeInTheDocument();
    expect(screen.getByText(/1 source/i)).toBeInTheDocument();
    // The user's own message is shown too.
    expect(screen.getByText("How many remote days?")).toBeInTheDocument();
  });

  it("disables send when the input is empty", () => {
    render(<ChatPanel hasDocuments={false} />);
    expect(screen.getByRole("button", { name: /send question/i })).toBeDisabled();
  });
});

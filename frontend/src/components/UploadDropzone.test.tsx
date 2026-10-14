import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { UploadDropzone } from "./UploadDropzone";
import { uploadDocument } from "../lib/api";

vi.mock("../lib/api", () => {
  class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  }
  return { ApiError, uploadDocument: vi.fn() };
});

const mockedUpload = vi.mocked(uploadDocument);

function getFileInput(): HTMLInputElement {
  // The hidden file input inside the dropzone.
  const input = document.querySelector('input[type="file"]');
  if (!input) throw new Error("file input not found");
  return input as HTMLInputElement;
}

describe("UploadDropzone", () => {
  beforeEach(() => mockedUpload.mockReset());

  it("uploads a valid file and reports success", async () => {
    mockedUpload.mockResolvedValue({
      document: {
        id: "d1",
        filename: "notes.txt",
        content_type: "text/plain",
        size_bytes: 10,
        char_count: 10,
        chunk_count: 1,
        sha256: "x".repeat(64),
        uploaded_at: new Date().toISOString(),
      },
      message: "ok",
    });
    const onUploaded = vi.fn();
    const user = userEvent.setup();
    render(<UploadDropzone onUploaded={onUploaded} />);

    const file = new File(["hello world"], "notes.txt", { type: "text/plain" });
    await user.upload(getFileInput(), file);

    await waitFor(() => expect(mockedUpload).toHaveBeenCalledTimes(1));
    expect(await screen.findByText(/indexed/i)).toBeInTheDocument();
    expect(onUploaded).toHaveBeenCalled();
  });

  it("rejects an unsupported file type without calling the API", async () => {
    // applyAccept:false bypasses the input's `accept` filter so the component's
    // own client-side validation (not just the browser picker) is exercised.
    const user = userEvent.setup({ applyAccept: false });
    render(<UploadDropzone onUploaded={vi.fn()} />);

    const bad = new File(["MZ"], "malware.exe", { type: "application/octet-stream" });
    await user.upload(getFileInput(), bad);

    expect(await screen.findByText(/unsupported type/i)).toBeInTheDocument();
    expect(mockedUpload).not.toHaveBeenCalled();
  });
});

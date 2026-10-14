import { describe, expect, it } from "vitest";
import { fileExtension, formatBytes } from "./utils";

describe("formatBytes", () => {
  it("formats bytes, KB and MB", () => {
    expect(formatBytes(512)).toBe("512 B");
    expect(formatBytes(2048)).toBe("2.0 KB");
    expect(formatBytes(5 * 1024 * 1024)).toBe("5.0 MB");
  });
});

describe("fileExtension", () => {
  it("returns lowercased extension with dot", () => {
    expect(fileExtension("Report.PDF")).toBe(".pdf");
    expect(fileExtension("notes.md")).toBe(".md");
  });
  it("returns empty string when no extension", () => {
    expect(fileExtension("README")).toBe("");
  });
});

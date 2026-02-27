import { describe, expect, test } from "bun:test";
import { homedir } from "node:os";
import { join } from "node:path";

import {
  buildEditorCommand,
  buildFolderOpenCommand,
  getMcpConfigPath,
  openMcpConfigFolder,
  openMcpConfigInEditor,
  resolveEditor,
} from "../../src/tui/utils/openers";

describe("tui openers", () => {
  test("getMcpConfigPath resolves known targets", () => {
    expect(getMcpConfigPath("claude")).toBe(
      join(homedir(), ".claude", "claude_desktop_config.json"),
    );
    expect(getMcpConfigPath("opencode")).toBe(
      join(homedir(), ".config", "opencode", "config.json"),
    );
    expect(getMcpConfigPath("codex")).toBeNull();
  });

  test("resolveEditor falls back to vim", () => {
    expect(resolveEditor({})).toBe("vim");
    expect(resolveEditor({ EDITOR: "nvim" })).toBe("nvim");
  });

  test("buildEditorCommand appends config path and respects EDITOR", () => {
    const configPath = "/tmp/config.json";

    expect(buildEditorCommand(configPath, { EDITOR: "nvim" })).toEqual([
      "nvim",
      [configPath],
    ]);
    expect(buildEditorCommand(configPath, {})).toEqual(["vim", [configPath]]);
  });

  test("buildFolderOpenCommand uses OS-specific open command", () => {
    const configPath = "/tmp/config.json";

    expect(buildFolderOpenCommand(configPath, "darwin")).toEqual([
      "open",
      ["/tmp"],
    ]);
    expect(buildFolderOpenCommand(configPath, "linux")).toEqual([
      "xdg-open",
      ["/tmp"],
    ]);
  });

  test("openMcpConfigInEditor runs resolved editor command", async () => {
    const calls: Array<[string, string[]]> = [];
    const result = await openMcpConfigInEditor(
      "claude",
      async (command, args) => {
        calls.push([command, args]);
      },
      { EDITOR: "nvim" },
    );

    expect(result.success).toBe(true);
    expect(calls).toHaveLength(1);
    expect(calls[0]).toEqual([
      "nvim",
      [join(homedir(), ".claude", "claude_desktop_config.json")],
    ]);
  });

  test("openMcpConfigFolder uses requested platform command", async () => {
    const calls: Array<[string, string[]]> = [];
    const result = await openMcpConfigFolder(
      "opencode",
      async (command, args) => {
        calls.push([command, args]);
      },
      "linux",
    );

    expect(result.success).toBe(true);
    expect(calls).toEqual([
      ["xdg-open", [join(homedir(), ".config", "opencode")]],
    ]);
  });

  test("openers return failure when target has no MCP config", async () => {
    let called = false;
    const result = await openMcpConfigInEditor("codex", async () => {
      called = true;
    });

    expect(result.success).toBe(false);
    expect(result.message).toContain("not available");
    expect(called).toBe(false);
  });
});

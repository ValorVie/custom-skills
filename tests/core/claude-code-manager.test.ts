import { describe, expect, test } from "bun:test";

import {
  getClaudeInstallType,
  showClaudeStatus,
  updateClaudeCode,
} from "../../src/core/claude-code-manager";

describe("core/claude-code-manager", () => {
  test("getClaudeInstallType returns null when claude not found", async () => {
    const result = await getClaudeInstallType({
      commandExistsFn: () => false,
      runCommandFn: async () => ({ exitCode: 1, stdout: "", stderr: "" }),
    });

    expect(result).toBeNull();
  });

  test("getClaudeInstallType returns npm when npm package exists", async () => {
    const result = await getClaudeInstallType({
      commandExistsFn: (command: string) =>
        command === "claude" || command === "npm",
      runCommandFn: async (command: string[]) => {
        if (command[0] === "npm" && command[1] === "list") {
          return {
            exitCode: 0,
            stdout: "@anthropic-ai/claude-code@1.0.0",
            stderr: "",
          };
        }

        return { exitCode: 1, stdout: "", stderr: "" };
      },
    });

    expect(result).toBe("npm");
  });

  test("getClaudeInstallType returns native when not npm", async () => {
    const result = await getClaudeInstallType({
      commandExistsFn: (command: string) => command === "claude",
      runCommandFn: async (command: string[]) => {
        if (command[0] === "npm" && command[1] === "list") {
          return { exitCode: 1, stdout: "", stderr: "" };
        }

        return { exitCode: 0, stdout: "", stderr: "" };
      },
    });

    expect(result).toBe("native");
  });

  test("showClaudeStatus returns version for native install", async () => {
    const progress: string[] = [];

    const result = await showClaudeStatus(
      (message: string) => {
        progress.push(message);
      },
      {
        commandExistsFn: (command: string) => command === "claude",
        runCommandFn: async (command: string[]) => {
          if (command[0] === "npm" && command[1] === "list") {
            return { exitCode: 1, stdout: "", stderr: "" };
          }
          if (command[0] === "claude" && command[1] === "--version") {
            return { exitCode: 0, stdout: "2.1.0\n", stderr: "" };
          }

          return { exitCode: 0, stdout: "", stderr: "" };
        },
      },
    );

    expect(result.type).toBe("native");
    expect(result.version).toBe("2.1.0");
    expect(progress.some((line) => line.includes("Claude Code"))).toBe(true);
  });

  test("showClaudeStatus falls back to stderr for version output", async () => {
    const result = await showClaudeStatus(() => {}, {
      commandExistsFn: (command: string) => command === "claude",
      runCommandFn: async (command: string[]) => {
        if (command[0] === "npm" && command[1] === "list") {
          return { exitCode: 1, stdout: "", stderr: "" };
        }
        if (command[0] === "claude" && command[1] === "--version") {
          return { exitCode: 0, stdout: "", stderr: "2.2.0\n" };
        }

        return { exitCode: 0, stdout: "", stderr: "" };
      },
    });

    expect(result.type).toBe("native");
    expect(result.version).toBe("2.2.0");
  });

  test("updateClaudeCode uses npm update path for npm installs", async () => {
    const commands: string[][] = [];

    const result = await updateClaudeCode(() => {}, {
      commandExistsFn: (command: string) =>
        command === "claude" || command === "npm",
      runCommandFn: async (command: string[]) => {
        commands.push(command);
        if (command[0] === "npm" && command[1] === "list") {
          return {
            exitCode: 0,
            stdout: "@anthropic-ai/claude-code@1.0.0",
            stderr: "",
          };
        }
        return { exitCode: 0, stdout: "", stderr: "" };
      },
    });

    expect(result.success).toBe(true);
    expect(
      commands.some(
        (command) =>
          command[0] === "npm" &&
          command[1] === "install" &&
          command[2] === "-g",
      ),
    ).toBe(true);
  });

  test("updateClaudeCode reports native version after successful update", async () => {
    const progress: string[] = [];

    const result = await updateClaudeCode(
      (message: string) => {
        progress.push(message);
      },
      {
        commandExistsFn: (command: string) =>
          command === "claude" || command === "npm",
        runCommandFn: async (command: string[]) => {
          if (command[0] === "npm" && command[1] === "list") {
            return { exitCode: 1, stdout: "", stderr: "" };
          }
          if (command[0] === "claude" && command[1] === "update") {
            return { exitCode: 0, stdout: "", stderr: "" };
          }
          if (command[0] === "claude" && command[1] === "--version") {
            return { exitCode: 0, stdout: "2.1.0\n", stderr: "" };
          }
          return { exitCode: 0, stdout: "", stderr: "" };
        },
      },
    );

    expect(result.success).toBe(true);
    expect(
      progress.some((line) => line.includes("更新完成") && line.includes("2.1.0")),
    ).toBe(true);
  });
});

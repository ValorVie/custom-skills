import { beforeEach, describe, expect, test } from "bun:test";

import { handleInstallCommand } from "../../src/cli/install";
import type { InstallResult } from "../../src/core/installer";
import { setLocale } from "../../src/utils/i18n";

function createInstallResult(): InstallResult {
  return {
    prerequisites: { node: true, git: true, gh: true, bun: true },
    prerequisiteDetails: {
      node: {
        installed: true,
        version: "v20.0.0",
        meetsRequirement: true,
      },
      git: {
        installed: true,
        version: "git version 2.0.0",
        meetsRequirement: true,
      },
      gh: {
        installed: true,
        version: "gh version 2.0.0",
        meetsRequirement: true,
      },
      bun: {
        installed: true,
        version: "1.3.0",
        meetsRequirement: true,
      },
    },
    claudeCode: { installed: true, version: "2.0.0" },
    npmPackages: [],
    bunPackages: [],
    repos: [],
    customRepos: [],
    skills: { installed: [], conflicts: [] },
    shellCompletion: {
      name: "shell-completion",
      success: true,
      message: "ok",
    },
    npmHint: null,
    errors: [],
  };
}

describe("cli/install output parity", () => {
  beforeEach(() => {
    setLocale("zh-TW");
  });

  test("non-json output includes start and completion via formatter", async () => {
    const progressMessages: string[] = [];
    const runInstallCalls: Array<{
      stream?: boolean;
      onProgress?: (message: string) => void;
    }> = [];
    const originalLog = console.log;

    console.log = () => {};

    try {
      await handleInstallCommand(
        {
          skipNpm: true,
          skipBun: true,
          skipRepos: true,
          skipSkills: true,
          syncProject: false,
          json: false,
        },
        {
          runInstallFn: async (options) => {
            runInstallCalls.push({
              stream: options.stream,
              onProgress: options.onProgress,
            });

            options.onProgress?.("開始安裝...");
            options.onProgress?.("檢查 Claude Code 安裝狀態...");
            return createInstallResult();
          },
          formatProgressFn: (message) => {
            progressMessages.push(message);
          },
        },
      );
    } finally {
      console.log = originalLog;
    }

    expect(runInstallCalls[0]?.stream).toBe(true);
    expect(typeof runInstallCalls[0]?.onProgress).toBe("function");
    expect(progressMessages).toContain("開始安裝...");
    expect(progressMessages).toContain("安裝完成！");
    expect(
      progressMessages.filter((message) => message === "安裝完成！").length,
    ).toBe(1);
  });
});

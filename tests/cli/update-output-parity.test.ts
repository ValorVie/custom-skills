import { beforeEach, describe, expect, test } from "bun:test";

import { handleUpdateCommand } from "../../src/cli/update";
import type { UpdateResult } from "../../src/core/updater";
import { setLocale } from "../../src/utils/i18n";

function createUpdateResult(): UpdateResult {
  return {
    claudeCode: { name: "claude-code", success: true, message: undefined },
    tools: [],
    npmPackages: [],
    bunPackages: [],
    repos: [],
    customRepos: [],
    plugins: [],
    summary: {
      updated: [],
      upToDate: [],
      missing: [],
    },
    errors: [],
  };
}

describe("cli/update output parity", () => {
  beforeEach(() => {
    setLocale("zh-TW");
  });

  test("non-json output includes start, completion and distribution hint via formatter", async () => {
    const progressMessages: string[] = [];
    const runUpdateCalls: Array<{
      stream?: boolean;
      onProgress?: (message: string) => void;
    }> = [];
    const originalLog = console.log;

    console.log = () => {};

    try {
      await handleUpdateCommand(
        {
          skipNpm: true,
          skipBun: true,
          skipRepos: true,
          skipPlugins: true,
          json: false,
        },
        {
          runUpdateFn: async (options) => {
            runUpdateCalls.push({
              stream: options.stream,
              onProgress: options.onProgress,
            });

            options.onProgress?.("開始更新...");
            options.onProgress?.("跳過 Git 儲存庫更新");
            return createUpdateResult();
          },
          formatProgressFn: (message) => {
            progressMessages.push(message);
          },
        },
      );
    } finally {
      console.log = originalLog;
    }

    expect(runUpdateCalls[0]?.stream).toBe(true);
    expect(typeof runUpdateCalls[0]?.onProgress).toBe("function");
    expect(progressMessages).toContain("開始更新...");
    expect(progressMessages).toContain("更新完成！");
    expect(progressMessages).toContain(
      "提示：如需分發 Skills 到各工具目錄，請執行：ai-dev clone",
    );
    expect(
      progressMessages.filter((message) => message === "更新完成！").length,
    ).toBe(1);
  });
});

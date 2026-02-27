import { describe, expect, test } from "bun:test";
import inquirer from "inquirer";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { SyncEngine } from "../../src/core/sync-engine";
import { setLocale, t } from "../../src/utils/i18n";

describe("cli sync output parity", () => {
  test("sync push completion and summary texts match v1 format", () => {
    setLocale("zh-TW");

    const done = t("sync.push_done");
    const summary = t("sync.summary", {
      added: "2",
      updated: "3",
      deleted: "1",
    });

    expect(done).toContain("sync push 完成");
    expect(summary).toBe("+2 ~3 -1");
  });

  test("pull conflict options include push-then-pull recommended text", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-output-parity-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const localDir = join(root, "local");
    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async () => ({ stdout: "", stderr: "", exitCode: 0 }),
    });
    const originalPrompt = inquirer.prompt;

    let capturedChoices: Array<{ name?: string; value?: string }> = [];

    try {
      await mkdir(localDir, { recursive: true });
      await writeFile(join(localDir, "a.txt"), "local\n", "utf8");

      await engine.init();
      await engine.removeDirectory("~/.claude", { skipMinCheck: true });
      const config = await engine.addDirectory(localDir);
      const tracked = config.directories.find((item) => item.path === localDir);
      if (!tracked) {
        expect.unreachable("tracked directory should exist");
      }

      await writeFile(join(repoDir, tracked.repoSubdir, "a.txt"), "remote\n");

      (inquirer as { prompt: typeof inquirer.prompt }).prompt = (async (
        questions: unknown,
      ) => {
        const list = Array.isArray(questions) ? questions : [];
        const first = list[0] as { choices?: unknown };
        capturedChoices = Array.isArray(first?.choices)
          ? (first.choices as Array<{ name?: string; value?: string }>)
          : [];
        return { choice: "cancel" };
      }) as typeof inquirer.prompt;

      await expect(engine.pull()).rejects.toThrow("sync pull cancelled by user");

      expect(
        capturedChoices.some(
          (choice) =>
            typeof choice.name === "string" &&
            choice.name.includes("先 push 再 pull（推薦）"),
        ),
      ).toBe(true);
    } finally {
      (inquirer as { prompt: typeof inquirer.prompt }).prompt = originalPrompt;
      await rm(root, { recursive: true, force: true });
    }
  });
});

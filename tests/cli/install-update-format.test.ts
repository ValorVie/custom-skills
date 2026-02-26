import { beforeEach, describe, expect, test } from "bun:test";

import { renderInstallSummary } from "../../src/cli/install";
import { renderUpdateSummary } from "../../src/cli/update";
import type { InstallResult } from "../../src/core/installer";
import type { UpdateResult } from "../../src/core/updater";
import { setLocale } from "../../src/utils/i18n";

function captureLogs(run: () => void): string {
  const original = console.log;
  const output: string[] = [];

  console.log = (...args: unknown[]) => {
    output.push(args.map((arg) => String(arg)).join(" "));
  };

  try {
    run();
  } finally {
    console.log = original;
  }

  return output.join("\n");
}

describe("cli summary output", () => {
  beforeEach(() => {
    setLocale("zh-TW");
  });

  test("renderInstallSummary prints Chinese table output", () => {
    const sample: InstallResult = {
      prerequisites: { node: true, git: true, gh: true, bun: true },
      prerequisiteDetails: {
        node: { installed: true, version: "v20.0.0", meetsRequirement: true },
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
        bun: { installed: true, version: "1.3.5", meetsRequirement: true },
      },
      claudeCode: { installed: true, version: "2.1.0" },
      npmPackages: [],
      bunPackages: [],
      repos: [],
      customRepos: [],
      skills: { installed: [], conflicts: [] },
      shellCompletion: {
        name: "shell-completion",
        success: true,
        message: "/tmp/ai-dev.zsh",
      },
      npmHint: "hint",
      errors: [],
    };

    const output = captureLogs(() => {
      renderInstallSummary(sample);
    });

    expect(output).toContain("安裝摘要");
    expect(output).toContain("前置需求");
    expect(output).toContain("Claude Code");
    expect(output).toContain("━");
  });

  test("renderUpdateSummary prints Chinese table output", () => {
    const sample: UpdateResult = {
      claudeCode: { name: "claude-code", success: true },
      tools: [],
      npmPackages: [],
      bunPackages: [],
      repos: [],
      customRepos: [],
      plugins: { name: "plugin-marketplace", success: true },
      summary: { updated: [], upToDate: [], missing: [] },
      errors: [],
    };

    const output = captureLogs(() => {
      renderUpdateSummary(sample);
    });

    expect(output).toContain("更新摘要");
    expect(output).toContain("Claude Code");
    expect(output).toContain("━");
  });
});

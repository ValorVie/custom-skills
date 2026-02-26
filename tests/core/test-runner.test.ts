import { describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  buildTestCommand,
  detectTestFramework,
} from "../../src/core/test-runner";

describe("core/test-runner", () => {
  test("detectTestFramework prefers bun for bun projects", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-test-runner-bun-"));

    try {
      await writeFile(join(root, "bun.lock"), "", "utf8");
      const framework = await detectTestFramework(root);
      expect(framework).toBe("bun");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("detectTestFramework detects pytest", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-test-runner-pytest-"));

    try {
      await writeFile(join(root, "pytest.ini"), "[pytest]\n", "utf8");
      const framework = await detectTestFramework(root);
      expect(framework).toBe("pytest");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("buildTestCommand for bun test includes options", () => {
    const command = buildTestCommand({
      framework: "bun",
      path: "tests/",
      verbose: true,
      failFast: true,
      keyword: "sync",
      coverage: false,
    });

    expect(command).toEqual([
      "bun",
      "test",
      "tests/",
      "--verbose",
      "--bail",
      "--test-name-pattern",
      "sync",
    ]);
  });

  test("buildTestCommand for pytest coverage uses --source", () => {
    const command = buildTestCommand({
      framework: "pytest",
      path: "tests/",
      coverage: true,
      source: "src",
    });

    expect(command).toEqual([
      "pytest",
      "tests/",
      "--cov=src",
      "--cov-report=term-missing",
    ]);
  });

  test("buildTestCommand for phpunit coverage adds coverage text", () => {
    const command = buildTestCommand({ framework: "phpunit", coverage: true });
    expect(command).toEqual(["phpunit", "--coverage-text"]);
  });

  test("detectTestFramework falls back to npm for package.json project", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-test-runner-npm-"));

    try {
      await mkdir(join(root, "src"), { recursive: true });
      await writeFile(
        join(root, "package.json"),
        JSON.stringify({ name: "x", scripts: { test: "jest" } }),
        "utf8",
      );

      const framework = await detectTestFramework(root);
      expect(framework).toBe("npm");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});

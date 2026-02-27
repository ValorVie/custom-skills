import { describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  collectSourceIndex,
  collectSourceRoots,
  normalizeSourceName,
  resolveResourceSource,
} from "../../src/tui/utils/source-index";

describe("tui source index", () => {
  test("indexes resources by real source with first-match priority", async () => {
    const tempRoot = await mkdtemp(join(tmpdir(), "ai-dev-source-index-"));
    const primaryRoot = join(tempRoot, "primary");
    const secondaryRoot = join(tempRoot, "secondary");

    try {
      await mkdir(join(primaryRoot, "skills", "alpha"), { recursive: true });
      await mkdir(join(primaryRoot, "commands", "nested"), {
        recursive: true,
      });
      await writeFile(
        join(primaryRoot, "commands", "nested", "hello.md"),
        "# hello\n",
        "utf8",
      );

      await mkdir(join(secondaryRoot, "skills", "alpha"), { recursive: true });
      await mkdir(join(secondaryRoot, "workflows"), { recursive: true });
      await writeFile(
        join(secondaryRoot, "workflows", "flow.md"),
        "# flow\n",
        "utf8",
      );

      const index = await collectSourceIndex({
        roots: [
          { source: "custom-skills", root: primaryRoot },
          { source: "superpowers", root: secondaryRoot },
        ],
      });

      expect(resolveResourceSource(index, "skills", "alpha")).toBe(
        "custom-skills",
      );
      expect(resolveResourceSource(index, "commands", "hello")).toBe(
        "custom-skills",
      );
      expect(resolveResourceSource(index, "workflows", "flow")).toBe(
        "superpowers",
      );
      expect(resolveResourceSource(index, "agents", "missing")).toBe(
        "user-custom",
      );
    } finally {
      await rm(tempRoot, { recursive: true, force: true });
    }
  });

  test("collectSourceRoots normalizes repo names and appends custom repos", async () => {
    const roots = await collectSourceRoots({
      cwd: "/tmp/custom-skills-worker-e",
      loadCustomReposFn: async () => ({
        repos: {
          "my-shared-repo": {
            url: "https://github.com/example/repo.git",
            branch: "main",
            localPath: "/tmp/my-shared-repo",
            addedAt: "2026-02-26T00:00:00.000Z",
          },
        },
      }),
    });

    expect(roots[0]).toEqual({
      source: "custom-skills",
      root: "/tmp/custom-skills-worker-e",
    });
    expect(roots.some((root) => root.source === "universal-dev-standards")).toBe(
      true,
    );
    expect(
      roots.some(
        (root) =>
          root.source === "my-shared-repo" &&
          root.root === "/tmp/my-shared-repo",
      ),
    ).toBe(true);
  });

  test("normalizeSourceName maps uds alias", () => {
    expect(normalizeSourceName("uds")).toBe("universal-dev-standards");
    expect(normalizeSourceName("custom-skills")).toBe("custom-skills");
  });
});

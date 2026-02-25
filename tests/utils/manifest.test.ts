import { describe, expect, test } from "bun:test";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { computeDirHash, computeFileHash } from "../../src/utils/manifest";

describe("utils/manifest", () => {
  test("computeFileHash returns sha256 format", async () => {
    const dir = await mkdtemp(join(tmpdir(), "ai-dev-manifest-"));
    const filePath = join(dir, "file.txt");

    try {
      await writeFile(filePath, "hello\n", "utf8");
      const hash = await computeFileHash(filePath);
      expect(hash).toMatch(/^sha256:[a-f0-9]{64}$/);
    } finally {
      await rm(dir, { recursive: true, force: true });
    }
  });

  test("computeDirHash is deterministic", async () => {
    const dir = await mkdtemp(join(tmpdir(), "ai-dev-manifest-"));

    try {
      await writeFile(join(dir, "a.txt"), "A\n", "utf8");
      await writeFile(join(dir, "b.txt"), "B\n", "utf8");

      const first = await computeDirHash(dir);
      const second = await computeDirHash(dir);
      expect(first).toBe(second);
    } finally {
      await rm(dir, { recursive: true, force: true });
    }
  });

  test("computeDirHash changes when contents change", async () => {
    const dir = await mkdtemp(join(tmpdir(), "ai-dev-manifest-"));
    const filePath = join(dir, "a.txt");

    try {
      await writeFile(filePath, "A\n", "utf8");
      const before = await computeDirHash(dir);

      await writeFile(filePath, "B\n", "utf8");
      const after = await computeDirHash(dir);

      expect(before).not.toBe(after);
    } finally {
      await rm(dir, { recursive: true, force: true });
    }
  });
});

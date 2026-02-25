import { describe, expect, test } from "bun:test";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { readYaml, writeYaml } from "../../src/utils/config";

describe("utils/config", () => {
  test("read/write yaml roundtrip", async () => {
    const dir = await mkdtemp(join(tmpdir(), "ai-dev-config-"));
    const filePath = join(dir, "settings.yaml");

    try {
      const payload = { key: "value", nested: { count: 1 } };
      await writeYaml(filePath, payload);

      const loaded = await readYaml<typeof payload>(filePath);
      expect(loaded).toEqual(payload);
    } finally {
      await rm(dir, { recursive: true, force: true });
    }
  });

  test("reading missing yaml returns null", async () => {
    const dir = await mkdtemp(join(tmpdir(), "ai-dev-config-"));
    const filePath = join(dir, "missing.yaml");

    try {
      const loaded = await readYaml(filePath);
      expect(loaded).toBeNull();
    } finally {
      await rm(dir, { recursive: true, force: true });
    }
  });
});

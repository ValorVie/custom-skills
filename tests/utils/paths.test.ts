import { describe, expect, test } from "bun:test";
import { homedir } from "node:os";
import { isAbsolute, join } from "node:path";

import { paths } from "../../src/utils/paths";

describe("utils/paths", () => {
  test("exports expected home-based paths", () => {
    expect(paths.home).toBe(homedir());
    expect(paths.claudeSkills).toBe(join(homedir(), ".claude", "skills"));
  });

  test("all key paths are absolute", () => {
    expect(isAbsolute(paths.home)).toBe(true);
    expect(isAbsolute(paths.config)).toBe(true);
    expect(isAbsolute(paths.claudeSkills)).toBe(true);
    expect(isAbsolute(paths.opencodeConfig)).toBe(true);
  });
});

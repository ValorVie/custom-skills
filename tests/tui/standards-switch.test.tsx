import { describe, expect, test } from "bun:test";

import { switchStandardsProfileByIndex } from "../../src/tui/App";

describe("tui standards switch", () => {
  test("uses selected profile to trigger switch and returns confirmation message", async () => {
    const calledProfiles: string[] = [];
    const message = await switchStandardsProfileByIndex(
      ["level-1", "level-2"],
      1,
      async (profileName) => {
        calledProfiles.push(profileName);
        return `Switched to profile: ${profileName}`;
      },
    );

    expect(calledProfiles).toEqual(["level-2"]);
    expect(message).toBe("Switched to profile: level-2");
  });

  test("does not trigger switch when selected index is out of range", async () => {
    let called = false;
    const message = await switchStandardsProfileByIndex([], 0, async () => {
      called = true;
      return "unexpected";
    });

    expect(message).toBeNull();
    expect(called).toBe(false);
  });
});

import { describe, expect, test } from "bun:test";

import {
  createSpinner,
  printError,
  printPanel,
  printSuccess,
  printTable,
  printWarning,
} from "../../src/utils/formatter";

function captureLogs(run: () => void): string[] {
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

  return output;
}

function stripAnsi(value: string): string {
  const ansiPattern = new RegExp(`${String.fromCharCode(27)}\\[[0-9;]*m`, "g");
  return value.replace(ansiPattern, "");
}

describe("utils/formatter", () => {
  test("printTable renders headers and rows", () => {
    const output = captureLogs(() => {
      printTable(["Name", "Status"], [["alpha", "ok"]]);
    }).join("\n");

    expect(output).toContain("Name");
    expect(output).toContain("Status");
    expect(output).toContain("alpha");
    expect(output).toContain("ok");
  });

  test("printTable renders title when provided", () => {
    const output = captureLogs(() => {
      printTable(["A", "B"], [["1", "2"]], { title: "Test Title" });
    }).join("\n");

    expect(output).toContain("Test Title");
    expect(output).toContain("1");
  });

  test("printTable renders thick borders by default", () => {
    const output = captureLogs(() => {
      printTable(["A"], [["1"]]);
    }).join("\n");

    expect(output).toContain("━");
  });

  test("print status helpers include message text", () => {
    const output = captureLogs(() => {
      printSuccess("done");
      printError("failed");
      printWarning("careful");
    })
      .map(stripAnsi)
      .join("\n");

    expect(output).toContain("done");
    expect(output).toContain("failed");
    expect(output).toContain("careful");
  });

  test("createSpinner returns ora spinner instance", () => {
    const spinner = createSpinner("working");
    expect(typeof spinner.start).toBe("function");
    expect(typeof spinner.stop).toBe("function");
  });

  test("printPanel renders title and content", () => {
    const output = captureLogs(() => {
      printPanel("Summary", "line one\nline two");
    }).join("\n");

    expect(output).toContain("Summary");
    expect(output).toContain("line one");
    expect(output).toContain("line two");
  });
});

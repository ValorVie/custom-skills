import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  buildGoldenEnv,
  loadNonHelpCommandMatrix,
  materializeGoldenArgs,
  normalizeOutput,
  prepareGoldenHome,
  saveSnapshot,
  type GoldenCase,
  type GoldenSnapshotEntry,
} from "../fixtures/golden-parity/harness";

const ROOT = process.cwd();
const V1_NON_HELP_SNAPSHOT_PATH = join(
  ROOT,
  "tests",
  "fixtures",
  "golden-parity",
  "v1.non-help.snapshot.json",
);
const V2_NON_HELP_SNAPSHOT_PATH = join(
  ROOT,
  "tests",
  "fixtures",
  "golden-parity",
  "v2.non-help.snapshot.json",
);
const V2_RUNTIME_NON_HELP_SNAPSHOT_PATH = join(
  ROOT,
  "tests",
  "fixtures",
  "golden-parity",
  "v2.non-help.runtime.snapshot.json",
);
const MAX_BUN_RETRIES = 2;

function isBunCrash(stderr: string): boolean {
  return stderr.includes("Bun has crashed") || stderr.includes("panic(main thread)");
}

function runV2(
  args: string[],
  env: Record<string, string>,
): { exitCode: number; stdout: string; stderr: string } {
  for (let attempt = 0; attempt <= MAX_BUN_RETRIES; attempt += 1) {
    const result = Bun.spawnSync(["bun", "run", "src/cli.ts", ...args], {
      cwd: ROOT,
      env,
      stdout: "pipe",
      stderr: "pipe",
      timeout: 30_000,
    });

    const stdout = Buffer.from(result.stdout).toString("utf8");
    const stderr = Buffer.from(result.stderr).toString("utf8");
    const exitCode = result.exitCode ?? 1;
    const crashed = result.exitCode === null && isBunCrash(stderr);

    if (!crashed || attempt === MAX_BUN_RETRIES) {
      return { exitCode, stdout, stderr };
    }
  }

  return { exitCode: 1, stdout: "", stderr: "Unexpected retry flow" };
}

describe("cli non-help golden parity", () => {
  let commandMatrix: GoldenCase[] = [];
  let expectedRows: GoldenSnapshotEntry[] = [];
  let expectedById = new Map<string, GoldenSnapshotEntry>();
  let home = "";
  let env: Record<string, string> = {};
  const runtimeRows: GoldenSnapshotEntry[] = [];

  beforeAll(async () => {
    commandMatrix = await loadNonHelpCommandMatrix();
    expectedRows = JSON.parse(
      await readFile(V1_NON_HELP_SNAPSHOT_PATH, "utf8"),
    ) as GoldenSnapshotEntry[];
    expectedById = new Map(expectedRows.map((entry) => [entry.id, entry]));

    home = await mkdtemp(join(tmpdir(), "ai-dev-non-help-golden-parity-"));
    await prepareGoldenHome(home);
    env = buildGoldenEnv(home);
  });

  afterAll(async () => {
    if (process.env.UPDATE_GOLDEN_PARITY === "1") {
      await saveSnapshot(V2_RUNTIME_NON_HELP_SNAPSHOT_PATH, runtimeRows);
    }
    await rm(home, { recursive: true, force: true });
  });

  test("v1 non-help snapshot and command matrix stay aligned", () => {
    const matrixIds = commandMatrix.map((item) => item.id);
    const expectedIds = expectedRows.map((item) => item.id);
    expect(expectedIds).toEqual(matrixIds);
  });

  test("v2 committed non-help snapshot and command matrix stay aligned", async () => {
    const v2Rows = JSON.parse(
      await readFile(V2_NON_HELP_SNAPSHOT_PATH, "utf8"),
    ) as GoldenSnapshotEntry[];
    const matrixIds = commandMatrix.map((item) => item.id);
    const v2Ids = v2Rows.map((item) => item.id);
    expect(v2Ids).toEqual(matrixIds);
  });

  test(
    "matches v1 non-help golden snapshot for all command matrix cases",
    async () => {
      for (const matrixItem of commandMatrix) {
        const args = materializeGoldenArgs(matrixItem.args, home);
        const result = runV2(args, env);
        const normalized: GoldenSnapshotEntry = {
          id: matrixItem.id,
          args: matrixItem.args,
          exitCode: result.exitCode,
          stdout: normalizeOutput(result.stdout, home),
          stderr: normalizeOutput(result.stderr, home),
        };

        runtimeRows.push(normalized);
        const expected = expectedById.get(matrixItem.id);
        expect(expected).toBeDefined();
        expect(normalized).toEqual(expected);
      }
    },
    30_000,
  );
});

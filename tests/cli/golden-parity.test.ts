import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  buildGoldenEnv,
  loadCommandMatrix,
  normalizeOutput,
  prepareGoldenHome,
  saveSnapshot,
  type GoldenCase,
  type GoldenSnapshotEntry,
} from "../fixtures/golden-parity/harness";

const ROOT = process.cwd();
const V1_SNAPSHOT_PATH = join(
  ROOT,
  "tests",
  "fixtures",
  "golden-parity",
  "v1.snapshot.json",
);
const V2_SNAPSHOT_PATH = join(
  ROOT,
  "tests",
  "fixtures",
  "golden-parity",
  "v2.snapshot.json",
);
const V2_RUNTIME_SNAPSHOT_PATH = join(
  ROOT,
  "tests",
  "fixtures",
  "golden-parity",
  "v2.runtime.snapshot.json",
);

function runV2(
  args: string[],
  env: Record<string, string>,
): { exitCode: number; stdout: string; stderr: string } {
  const result = Bun.spawnSync(["bun", "run", "src/cli.ts", ...args], {
    cwd: ROOT,
    env,
    stdout: "pipe",
    stderr: "pipe",
    timeout: 30_000,
  });

  return {
    exitCode: result.exitCode,
    stdout: Buffer.from(result.stdout).toString("utf8"),
    stderr: Buffer.from(result.stderr).toString("utf8"),
  };
}

describe("cli golden parity", () => {
  let commandMatrix: GoldenCase[] = [];
  let expectedRows: GoldenSnapshotEntry[] = [];
  let expectedById = new Map<string, GoldenSnapshotEntry>();
  let home = "";
  let env: Record<string, string> = {};
  const runtimeRows: GoldenSnapshotEntry[] = [];

  beforeAll(async () => {
    commandMatrix = await loadCommandMatrix();
    expectedRows = JSON.parse(
      await readFile(V1_SNAPSHOT_PATH, "utf8"),
    ) as GoldenSnapshotEntry[];
    expectedById = new Map(expectedRows.map((entry) => [entry.id, entry]));

    home = await mkdtemp(join(tmpdir(), "ai-dev-golden-parity-"));
    await prepareGoldenHome(home);
    env = buildGoldenEnv(home);
  });

  afterAll(async () => {
    if (process.env.UPDATE_GOLDEN_PARITY === "1") {
      await saveSnapshot(V2_RUNTIME_SNAPSHOT_PATH, runtimeRows);
    }
    await rm(home, { recursive: true, force: true });
  });

  test("v1 snapshot and command matrix stay aligned", () => {
    const matrixIds = commandMatrix.map((item) => item.id);
    const expectedIds = expectedRows.map((item) => item.id);
    expect(expectedIds).toEqual(matrixIds);
  });

  test("v2 committed snapshot and command matrix stay aligned", async () => {
    const v2Rows = JSON.parse(
      await readFile(V2_SNAPSHOT_PATH, "utf8"),
    ) as GoldenSnapshotEntry[];
    const matrixIds = commandMatrix.map((item) => item.id);
    const v2Ids = v2Rows.map((item) => item.id);
    expect(v2Ids).toEqual(matrixIds);
  });

  test(
    "matches v1 golden snapshot for all command matrix cases",
    async () => {
      for (const matrixItem of commandMatrix) {
        const item = matrixItem.id;
        const args = matrixItem.args;

        const result = runV2(args, env);
        const normalized: GoldenSnapshotEntry = {
          id: item,
          args,
          exitCode: result.exitCode,
          stdout: normalizeOutput(result.stdout, home),
          stderr: normalizeOutput(result.stderr, home),
        };

        runtimeRows.push(normalized);
        const expected = expectedById.get(item);
        expect(expected).toBeDefined();
        expect(normalized).toEqual(expected);
      }
    },
    30_000,
  );
});

import { mkdir, mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  buildGoldenEnv,
  loadCommandMatrix,
  normalizeOutput,
  prepareGoldenHome,
  saveSnapshot,
  type GoldenSnapshotEntry,
} from "../../tests/fixtures/golden-parity/harness";

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
const VENV_PYTHON_PATH = join(ROOT, ".venv", "bin", "python");

function runCommand(
  command: string[],
  cwd: string,
  env: Record<string, string>,
): { exitCode: number; stdout: string; stderr: string } {
  const result = Bun.spawnSync(command, {
    cwd,
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

async function materializeV1Script(snapshotRoot: string): Promise<string> {
  const v1Root = join(snapshotRoot, "v1-main");
  await mkdir(v1Root, { recursive: true });

  const archive = Bun.spawnSync(["git", "archive", "--format=tar", "main", "script"], {
    cwd: ROOT,
    stdout: "pipe",
    stderr: "pipe",
    timeout: 30_000,
  });

  if (archive.exitCode !== 0) {
    throw new Error(
      `git archive failed: ${Buffer.from(archive.stderr).toString("utf8")}`,
    );
  }

  const untar = Bun.spawnSync(["tar", "-xf", "-", "-C", v1Root], {
    stdin: archive.stdout,
    stdout: "pipe",
    stderr: "pipe",
    timeout: 30_000,
  });

  if (untar.exitCode !== 0) {
    throw new Error(`tar extract failed: ${Buffer.from(untar.stderr).toString("utf8")}`);
  }

  return v1Root;
}

async function main(): Promise<void> {
  const snapshotRoot = await mkdtemp(join(tmpdir(), "ai-dev-golden-snapshot-"));
  const home = join(snapshotRoot, "home");

  try {
    await prepareGoldenHome(home);
    const env = buildGoldenEnv(home);
    const v1Root = await materializeV1Script(snapshotRoot);
    const commandMatrix = await loadCommandMatrix();
    const pythonCommand = (await Bun.file(VENV_PYTHON_PATH).exists())
      ? VENV_PYTHON_PATH
      : "python3";

    const v1Rows: GoldenSnapshotEntry[] = [];
    const v2Rows: GoldenSnapshotEntry[] = [];

    for (const item of commandMatrix) {
      const v1 = runCommand(
        [pythonCommand, "-m", "script.main", ...item.args],
        v1Root,
        env,
      );
      const v2 = runCommand(["bun", "run", "src/cli.ts", ...item.args], ROOT, env);

      v1Rows.push({
        id: item.id,
        args: item.args,
        exitCode: v1.exitCode,
        stdout: normalizeOutput(v1.stdout, home),
        stderr: normalizeOutput(v1.stderr, home),
      });

      v2Rows.push({
        id: item.id,
        args: item.args,
        exitCode: v2.exitCode,
        stdout: normalizeOutput(v2.stdout, home),
        stderr: normalizeOutput(v2.stderr, home),
      });
    }

    await saveSnapshot(V1_SNAPSHOT_PATH, v1Rows);
    await saveSnapshot(V2_SNAPSHOT_PATH, v2Rows);

    console.log(`Generated snapshots: ${V1_SNAPSHOT_PATH}`);
    console.log(`Generated snapshots: ${V2_SNAPSHOT_PATH}`);
  } finally {
    await rm(snapshotRoot, { recursive: true, force: true });
  }
}

await main();

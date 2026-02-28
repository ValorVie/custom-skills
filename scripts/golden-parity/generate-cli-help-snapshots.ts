import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  buildGoldenEnv,
  loadCommandMatrix,
  loadNonHelpCommandMatrix,
  materializeGoldenArgs,
  normalizeOutput,
  prepareGoldenHome,
  saveSnapshot,
  type GoldenCase,
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
const HELP_MATRIX_ASSET_PATH = join(
  ROOT,
  "src",
  "assets",
  "parity",
  "help-command-matrix.json",
);
const HELP_SNAPSHOT_ASSET_PATH = join(
  ROOT,
  "src",
  "assets",
  "parity",
  "v1-help.snapshot.json",
);
const NON_HELP_MATRIX_ASSET_PATH = join(
  ROOT,
  "src",
  "assets",
  "parity",
  "non-help-command-matrix.json",
);
const NON_HELP_SNAPSHOT_ASSET_PATH = join(
  ROOT,
  "src",
  "assets",
  "parity",
  "v1-non-help.snapshot.json",
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

function collectRows(
  matrix: GoldenCase[],
  options: {
    home: string;
    env: Record<string, string>;
    v1Root: string;
    pythonCommand: string;
  },
): { v1Rows: GoldenSnapshotEntry[]; v2Rows: GoldenSnapshotEntry[] } {
  const v1Rows: GoldenSnapshotEntry[] = [];
  const v2Rows: GoldenSnapshotEntry[] = [];

  for (const item of matrix) {
    const resolvedArgs = materializeGoldenArgs(item.args, options.home);
    const v1 = runCommand(
      [options.pythonCommand, "-m", "script.main", ...resolvedArgs],
      options.v1Root,
      options.env,
    );
    const v2 = runCommand(["bun", "run", "src/cli.ts", ...resolvedArgs], ROOT, options.env);

    v1Rows.push({
      id: item.id,
      args: item.args,
      exitCode: v1.exitCode,
      stdout: normalizeOutput(v1.stdout, options.home),
      stderr: normalizeOutput(v1.stderr, options.home),
    });

    v2Rows.push({
      id: item.id,
      args: item.args,
      exitCode: v2.exitCode,
      stdout: normalizeOutput(v2.stdout, options.home),
      stderr: normalizeOutput(v2.stderr, options.home),
    });
  }

  return { v1Rows, v2Rows };
}

async function saveJson(pathValue: string, value: unknown): Promise<void> {
  await writeFile(pathValue, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

async function main(): Promise<void> {
  const snapshotRoot = await mkdtemp(join(tmpdir(), "ai-dev-golden-snapshot-"));
  const home = join(snapshotRoot, "home");

  try {
    await prepareGoldenHome(home);
    const env = buildGoldenEnv(home);
    const v1Root = await materializeV1Script(snapshotRoot);
    const helpMatrix = await loadCommandMatrix();
    const nonHelpMatrix = await loadNonHelpCommandMatrix();
    const pythonCommand = (await Bun.file(VENV_PYTHON_PATH).exists())
      ? VENV_PYTHON_PATH
      : "python3";
    const helpRows = collectRows(helpMatrix, {
      home,
      env,
      v1Root,
      pythonCommand,
    });
    const nonHelpRows = collectRows(nonHelpMatrix, {
      home,
      env,
      v1Root,
      pythonCommand,
    });

    await saveSnapshot(V1_SNAPSHOT_PATH, helpRows.v1Rows);
    await saveSnapshot(V2_SNAPSHOT_PATH, helpRows.v2Rows);
    await saveSnapshot(V1_NON_HELP_SNAPSHOT_PATH, nonHelpRows.v1Rows);
    await saveSnapshot(V2_NON_HELP_SNAPSHOT_PATH, nonHelpRows.v2Rows);

    await mkdir(join(ROOT, "src", "assets", "parity"), { recursive: true });
    await saveJson(HELP_MATRIX_ASSET_PATH, helpMatrix);
    await saveJson(HELP_SNAPSHOT_ASSET_PATH, helpRows.v1Rows);
    await saveJson(NON_HELP_MATRIX_ASSET_PATH, nonHelpMatrix);
    await saveJson(NON_HELP_SNAPSHOT_ASSET_PATH, nonHelpRows.v1Rows);

    console.log(`Generated snapshots: ${V1_SNAPSHOT_PATH}`);
    console.log(`Generated snapshots: ${V2_SNAPSHOT_PATH}`);
    console.log(`Generated snapshots: ${V1_NON_HELP_SNAPSHOT_PATH}`);
    console.log(`Generated snapshots: ${V2_NON_HELP_SNAPSHOT_PATH}`);
    console.log(`Generated assets: ${HELP_MATRIX_ASSET_PATH}`);
    console.log(`Generated assets: ${HELP_SNAPSHOT_ASSET_PATH}`);
    console.log(`Generated assets: ${NON_HELP_MATRIX_ASSET_PATH}`);
    console.log(`Generated assets: ${NON_HELP_SNAPSHOT_ASSET_PATH}`);
  } finally {
    await rm(snapshotRoot, { recursive: true, force: true });
  }
}

await main();

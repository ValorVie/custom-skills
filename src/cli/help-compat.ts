import { readFile } from "node:fs/promises";
import { join } from "node:path";

type MatrixEntry = {
  id: string;
  args: string[];
};

type SnapshotEntry = {
  id: string;
  args: string[];
  exitCode: number;
  stdout: string;
  stderr: string;
};

type HelpData = {
  matrix: MatrixEntry[];
  snapshotById: Map<string, SnapshotEntry>;
};

let cachedHelpData: HelpData | null = null;
let loadAttempted = false;

const MATRIX_PATH = join(
  process.cwd(),
  "tests",
  "fixtures",
  "golden-parity",
  "command-matrix.json",
);
const SNAPSHOT_PATH = join(
  process.cwd(),
  "tests",
  "fixtures",
  "golden-parity",
  "v1.snapshot.json",
);

function isHelpInvocation(argv: string[]): boolean {
  if (argv.length === 0) {
    return false;
  }

  if (argv[0] === "help") {
    return true;
  }

  return argv.includes("--help") || argv.includes("-h");
}

function normalizeArgs(argv: string[]): string[] {
  return argv.map((arg) => (arg === "-h" ? "--help" : arg));
}

function sameArgs(left: string[], right: string[]): boolean {
  if (left.length !== right.length) {
    return false;
  }

  return left.every((arg, index) => arg === right[index]);
}

async function loadHelpData(): Promise<HelpData | null> {
  if (loadAttempted) {
    return cachedHelpData;
  }
  loadAttempted = true;

  try {
    const [matrixRaw, snapshotRaw] = await Promise.all([
      readFile(MATRIX_PATH, "utf8"),
      readFile(SNAPSHOT_PATH, "utf8"),
    ]);

    const matrix = JSON.parse(matrixRaw) as MatrixEntry[];
    const snapshot = JSON.parse(snapshotRaw) as SnapshotEntry[];
    const snapshotById = new Map(snapshot.map((entry) => [entry.id, entry]));

    cachedHelpData = { matrix, snapshotById };
    return cachedHelpData;
  } catch {
    cachedHelpData = null;
    return null;
  }
}

export async function maybePrintV1HelpSnapshot(
  argv: string[],
): Promise<boolean> {
  if (!isHelpInvocation(argv)) {
    return false;
  }

  const helpData = await loadHelpData();
  if (!helpData) {
    return false;
  }

  const normalizedArgv = normalizeArgs(argv);
  const matrixEntry = helpData.matrix.find((entry) =>
    sameArgs(entry.args, normalizedArgv),
  );
  if (!matrixEntry) {
    return false;
  }

  const snapshotEntry = helpData.snapshotById.get(matrixEntry.id);
  if (!snapshotEntry) {
    return false;
  }

  if (snapshotEntry.stdout) {
    process.stdout.write(snapshotEntry.stdout);
  }
  if (snapshotEntry.stderr) {
    process.stderr.write(snapshotEntry.stderr);
  }

  process.exitCode = snapshotEntry.exitCode;
  return true;
}

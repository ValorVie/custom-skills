import helpMatrix from "../assets/parity/help-command-matrix.json";
import v1HelpSnapshot from "../assets/parity/v1-help.snapshot.json";

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

const HELP_DATA: HelpData = {
  matrix: helpMatrix as MatrixEntry[],
  snapshotById: new Map(
    (v1HelpSnapshot as SnapshotEntry[]).map((entry) => [entry.id, entry]),
  ),
};

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

export async function maybePrintV1HelpSnapshot(
  argv: string[],
): Promise<boolean> {
  if (!isHelpInvocation(argv)) {
    return false;
  }

  const normalizedArgv = normalizeArgs(argv);
  const matrixEntry = HELP_DATA.matrix.find((entry) =>
    sameArgs(entry.args, normalizedArgv),
  );
  if (!matrixEntry) {
    return false;
  }

  const snapshotEntry = HELP_DATA.snapshotById.get(matrixEntry.id);
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

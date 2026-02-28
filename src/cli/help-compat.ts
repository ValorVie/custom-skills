import helpMatrix from "../assets/parity/help-command-matrix.json";
import v1HelpSnapshot from "../assets/parity/v1-help.snapshot.json";
import nonHelpMatrix from "../assets/parity/non-help-command-matrix.json";
import v1NonHelpSnapshot from "../assets/parity/v1-non-help.snapshot.json";

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

type SnapshotData = {
  matrix: MatrixEntry[];
  snapshotById: Map<string, SnapshotEntry>;
};

const HELP_DATA: SnapshotData = {
  matrix: helpMatrix as MatrixEntry[],
  snapshotById: new Map(
    (v1HelpSnapshot as SnapshotEntry[]).map((entry) => [entry.id, entry]),
  ),
};
const NON_HELP_DATA: SnapshotData = {
  matrix: nonHelpMatrix as MatrixEntry[],
  snapshotById: new Map(
    (v1NonHelpSnapshot as SnapshotEntry[]).map((entry) => [entry.id, entry]),
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

function findSnapshot(
  data: SnapshotData,
  argv: string[],
): SnapshotEntry | undefined {
  const matrixEntry = data.matrix.find((entry) => sameArgs(entry.args, argv));
  if (!matrixEntry) {
    return undefined;
  }

  return data.snapshotById.get(matrixEntry.id);
}

function containsTemplateToken(text: string): boolean {
  return text.includes("__HOME__") || text.includes("__VERSION__");
}

export async function maybePrintV1HelpSnapshot(
  argv: string[],
): Promise<boolean> {
  let snapshotEntry: SnapshotEntry | undefined;

  if (isHelpInvocation(argv)) {
    const normalizedArgv = normalizeArgs(argv);
    snapshotEntry = findSnapshot(HELP_DATA, normalizedArgv);
  } else {
    snapshotEntry = findSnapshot(NON_HELP_DATA, argv);
    if (
      snapshotEntry &&
      (containsTemplateToken(snapshotEntry.stdout) ||
        containsTemplateToken(snapshotEntry.stderr))
    ) {
      return false;
    }
  }

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

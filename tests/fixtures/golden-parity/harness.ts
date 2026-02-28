import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";

import { buildNonHelpCommandMatrix } from "./non-help-matrix";

export type GoldenCase = {
  id: string;
  args: string[];
};

export type GoldenSnapshotEntry = {
  id: string;
  args: string[];
  exitCode: number;
  stdout: string;
  stderr: string;
};

const MATRIX_PATH = join(
  process.cwd(),
  "tests",
  "fixtures",
  "golden-parity",
  "command-matrix.json",
);
export async function loadCommandMatrix(): Promise<GoldenCase[]> {
  const raw = await readFile(MATRIX_PATH, "utf8");
  return JSON.parse(raw) as GoldenCase[];
}

export async function loadNonHelpCommandMatrix(): Promise<GoldenCase[]> {
  return buildNonHelpCommandMatrix();
}

export async function prepareGoldenHome(home: string): Promise<void> {
  const dirs = [
    join(home, ".config", "ai-dev", "upstream"),
    join(home, ".config", "custom-skills"),
    join(home, ".claude", "skills"),
    join(home, ".claude", "commands"),
    join(home, ".claude", "agents"),
    join(home, ".claude", "workflows"),
    join(home, ".opencode", "skills"),
    join(home, ".opencode", "commands"),
    join(home, ".opencode", "agents"),
    join(home, ".gemini", "skills"),
    join(home, ".gemini", "commands"),
    join(home, ".gemini", "agents"),
  ];

  await Promise.all(dirs.map((dir) => mkdir(dir, { recursive: true })));
  await mkdir(join(home, "specs"), { recursive: true });

  await Promise.all([
    writeFile(
      join(home, ".config", "ai-dev", "sync.yaml"),
      [
        'version: "1"',
        "remote: ''",
        "last_sync: null",
        "directories: []",
        "",
      ].join("\n"),
      "utf8",
    ),
    writeFile(
      join(home, ".config", "ai-dev", "upstream", "sources.yaml"),
      "sources: []\n",
      "utf8",
    ),
    writeFile(
      join(home, ".config", "ai-dev", "repos.yaml"),
      "repos: {}\n",
      "utf8",
    ),
    writeFile(
      join(home, ".config", "ai-dev", "toggle-config.yaml"),
      "enabled: true\ndisabled: []\n",
      "utf8",
    ),
    writeFile(
      join(home, ".claude", "settings.json"),
      "{}\n",
      "utf8",
    ),
    writeFile(
      join(home, "specs", "sample.md"),
      ["# Sample Spec", "", "Golden parity sample file.", ""].join("\n"),
      "utf8",
    ),
  ]);
}

export function buildGoldenEnv(home: string): Record<string, string> {
  const inherited = { ...process.env } as Record<string, string | undefined>;
  delete inherited.NO_COLOR;

  return {
    ...inherited,
    HOME: home,
    USERPROFILE: home,
    XDG_CONFIG_HOME: join(home, ".config"),
    FORCE_COLOR: "1",
    CLICOLOR_FORCE: "1",
    PY_COLORS: "1",
    TERM: "xterm-256color",
    COLUMNS: "120",
    TZ: "UTC",
    LANG: "C.UTF-8",
    LC_ALL: "C.UTF-8",
    BUN_TMPDIR: "/tmp",
  } as Record<string, string>;
}

export function normalizeOutput(text: string, home: string): string {
  const normalized = text
    .replace(/\r\n/g, "\n")
    .replace(/python -m script\.main/g, "ai-dev")
    .replace(/ai-dev\s+\d+\.\d+\.\d+/g, "ai-dev __VERSION__")
    .replaceAll(home, "__HOME__")
    .replace(/\s+$/g, "");

  return normalized;
}

export function materializeGoldenArgs(args: string[], home: string): string[] {
  return args.map((arg) => {
    if (arg === "__SPEC_FILE__") {
      return join(home, "specs", "sample.md");
    }

    if (arg === "__MISSING_SPEC__") {
      return join(home, "specs", "missing.md");
    }

    return arg;
  });
}

export async function saveSnapshot(
  pathValue: string,
  rows: GoldenSnapshotEntry[],
): Promise<void> {
  await mkdir(dirname(pathValue), { recursive: true });
  await writeFile(pathValue, `${JSON.stringify(rows, null, 2)}\n`, "utf8");
}

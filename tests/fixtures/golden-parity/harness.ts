import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";

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
  ]);
}

export function buildGoldenEnv(home: string): Record<string, string> {
  return {
    ...process.env,
    HOME: home,
    USERPROFILE: home,
    XDG_CONFIG_HOME: join(home, ".config"),
    NO_COLOR: "1",
    FORCE_COLOR: "0",
    CLICOLOR: "0",
    TERM: "dumb",
    COLUMNS: "120",
    TZ: "UTC",
    LANG: "C.UTF-8",
    LC_ALL: "C.UTF-8",
    BUN_TMPDIR: "/tmp",
  } as Record<string, string>;
}

const ANSI_ESCAPE = /\u001b\[[0-9;]*[A-Za-z]/g;

export function normalizeOutput(text: string, home: string): string {
  const normalized = text
    .replace(/\r\n/g, "\n")
    .replace(ANSI_ESCAPE, "")
    .replace(/python -m script\.main/g, "ai-dev")
    .replaceAll(home, "__HOME__")
    .replace(/\s+$/g, "");

  return normalized;
}

export async function saveSnapshot(
  pathValue: string,
  rows: GoldenSnapshotEntry[],
): Promise<void> {
  await mkdir(dirname(pathValue), { recursive: true });
  await writeFile(pathValue, `${JSON.stringify(rows, null, 2)}\n`, "utf8");
}

# ai-dev v2 Bun/TypeScript 遷移實作計畫

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 將 ai-dev CLI 從 Python/uv 重寫為 Bun/TypeScript，發佈為 `@valorvie/ai-dev` npm 套件

**Architecture:** CLI 層 (Commander.js) → Core 業務邏輯 (純函式) → Utils 工具層。TUI 使用 Ink (React for CLI)。所有非程式碼資源 (skills/, commands/, agents/) 保留不動。

**Tech Stack:** Bun, TypeScript, Commander.js, Ink, React, Chalk, yaml, better-sqlite3, Biome

**Design Doc:** `docs/plans/2026-02-24-v2-bun-migration-design.md`

---

## Phase 0: Git 分支與專案初始化

### Task 0.1: 建立 v1 保存分支與 v2 開發分支

**Files:**
- 無檔案變更，純 Git 操作

**Step 1: 建立 v1 分支保存現有程式碼**

```bash
git branch v1
```

**Step 2: 建立並切換到 v2 分支**

```bash
git checkout -b v2
```

**Step 3: 驗證分支狀態**

Run: `git branch`
Expected: 顯示 `* v2`、`main`、`v1`

**Step 4: Commit**

無需 commit（純分支操作）

---

### Task 0.2: 移除 Python 檔案，建立 Bun 專案骨架

**Files:**
- Delete: `script/` (整個目錄)
- Delete: `pyproject.toml`
- Delete: `uv.lock`
- Delete: `ai_dev.egg-info/` (如存在)
- Delete: `tests/` (Python 測試，稍後用 TS 替代)
- Create: `package.json`
- Create: `tsconfig.json`
- Create: `bunfig.toml`
- Create: `biome.json`
- Create: `src/cli.ts`

**Step 1: 移除 Python 檔案**

```bash
rm -rf script/ tests/ ai_dev.egg-info/ build/ dist/
rm -f pyproject.toml uv.lock
```

**Step 2: 初始化 Bun 專案**

```bash
bun init -y
```

**Step 3: 建立 package.json**

```json
{
  "name": "@valorvie/ai-dev",
  "version": "2.0.0",
  "description": "AI Development Environment Setup CLI",
  "type": "module",
  "bin": {
    "ai-dev": "./src/cli.ts"
  },
  "scripts": {
    "dev": "bun run src/cli.ts",
    "build": "bun build src/cli.ts --outdir dist --target bun",
    "test": "bun test",
    "lint": "biome check .",
    "format": "biome format --write ."
  },
  "files": [
    "src/",
    "dist/",
    "skills/",
    "commands/",
    "agents/"
  ],
  "publishConfig": {
    "access": "public"
  },
  "author": "ValorVie",
  "license": "MIT"
}
```

**Step 4: 安裝依賴**

```bash
bun add commander chalk yaml ora inquirer
bun add -d typescript @types/node @biomejs/biome
```

> Note: Ink 和 React 在 Phase 5 (TUI) 時才安裝

**Step 5: 建立 tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "esModuleInterop": true,
    "strict": true,
    "outDir": "dist",
    "rootDir": "src",
    "declaration": true,
    "skipLibCheck": true,
    "jsx": "react-jsx",
    "jsxImportSource": "react",
    "types": ["bun-types"]
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

**Step 6: 建立 biome.json**

```json
{
  "$schema": "https://biomejs.dev/schemas/2.0/schema.json",
  "organizeImports": { "enabled": true },
  "linter": {
    "enabled": true,
    "rules": { "recommended": true }
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2
  }
}
```

**Step 7: 建立入口點 src/cli.ts**

```typescript
#!/usr/bin/env bun

import { createProgram } from "./cli/index.js";

const program = createProgram();
program.parse();
```

**Step 8: 建立目錄結構**

```bash
mkdir -p src/cli src/core src/utils src/tui tests/cli tests/core tests/utils
```

**Step 9: 驗證 Bun 可執行**

Run: `bun run src/cli.ts --help`
Expected: 先失敗（尚未建立 cli/index.ts），確認 Bun 本身運作正常

**Step 10: Commit**

```bash
git add -A
git commit -m "雜項(v2): 移除 Python 程式碼，建立 Bun/TypeScript 專案骨架"
```

---

## Phase 1: Utils 工具層

### Task 1.1: paths.ts — 路徑管理

**Files:**
- Create: `src/utils/paths.ts`
- Test: `tests/utils/paths.test.ts`

**Step 1: 寫失敗測試**

```typescript
// tests/utils/paths.test.ts
import { describe, test, expect } from "bun:test";
import { paths } from "../../src/utils/paths.js";
import { homedir } from "os";
import { join } from "path";

const HOME = homedir();

describe("paths", () => {
  test("home returns user home directory", () => {
    expect(paths.home).toBe(HOME);
  });

  test("config returns ~/.config", () => {
    expect(paths.config).toBe(join(HOME, ".config"));
  });

  test("customSkills returns ~/.config/custom-skills", () => {
    expect(paths.customSkills).toBe(join(HOME, ".config", "custom-skills"));
  });

  test("claudeConfig returns ~/.claude", () => {
    expect(paths.claudeConfig).toBe(join(HOME, ".claude"));
  });

  test("claudeSkills returns ~/.claude/skills", () => {
    expect(paths.claudeSkills).toBe(join(HOME, ".claude", "skills"));
  });

  test("syncRepo returns ~/.config/ai-dev/sync-repo", () => {
    expect(paths.syncRepo).toBe(join(HOME, ".config", "ai-dev", "sync-repo"));
  });

  test("syncConfig returns ~/.config/ai-dev/sync.yaml", () => {
    expect(paths.syncConfig).toBe(join(HOME, ".config", "ai-dev", "sync.yaml"));
  });

  test("memConfig returns ~/.config/ai-dev/sync-server.yaml", () => {
    expect(paths.memConfig).toBe(join(HOME, ".config", "ai-dev", "sync-server.yaml"));
  });

  test("claudeMemDb returns ~/.claude-mem/claude-mem.db", () => {
    expect(paths.claudeMemDb).toBe(join(HOME, ".claude-mem", "claude-mem.db"));
  });
});
```

**Step 2: 執行測試確認失敗**

Run: `bun test tests/utils/paths.test.ts`
Expected: FAIL — module not found

**Step 3: 實作**

```typescript
// src/utils/paths.ts
import { homedir } from "os";
import { join } from "path";

const HOME = homedir();
const CONFIG = join(HOME, ".config");

export const paths = {
  home: HOME,
  config: CONFIG,

  // custom-skills
  customSkills: join(CONFIG, "custom-skills"),

  // ai-dev
  aiDevConfig: join(CONFIG, "ai-dev"),
  syncRepo: join(CONFIG, "ai-dev", "sync-repo"),
  syncConfig: join(CONFIG, "ai-dev", "sync.yaml"),
  memConfig: join(CONFIG, "ai-dev", "sync-server.yaml"),
  manifests: join(CONFIG, "ai-dev", "manifests"),

  // Claude
  claudeConfig: join(HOME, ".claude"),
  claudeSkills: join(HOME, ".claude", "skills"),
  claudeCommands: join(HOME, ".claude", "commands"),
  claudeAgents: join(HOME, ".claude", "agents"),
  claudeWorkflows: join(HOME, ".claude", "workflows"),

  // Antigravity
  antigravityConfig: join(HOME, ".gemini", "antigravity"),

  // OpenCode
  opencodeConfig: join(CONFIG, "opencode"),
  opencodePlugins: join(CONFIG, "opencode", "plugins"),
  opencodeSuperpowers: join(CONFIG, "opencode", "superpowers"),

  // Codex
  codexConfig: join(HOME, ".codex"),

  // Gemini
  geminiConfig: join(HOME, ".gemini"),

  // Upstream repos
  superpowers: join(CONFIG, "superpowers"),
  uds: join(CONFIG, "universal-dev-standards"),
  obsidianSkills: join(CONFIG, "obsidian-skills"),
  anthropicSkills: join(CONFIG, "anthropic-skills"),
  ecc: join(CONFIG, "everything-claude-code"),
  autoSkill: join(CONFIG, "auto-skill"),

  // claude-mem
  claudeMemDb: join(HOME, ".claude-mem", "claude-mem.db"),
} as const;

export type PathKey = keyof typeof paths;
```

**Step 4: 執行測試確認通過**

Run: `bun test tests/utils/paths.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add src/utils/paths.ts tests/utils/paths.test.ts
git commit -m "功能(v2): 新增 paths.ts 路徑管理模組"
```

---

### Task 1.2: system.ts — 系統工具

**Files:**
- Create: `src/utils/system.ts`
- Test: `tests/utils/system.test.ts`

**Step 1: 寫失敗測試**

```typescript
// tests/utils/system.test.ts
import { describe, test, expect } from "bun:test";
import { getOS, commandExists, runCommand, getBunVersion } from "../../src/utils/system.js";

describe("getOS", () => {
  test("returns linux, macos, or windows", () => {
    const os = getOS();
    expect(["linux", "macos", "windows"]).toContain(os);
  });
});

describe("commandExists", () => {
  test("returns true for existing command", () => {
    expect(commandExists("git")).toBe(true);
  });

  test("returns false for non-existing command", () => {
    expect(commandExists("this_command_does_not_exist_12345")).toBe(false);
  });
});

describe("runCommand", () => {
  test("captures stdout", async () => {
    const result = await runCommand(["echo", "hello"]);
    expect(result.stdout.trim()).toBe("hello");
    expect(result.exitCode).toBe(0);
  });

  test("returns non-zero exit code on failure", async () => {
    const result = await runCommand(["false"], { check: false });
    expect(result.exitCode).not.toBe(0);
  });
});
```

**Step 2: 執行測試確認失敗**

Run: `bun test tests/utils/system.test.ts`
Expected: FAIL

**Step 3: 實作**

```typescript
// src/utils/system.ts
import { platform } from "os";
import { which } from "bun";

export type OS = "linux" | "macos" | "windows";

export function getOS(): OS {
  const p = platform();
  if (p === "darwin") return "macos";
  if (p === "win32") return "windows";
  return "linux";
}

export function commandExists(command: string): boolean {
  return which(command) !== null;
}

export interface RunResult {
  stdout: string;
  stderr: string;
  exitCode: number;
}

export interface RunOptions {
  cwd?: string;
  check?: boolean;
  silent?: boolean;
}

export async function runCommand(
  command: string[],
  options: RunOptions = {},
): Promise<RunResult> {
  const { cwd, check = true, silent = false } = options;

  const proc = Bun.spawn(command, {
    cwd,
    stdout: "pipe",
    stderr: "pipe",
  });

  const stdout = await new Response(proc.stdout).text();
  const stderr = await new Response(proc.stderr).text();
  const exitCode = await proc.exited;

  if (check && exitCode !== 0) {
    if (!silent) {
      console.error(`Command failed: ${command.join(" ")}`);
      if (stderr) console.error(stderr);
    }
    throw new Error(`Command failed with exit code ${exitCode}: ${command.join(" ")}`);
  }

  return { stdout, stderr, exitCode };
}

export async function getBunVersion(): Promise<string | null> {
  try {
    const result = await runCommand(["bun", "--version"], { check: false, silent: true });
    return result.exitCode === 0 ? result.stdout.trim() : null;
  } catch {
    return null;
  }
}

export async function getNpmPackageVersion(pkg: string): Promise<string | null> {
  try {
    const result = await runCommand(["npm", "list", "-g", pkg, "--json"], {
      check: false,
      silent: true,
    });
    if (result.exitCode === 0) {
      const data = JSON.parse(result.stdout);
      return data?.dependencies?.[pkg]?.version ?? null;
    }
  } catch {
    // ignore
  }
  return null;
}
```

**Step 4: 執行測試確認通過**

Run: `bun test tests/utils/system.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add src/utils/system.ts tests/utils/system.test.ts
git commit -m "功能(v2): 新增 system.ts 系統工具模組"
```

---

### Task 1.3: config.ts — YAML 設定檔讀寫

**Files:**
- Create: `src/utils/config.ts`
- Test: `tests/utils/config.test.ts`

**Step 1: 寫失敗測試**

```typescript
// tests/utils/config.test.ts
import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { readYaml, writeYaml } from "../../src/utils/config.js";
import { mkdtempSync, rmSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";

describe("config", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = mkdtempSync(join(tmpdir(), "ai-dev-test-"));
  });

  afterEach(() => {
    rmSync(tmpDir, { recursive: true, force: true });
  });

  test("writeYaml then readYaml roundtrip", () => {
    const filePath = join(tmpDir, "test.yaml");
    const data = { server_url: "http://localhost:3000", api_key: "abc123" };
    writeYaml(filePath, data);
    const result = readYaml(filePath);
    expect(result).toEqual(data);
  });

  test("readYaml returns null for non-existent file", () => {
    const result = readYaml(join(tmpDir, "nope.yaml"));
    expect(result).toBeNull();
  });
});
```

**Step 2: 執行測試確認失敗**

Run: `bun test tests/utils/config.test.ts`
Expected: FAIL

**Step 3: 實作**

```typescript
// src/utils/config.ts
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "fs";
import { dirname } from "path";
import YAML from "yaml";

export function readYaml<T = Record<string, unknown>>(filePath: string): T | null {
  if (!existsSync(filePath)) return null;
  try {
    const content = readFileSync(filePath, "utf-8");
    const data = YAML.parse(content);
    return data ?? null;
  } catch {
    return null;
  }
}

export function writeYaml(filePath: string, data: Record<string, unknown>): void {
  const dir = dirname(filePath);
  mkdirSync(dir, { recursive: true });
  const content = YAML.stringify(data);
  writeFileSync(filePath, content, "utf-8");
}
```

**Step 4: 執行測試確認通過**

Run: `bun test tests/utils/config.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add src/utils/config.ts tests/utils/config.test.ts
git commit -m "功能(v2): 新增 config.ts YAML 設定檔讀寫"
```

---

### Task 1.4: git.ts — Git 操作工具

**Files:**
- Create: `src/utils/git.ts`
- Test: `tests/utils/git.test.ts`

**Step 1: 寫失敗測試**

```typescript
// tests/utils/git.test.ts
import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { isGitRepo, gitInit, gitAddCommit, gitPullRebase, gitPush } from "../../src/utils/git.js";
import { mkdtempSync, rmSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";

describe("git utils", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = mkdtempSync(join(tmpdir(), "ai-dev-git-test-"));
  });

  afterEach(() => {
    rmSync(tmpDir, { recursive: true, force: true });
  });

  test("isGitRepo returns false for non-git directory", async () => {
    expect(await isGitRepo(tmpDir)).toBe(false);
  });

  test("gitInit creates a git repo", async () => {
    await gitInit(tmpDir);
    expect(await isGitRepo(tmpDir)).toBe(true);
  });
});
```

**Step 2: 執行測試確認失敗**

Run: `bun test tests/utils/git.test.ts`
Expected: FAIL

**Step 3: 實作**

```typescript
// src/utils/git.ts
import { existsSync } from "fs";
import { join } from "path";
import { runCommand } from "./system.js";

export async function isGitRepo(dir: string): Promise<boolean> {
  return existsSync(join(dir, ".git"));
}

export async function gitInit(dir: string): Promise<void> {
  await runCommand(["git", "init"], { cwd: dir });
}

export async function gitClone(url: string, dest: string): Promise<void> {
  await runCommand(["git", "clone", url, dest]);
}

export async function gitPull(dir: string): Promise<void> {
  await runCommand(["git", "pull"], { cwd: dir, check: false });
}

export async function gitAddCommit(dir: string, message: string): Promise<void> {
  await runCommand(["git", "add", "-A"], { cwd: dir });

  // Check if there are staged changes
  const result = await runCommand(["git", "diff", "--cached", "--quiet"], {
    cwd: dir,
    check: false,
    silent: true,
  });

  if (result.exitCode !== 0) {
    // There are staged changes
    await runCommand(["git", "commit", "-m", message], { cwd: dir });
  }
}

export async function gitPullRebase(dir: string): Promise<void> {
  // Stash uncommitted changes before rebase
  const stashResult = await runCommand(["git", "stash", "--include-untracked"], {
    cwd: dir,
    check: false,
    silent: true,
  });
  const didStash = !stashResult.stdout.includes("No local changes");

  try {
    await runCommand(["git", "pull", "--rebase"], { cwd: dir });
  } finally {
    if (didStash) {
      await runCommand(["git", "stash", "pop"], { cwd: dir, check: false });
    }
  }
}

export async function gitPush(dir: string): Promise<void> {
  await runCommand(["git", "push"], { cwd: dir });
}

export async function detectLocalChanges(dir: string): Promise<boolean> {
  const result = await runCommand(["git", "status", "--porcelain"], {
    cwd: dir,
    silent: true,
  });
  return result.stdout.trim().length > 0;
}
```

**Step 4: 執行測試確認通過**

Run: `bun test tests/utils/git.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add src/utils/git.ts tests/utils/git.test.ts
git commit -m "功能(v2): 新增 git.ts Git 操作工具"
```

---

### Task 1.5: manifest.ts — 檔案分發追蹤

**Files:**
- Create: `src/utils/manifest.ts`
- Test: `tests/utils/manifest.test.ts`

**Step 1: 寫失敗測試**

```typescript
// tests/utils/manifest.test.ts
import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { computeFileHash, computeDirHash } from "../../src/utils/manifest.js";
import { mkdtempSync, rmSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";

describe("manifest hashing", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = mkdtempSync(join(tmpdir(), "ai-dev-manifest-test-"));
  });

  afterEach(() => {
    rmSync(tmpDir, { recursive: true, force: true });
  });

  test("computeFileHash returns sha256 format", () => {
    const file = join(tmpDir, "test.txt");
    writeFileSync(file, "hello world");
    const hash = computeFileHash(file);
    expect(hash).toMatch(/^sha256:[a-f0-9]{64}$/);
  });

  test("computeFileHash is deterministic", () => {
    const file = join(tmpDir, "test.txt");
    writeFileSync(file, "hello world");
    expect(computeFileHash(file)).toBe(computeFileHash(file));
  });

  test("computeDirHash includes file structure", () => {
    const dir = join(tmpDir, "dir");
    mkdirSync(dir);
    writeFileSync(join(dir, "a.txt"), "aaa");
    writeFileSync(join(dir, "b.txt"), "bbb");
    const hash = computeDirHash(dir);
    expect(hash).toMatch(/^sha256:[a-f0-9]{64}$/);
  });

  test("computeDirHash changes when content changes", () => {
    const dir = join(tmpDir, "dir");
    mkdirSync(dir);
    writeFileSync(join(dir, "a.txt"), "aaa");
    const hash1 = computeDirHash(dir);
    writeFileSync(join(dir, "a.txt"), "bbb");
    const hash2 = computeDirHash(dir);
    expect(hash1).not.toBe(hash2);
  });
});
```

**Step 2: 執行測試確認失敗**

Run: `bun test tests/utils/manifest.test.ts`
Expected: FAIL

**Step 3: 實作**

```typescript
// src/utils/manifest.ts
import { createHash } from "crypto";
import { readFileSync, readdirSync, statSync } from "fs";
import { join, relative } from "path";

export function computeFileHash(filePath: string): string {
  const hash = createHash("sha256");
  const content = readFileSync(filePath);
  hash.update(content);
  return `sha256:${hash.digest("hex")}`;
}

export function computeDirHash(dirPath: string): string {
  const stat = statSync(dirPath);
  if (!stat.isDirectory()) return computeFileHash(dirPath);

  const hash = createHash("sha256");
  const files = getAllFiles(dirPath).sort();

  for (const file of files) {
    const relPath = relative(dirPath, file);
    hash.update(relPath);
    hash.update(computeFileHash(file));
  }

  return `sha256:${hash.digest("hex")}`;
}

function getAllFiles(dir: string): string[] {
  const results: string[] = [];
  const entries = readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "node_modules" || entry.name === "__pycache__") continue;
      results.push(...getAllFiles(fullPath));
    } else {
      if (entry.name.endsWith(".pyc") || entry.name.endsWith(".pyo")) continue;
      results.push(fullPath);
    }
  }

  return results;
}
```

**Step 4: 執行測試確認通過**

Run: `bun test tests/utils/manifest.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add src/utils/manifest.ts tests/utils/manifest.test.ts
git commit -m "功能(v2): 新增 manifest.ts 檔案分發追蹤"
```

---

### Task 1.6: shared.ts — 共用常數與設定

**Files:**
- Create: `src/utils/shared.ts`
- Test: `tests/utils/shared.test.ts`

**Step 1: 寫失敗測試**

```typescript
// tests/utils/shared.test.ts
import { describe, test, expect } from "bun:test";
import { NPM_PACKAGES, BUN_PACKAGES, REPOS, COPY_TARGETS } from "../../src/utils/shared.js";

describe("shared constants", () => {
  test("NPM_PACKAGES is non-empty array", () => {
    expect(NPM_PACKAGES.length).toBeGreaterThan(0);
    expect(NPM_PACKAGES).toContain("@fission-ai/openspec@latest");
  });

  test("BUN_PACKAGES contains codex", () => {
    expect(BUN_PACKAGES).toContain("@openai/codex");
  });

  test("REPOS has required entries", () => {
    expect(REPOS).toHaveProperty("custom_skills");
    expect(REPOS).toHaveProperty("superpowers");
    expect(REPOS).toHaveProperty("uds");
  });

  test("COPY_TARGETS has claude target", () => {
    expect(COPY_TARGETS).toHaveProperty("claude");
    expect(COPY_TARGETS.claude).toHaveProperty("skills");
  });
});
```

**Step 2: 執行測試確認失敗**

Run: `bun test tests/utils/shared.test.ts`
Expected: FAIL

**Step 3: 實作**

移植 Python `shared.py` 中的所有常數：`NPM_PACKAGES`、`BUN_PACKAGES`、`REPOS`、`COPY_TARGETS`、`UNWANTED_UDS_FILES`、`TargetType`、`ResourceType`。

參考來源：`script/utils/shared.py:1-200`

```typescript
// src/utils/shared.ts
import { paths } from "./paths.js";
import { join } from "path";

export type TargetType = "claude" | "antigravity" | "opencode" | "codex" | "gemini";
export type ResourceType = "skills" | "commands" | "agents" | "workflows";

export const NPM_PACKAGES = [
  "@fission-ai/openspec@latest",
  "@google/gemini-cli",
  "universal-dev-standards",
  "opencode-ai@latest",
  "skills",
  "happy-coder",
];

export const BUN_PACKAGES = ["@openai/codex"];

export const OPENCODE_SUPERPOWERS_URL = "https://github.com/obra/superpowers.git";

export const REPOS: Record<string, { url: string; dir: string }> = {
  custom_skills: { url: "https://github.com/ValorVie/custom-skills.git", dir: paths.customSkills },
  superpowers: { url: "https://github.com/obra/superpowers.git", dir: paths.superpowers },
  uds: { url: "https://github.com/AsiaOstrich/universal-dev-standards.git", dir: paths.uds },
  obsidian_skills: { url: "https://github.com/kepano/obsidian-skills.git", dir: paths.obsidianSkills },
  anthropic_skills: { url: "https://github.com/anthropics/skills.git", dir: paths.anthropicSkills },
  everything_claude_code: { url: "https://github.com/affaan-m/everything-claude-code.git", dir: paths.ecc },
  auto_skill: { url: "https://github.com/Toolsai/auto-skill.git", dir: paths.autoSkill },
};

export const COPY_TARGETS: Record<TargetType, Partial<Record<ResourceType, string>>> = {
  claude: {
    skills: paths.claudeSkills,
    commands: paths.claudeCommands,
    agents: paths.claudeAgents,
    workflows: paths.claudeWorkflows,
  },
  antigravity: {
    skills: join(paths.antigravityConfig, "global_skills"),
    workflows: join(paths.antigravityConfig, "global_workflows"),
  },
  opencode: {
    skills: join(paths.opencodeConfig, "skills"),
    commands: join(paths.opencodeConfig, "commands"),
  },
  codex: {
    skills: join(paths.codexConfig, "skills"),
  },
  gemini: {
    skills: join(paths.geminiConfig, "skills"),
  },
};

export const UNWANTED_UDS_FILES = [
  "tdd-assistant",
  "CONTRIBUTING.template.md",
  "install.ps1",
  "install.sh",
  "README.md",
];
```

**Step 4: 執行測試確認通過**

Run: `bun test tests/utils/shared.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add src/utils/shared.ts tests/utils/shared.test.ts
git commit -m "功能(v2): 新增 shared.ts 共用常數與設定"
```

---

## Phase 2: CLI 框架與核心指令

### Task 2.1: CLI 骨架 — Commander.js 主程式

**Files:**
- Create: `src/cli/index.ts`
- Modify: `src/cli.ts`

**Step 1: 實作 CLI 骨架**

```typescript
// src/cli/index.ts
import { Command } from "commander";

const VERSION = "2.0.0";

export function createProgram(): Command {
  const program = new Command()
    .name("ai-dev")
    .version(VERSION, "-v, --version")
    .description("AI Development Environment Setup CLI");

  // 頂層指令 — 後續 task 逐一加入
  // program.command("install").description("安裝環境").action(install);

  return program;
}
```

**Step 2: 驗證 CLI 運作**

Run: `bun run src/cli.ts --version`
Expected: `2.0.0`

Run: `bun run src/cli.ts --help`
Expected: 顯示 help 訊息

**Step 3: Commit**

```bash
git add src/cli/index.ts src/cli.ts
git commit -m "功能(v2): Commander.js CLI 骨架"
```

---

### Task 2.2: status 指令

**Files:**
- Create: `src/cli/status.ts`
- Create: `src/core/status-checker.ts`
- Test: `tests/core/status-checker.test.ts`
- Modify: `src/cli/index.ts`

**Step 1: 寫失敗測試**

```typescript
// tests/core/status-checker.test.ts
import { describe, test, expect, mock } from "bun:test";
import { checkEnvironment } from "../../src/core/status-checker.js";

describe("checkEnvironment", () => {
  test("returns status object with required fields", async () => {
    const status = await checkEnvironment();
    expect(status).toHaveProperty("git");
    expect(status).toHaveProperty("node");
    expect(status).toHaveProperty("bun");
    expect(status.git).toHaveProperty("installed");
  });
});
```

**Step 2: 執行測試確認失敗**

Run: `bun test tests/core/status-checker.test.ts`
Expected: FAIL

**Step 3: 實作 core 層**

```typescript
// src/core/status-checker.ts
import { commandExists, runCommand, getBunVersion, getNpmPackageVersion } from "../utils/system.js";
import { existsSync } from "fs";
import { paths } from "../utils/paths.js";
import { NPM_PACKAGES, REPOS } from "../utils/shared.js";

interface ToolStatus {
  installed: boolean;
  version?: string | null;
}

interface RepoStatus {
  name: string;
  cloned: boolean;
  path: string;
}

export interface EnvironmentStatus {
  git: ToolStatus;
  node: ToolStatus;
  bun: ToolStatus;
  gh: ToolStatus;
  npmPackages: { name: string; installed: boolean; version?: string | null }[];
  repos: RepoStatus[];
}

export async function checkEnvironment(): Promise<EnvironmentStatus> {
  const [gitVersion, nodeVersion, bunVersion] = await Promise.all([
    runCommand(["git", "--version"], { check: false, silent: true }).then(r => r.stdout.trim()).catch(() => null),
    runCommand(["node", "--version"], { check: false, silent: true }).then(r => r.stdout.trim()).catch(() => null),
    getBunVersion(),
  ]);

  const npmPackages = await Promise.all(
    NPM_PACKAGES.map(async (pkg) => {
      const name = pkg.replace(/@latest$/, "");
      const version = await getNpmPackageVersion(name);
      return { name, installed: version !== null, version };
    }),
  );

  const repos = Object.entries(REPOS).map(([key, { dir }]) => ({
    name: key,
    cloned: existsSync(dir),
    path: dir,
  }));

  return {
    git: { installed: commandExists("git"), version: gitVersion },
    node: { installed: commandExists("node"), version: nodeVersion },
    bun: { installed: commandExists("bun"), version: bunVersion },
    gh: { installed: commandExists("gh") },
    npmPackages,
    repos,
  };
}
```

**Step 4: 實作 CLI 層**

```typescript
// src/cli/status.ts
import chalk from "chalk";
import { checkEnvironment } from "../core/status-checker.js";

export async function status(): Promise<void> {
  const env = await checkEnvironment();

  console.log(chalk.bold("\n環境狀態檢查\n"));

  // Tools
  const tools = [
    { name: "Git", ...env.git },
    { name: "Node.js", ...env.node },
    { name: "Bun", ...env.bun },
    { name: "GitHub CLI", ...env.gh },
  ];

  for (const tool of tools) {
    const icon = tool.installed ? chalk.green("✓") : chalk.red("✗");
    const ver = tool.version ? chalk.dim(` (${tool.version})`) : "";
    console.log(`  ${icon} ${tool.name}${ver}`);
  }

  // NPM packages
  console.log(chalk.bold("\nNPM 套件:"));
  for (const pkg of env.npmPackages) {
    const icon = pkg.installed ? chalk.green("✓") : chalk.yellow("✗");
    const ver = pkg.version ? chalk.dim(` (${pkg.version})`) : "";
    console.log(`  ${icon} ${pkg.name}${ver}`);
  }

  // Repos
  console.log(chalk.bold("\n儲存庫:"));
  for (const repo of env.repos) {
    const icon = repo.cloned ? chalk.green("✓") : chalk.yellow("✗");
    console.log(`  ${icon} ${repo.name}`);
  }

  console.log();
}
```

**Step 5: 註冊到 CLI**

在 `src/cli/index.ts` 加入：
```typescript
import { status } from "./status.js";
program.command("status").description("檢查環境狀態").action(status);
```

**Step 6: 執行測試確認通過**

Run: `bun test tests/core/status-checker.test.ts`
Expected: PASS

**Step 7: 手動驗證**

Run: `bun run src/cli.ts status`
Expected: 顯示環境狀態

**Step 8: Commit**

```bash
git add src/cli/status.ts src/core/status-checker.ts tests/core/status-checker.test.ts src/cli/index.ts
git commit -m "功能(v2): 新增 status 指令"
```

---

### Task 2.3: install 指令

**Files:**
- Create: `src/cli/install.ts`
- Create: `src/core/installer.ts`
- Test: `tests/core/installer.test.ts`
- Modify: `src/cli/index.ts`

> 此 task 較大。core 層實作 `runInstall()` 函式，參考 `script/commands/install.py` 的完整行為：
> 1. 檢查前置條件 (Node.js, Git, gh, Bun)
> 2. 安裝全域 npm 套件
> 3. 安裝 Bun 套件
> 4. 建立目錄結構
> 5. Clone 儲存庫
> 6. 複製/同步 skills 到各目標
> 7. 安裝 shell completion

**Step 1: 寫失敗測試** (核心邏輯的單元測試)

```typescript
// tests/core/installer.test.ts
import { describe, test, expect } from "bun:test";
import { validatePrerequisites } from "../../src/core/installer.js";

describe("installer", () => {
  test("validatePrerequisites returns status object", async () => {
    const result = await validatePrerequisites();
    expect(result).toHaveProperty("git");
    expect(result).toHaveProperty("node");
    expect(typeof result.git).toBe("boolean");
  });
});
```

**Step 2-5: 實作 installer core、CLI 層、註冊、測試通過、commit**

> 因為 install 邏輯較多，實作時參考 `script/commands/install.py` 逐段移植。
> 關鍵對照：
> - `subprocess.run(["npm", "install", "-g", ...])` → `runCommand(["npm", "install", "-g", ...])`
> - `shutil.copytree()` → `fs.cpSync(src, dst, { recursive: true })`
> - `Path.mkdir(parents=True)` → `mkdirSync(dir, { recursive: true })`
> - Rich console output → chalk

```bash
git commit -m "功能(v2): 新增 install 指令"
```

---

### Task 2.4: update 指令

**Files:**
- Create: `src/cli/update.ts`
- Create: `src/core/updater.ts`
- Test: `tests/core/updater.test.ts`
- Modify: `src/cli/index.ts`

> 參考 `script/commands/update.py`，移植 update 邏輯。

```bash
git commit -m "功能(v2): 新增 update 指令"
```

---

### Task 2.5: clone 指令

**Files:**
- Create: `src/cli/clone.ts`
- Modify: `src/cli/index.ts`

> 參考 `script/commands/clone.py`。

```bash
git commit -m "功能(v2): 新增 clone 指令"
```

---

### Task 2.6: list 指令

**Files:**
- Create: `src/cli/list.ts`
- Modify: `src/cli/index.ts`

> 參考 `script/commands/list.py`。

```bash
git commit -m "功能(v2): 新增 list 指令"
```

---

### Task 2.7: toggle 指令

**Files:**
- Create: `src/cli/toggle.ts`
- Modify: `src/cli/index.ts`

> 參考 `script/commands/toggle.py`。

```bash
git commit -m "功能(v2): 新增 toggle 指令"
```

---

### Task 2.8: add-repo / add-custom-repo / update-custom-repo 指令

**Files:**
- Create: `src/cli/add-repo.ts`
- Create: `src/cli/add-custom-repo.ts`
- Create: `src/cli/update-custom-repo.ts`
- Create: `src/utils/custom-repos.ts`
- Modify: `src/cli/index.ts`

> 參考 `script/commands/add_repo.py`、`add_custom_repo.py`、`update_custom_repo.py`。

```bash
git commit -m "功能(v2): 新增 repo 管理指令 (add-repo, add-custom-repo, update-custom-repo)"
```

---

### Task 2.9: test / coverage / derive-tests 指令

**Files:**
- Create: `src/cli/test.ts`
- Create: `src/cli/coverage.ts`
- Create: `src/cli/derive-tests.ts`
- Modify: `src/cli/index.ts`

> 參考 `script/commands/test.py`、`coverage.py`、`derive_tests.py`。

```bash
git commit -m "功能(v2): 新增 test, coverage, derive-tests 指令"
```

---

## Phase 3: 子命令組

### Task 3.1: project 子命令 (init, update)

**Files:**
- Create: `src/cli/project/index.ts`
- Create: `src/cli/project/init.ts`
- Create: `src/cli/project/update.ts`
- Create: `src/core/project-manager.ts`
- Test: `tests/core/project-manager.test.ts`
- Modify: `src/cli/index.ts`

> 參考 `script/commands/project.py`（612 行）。核心邏輯：模板複製、merge、diff、備份。

```bash
git commit -m "功能(v2): 新增 project 子命令組"
```

---

### Task 3.2: standards 子命令 (status, list, switch, show, overlaps)

**Files:**
- Create: `src/cli/standards/index.ts`
- Create: `src/cli/standards/status.ts`
- Create: `src/cli/standards/list.ts`
- Create: `src/cli/standards/switch.ts`
- Create: `src/cli/standards/show.ts`
- Create: `src/cli/standards/overlaps.ts`
- Create: `src/core/standards-manager.ts`
- Test: `tests/core/standards-manager.test.ts`
- Modify: `src/cli/index.ts`

> 參考 `script/commands/standards.py`（801 行）。核心邏輯：profile YAML 管理、overlap 偵測。

```bash
git commit -m "功能(v2): 新增 standards 子命令組"
```

---

### Task 3.3: hooks 子命令 (install, uninstall, status)

**Files:**
- Create: `src/cli/hooks/index.ts`
- Modify: `src/cli/index.ts`

> 參考 `script/commands/hooks.py`（67 行，最簡單的子命令組）。

```bash
git commit -m "功能(v2): 新增 hooks 子命令組"
```

---

### Task 3.4: sync 子命令 (init, push, pull, status, add, remove)

**Files:**
- Create: `src/cli/sync/index.ts`
- Create: `src/cli/sync/init.ts`
- Create: `src/cli/sync/push.ts`
- Create: `src/cli/sync/pull.ts`
- Create: `src/cli/sync/status.ts`
- Create: `src/cli/sync/add.ts`
- Create: `src/cli/sync/remove.ts`
- Create: `src/core/sync-engine.ts`
- Test: `tests/core/sync-engine.test.ts`
- Modify: `src/cli/index.ts`

> 參考 `script/commands/sync.py`（554 行）和 `script/utils/sync_config.py`。
> 核心邏輯：目錄同步、git LFS 偵測、gitignore 生成、path normalization。

```bash
git commit -m "功能(v2): 新增 sync 子命令組"
```

---

### Task 3.5: mem 子命令 (register, push, pull, status, reindex)

**Files:**
- Create: `src/cli/mem/index.ts`
- Create: `src/cli/mem/register.ts`
- Create: `src/cli/mem/push.ts`
- Create: `src/cli/mem/pull.ts`
- Create: `src/cli/mem/status.ts`
- Create: `src/cli/mem/reindex.ts`
- Create: `src/core/mem-sync.ts`
- Test: `tests/core/mem-sync.test.ts`
- Modify: `src/cli/index.ts`

> 參考 `script/commands/mem.py`（620 行）和 `script/utils/mem_sync.py`。
> 核心邏輯：SQLite 讀取、HTTP API 呼叫、content hash 去重。
>
> 關鍵對照：
> - `sqlite3.connect(f"file:{path}?mode=ro", uri=True)` → `new Database(path, { readonly: true })` (better-sqlite3)
> - `urllib.request` → `fetch()`
> - `hashlib.sha256()` → `createHash("sha256")`

```bash
bun add better-sqlite3
bun add -d @types/better-sqlite3
git commit -m "功能(v2): 新增 mem 子命令組"
```

---

## Phase 4: 完整 Manifest 與 Skill 複製系統

### Task 4.1: ManifestTracker — 完整分發追蹤

**Files:**
- Modify: `src/utils/manifest.ts` (擴充 ManifestTracker、衝突偵測、孤兒清理)
- Test: `tests/utils/manifest.test.ts` (擴充)

> 參考 `script/utils/manifest.py` 的 ManifestTracker、detect_conflicts、find_orphans、cleanup_orphans、backup_file。

```bash
git commit -m "功能(v2): ManifestTracker 完整分發追蹤系統"
```

---

### Task 4.2: copy_skills — Skill 複製邏輯

**Files:**
- Modify: `src/utils/shared.ts` (加入 copySkills 等函式)
- Test: `tests/utils/shared.test.ts` (擴充)

> 參考 `script/utils/shared.py:200+` 的 `copy_skills()`、`get_all_skill_names()`。

```bash
git commit -m "功能(v2): copySkills 完整 skill 複製邏輯"
```

---

## Phase 5: TUI (Ink)

### Task 5.1: 安裝 Ink 依賴，建立 TUI 骨架

**Files:**
- Create: `src/tui/App.tsx`
- Create: `src/tui/index.tsx`
- Modify: `src/cli/index.ts`

**Step 1: 安裝 Ink**

```bash
bun add ink ink-select-input ink-text-input ink-spinner react
bun add -d @types/react
```

**Step 2: 建立 TUI 入口**

```tsx
// src/tui/index.tsx
import React from "react";
import { render } from "ink";
import { App } from "./App.js";

export function launchTUI(): void {
  render(<App />);
}
```

```tsx
// src/tui/App.tsx
import React, { useState } from "react";
import { Box, Text, useInput, useApp } from "ink";

type Screen = "main" | "preview" | "confirm" | "settings";

export function App() {
  const [screen, setScreen] = useState<Screen>("main");
  const { exit } = useApp();

  useInput((input) => {
    if (input === "q") exit();
  });

  return (
    <Box flexDirection="column">
      <Text bold color="cyan">ai-dev TUI v2</Text>
      <Text dimColor>Press q to quit</Text>
    </Box>
  );
}
```

**Step 3: 註冊 tui 指令**

```typescript
// src/cli/index.ts 加入
program.command("tui").description("啟動互動式 TUI").action(async () => {
  const { launchTUI } = await import("../tui/index.js");
  launchTUI();
});
```

**Step 4: 驗證**

Run: `bun run src/cli.ts tui`
Expected: 顯示基本 TUI，按 q 退出

**Step 5: Commit**

```bash
git add src/tui/ src/cli/index.ts
git commit -m "功能(v2): Ink TUI 骨架"
```

---

### Task 5.2: MainScreen — 主畫面

**Files:**
- Create: `src/tui/screens/MainScreen.tsx`
- Create: `src/tui/components/Header.tsx`
- Create: `src/tui/components/TabBar.tsx`
- Create: `src/tui/components/FilterBar.tsx`
- Create: `src/tui/components/ResourceList.tsx`
- Create: `src/tui/components/ResourceItem.tsx`
- Create: `src/tui/components/ActionBar.tsx`
- Create: `src/tui/hooks/useResources.ts`
- Create: `src/tui/hooks/useKeyBindings.ts`
- Modify: `src/tui/App.tsx`

> 參考 `script/tui/app.py` 的 widget 結構，逐一移植為 Ink 元件。
> 使用 useReducer + Context 管理狀態。

```bash
git commit -m "功能(v2): TUI MainScreen 與所有子元件"
```

---

### Task 5.3: PreviewScreen / ConfirmScreen / SettingsScreen

**Files:**
- Create: `src/tui/screens/PreviewScreen.tsx`
- Create: `src/tui/screens/ConfirmScreen.tsx`
- Create: `src/tui/screens/SettingsScreen.tsx`
- Modify: `src/tui/App.tsx`

> 參考 `script/tui/app.py` 的 ModalScreen 子類。

```bash
git commit -m "功能(v2): TUI 輔助畫面 (Preview, Confirm, Settings)"
```

---

## Phase 6: 整合測試與收尾

### Task 6.1: CLI 整合測試

**Files:**
- Create: `tests/cli/smoke.test.ts`

```typescript
// tests/cli/smoke.test.ts
import { describe, test, expect } from "bun:test";

async function runCli(args: string[]): Promise<{ stdout: string; exitCode: number }> {
  const proc = Bun.spawn(["bun", "run", "src/cli.ts", ...args], {
    stdout: "pipe",
    stderr: "pipe",
  });
  const stdout = await new Response(proc.stdout).text();
  const exitCode = await proc.exited;
  return { stdout, exitCode };
}

describe("CLI smoke tests", () => {
  test("--version returns 2.0.0", async () => {
    const { stdout, exitCode } = await runCli(["--version"]);
    expect(exitCode).toBe(0);
    expect(stdout.trim()).toBe("2.0.0");
  });

  test("--help shows all commands", async () => {
    const { stdout, exitCode } = await runCli(["--help"]);
    expect(exitCode).toBe(0);
    expect(stdout).toContain("install");
    expect(stdout).toContain("update");
    expect(stdout).toContain("status");
    expect(stdout).toContain("sync");
    expect(stdout).toContain("mem");
  });

  test("status runs without error", async () => {
    const { exitCode } = await runCli(["status"]);
    expect(exitCode).toBe(0);
  });
});
```

```bash
git commit -m "測試(v2): CLI 冒煙測試"
```

---

### Task 6.2: 全部測試通過驗證

**Step 1: 執行所有測試**

Run: `bun test`
Expected: 所有測試通過

**Step 2: Lint 檢查**

Run: `bun run lint`
Expected: 無錯誤

**Step 3: 型別檢查**

Run: `bunx tsc --noEmit`
Expected: 無錯誤

---

### Task 6.3: 建置與發佈準備

**Step 1: 建置**

```bash
bun run build
```

**Step 2: 驗證 dist 輸出**

Run: `ls dist/`
Expected: `cli.js`

**Step 3: 更新 README.md**

更新安裝方式：
```bash
# 全域安裝
bun add -g @valorvie/ai-dev
# 或
npm install -g @valorvie/ai-dev
```

**Step 4: Commit**

```bash
git commit -m "雜項(v2): 建置配置與 README 更新"
```

---

### Task 6.4: 合併回 main

**Step 1: 確認所有測試通過**

```bash
bun test && bun run lint && bunx tsc --noEmit
```

**Step 2: 合併 v2 到 main**

```bash
git checkout main
git merge v2
git tag v2.0.0
```

**Step 3: 驗證**

Run: `bun run src/cli.ts --version`
Expected: `2.0.0`

---

## 附錄：Python → TypeScript 對照速查

| Python | TypeScript/Bun |
|--------|----------------|
| `pathlib.Path` | `path.join()` + `fs.*` |
| `Path.home()` | `os.homedir()` |
| `Path.mkdir(parents=True)` | `mkdirSync(dir, { recursive: true })` |
| `Path.exists()` | `existsSync(path)` |
| `shutil.copytree()` | `fs.cpSync(src, dst, { recursive: true })` |
| `shutil.copy2()` | `fs.copyFileSync(src, dst)` |
| `shutil.rmtree()` | `fs.rmSync(dir, { recursive: true })` |
| `subprocess.run()` | `Bun.spawn()` |
| `os.symlink()` | `fs.symlinkSync()` |
| `hashlib.sha256()` | `crypto.createHash("sha256")` |
| `urllib.request` | `fetch()` |
| `sqlite3.connect()` | `new Database()` (better-sqlite3) |
| `yaml.safe_load()` | `YAML.parse()` |
| `yaml.dump()` | `YAML.stringify()` |
| `typer.echo()` | `console.log()` + chalk |
| `typer.confirm()` | `inquirer.confirm()` |
| `rich.console.print()` | `console.log()` + chalk |

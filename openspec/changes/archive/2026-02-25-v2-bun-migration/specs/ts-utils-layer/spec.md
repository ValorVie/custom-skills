## ADDED Requirements

### Requirement: paths 模組提供所有配置路徑
`src/utils/paths.ts` SHALL 匯出 `paths` 物件，包含所有工具的配置目錄路徑。

#### Scenario: 路徑正確性
- **WHEN** 匯入 `paths.claudeSkills`
- **THEN** 值為 `~/.claude/skills` 的絕對路徑

#### Scenario: 跨平台 home 目錄
- **WHEN** 在 Linux、macOS 或 Windows 上執行
- **THEN** `paths.home` 回傳對應作業系統的使用者家目錄

### Requirement: system 模組提供系統操作
`src/utils/system.ts` SHALL 提供 `getOS()`、`commandExists()`、`runCommand()` 函式。

#### Scenario: 偵測作業系統
- **WHEN** 呼叫 `getOS()`
- **THEN** 回傳 `"linux"` | `"macos"` | `"windows"` 之一

#### Scenario: 執行外部指令
- **WHEN** 呼叫 `runCommand(["echo", "hello"])`
- **THEN** 回傳包含 `stdout: "hello\n"` 和 `exitCode: 0` 的結果

#### Scenario: 指令失敗且 check=true
- **WHEN** 呼叫 `runCommand(["false"], { check: true })`
- **THEN** 拋出 Error

### Requirement: config 模組提供 YAML 讀寫
`src/utils/config.ts` SHALL 提供 `readYaml()` 和 `writeYaml()` 函式。

#### Scenario: 讀寫 roundtrip
- **WHEN** 寫入 `{ key: "value" }` 到 YAML 後再讀取
- **THEN** 回傳相同的物件

#### Scenario: 讀取不存在的檔案
- **WHEN** 呼叫 `readYaml("nonexistent.yaml")`
- **THEN** 回傳 `null`

### Requirement: git 模組提供 Git 操作
`src/utils/git.ts` SHALL 提供 `isGitRepo()`、`gitInit()`、`gitClone()`、`gitPull()`、`gitAddCommit()`、`gitPullRebase()`、`gitPush()`、`detectLocalChanges()` 函式。

#### Scenario: 偵測 Git repo
- **WHEN** 呼叫 `isGitRepo(path)` 且 path 下有 `.git/`
- **THEN** 回傳 `true`

#### Scenario: 初始化 Git repo
- **WHEN** 呼叫 `gitInit(path)` 後再呼叫 `isGitRepo(path)`
- **THEN** 回傳 `true`

### Requirement: manifest 模組提供 hash 計算
`src/utils/manifest.ts` SHALL 提供 `computeFileHash()` 和 `computeDirHash()` 函式，回傳 `sha256:<hex>` 格式。

#### Scenario: 檔案 hash 格式
- **WHEN** 對任意檔案呼叫 `computeFileHash()`
- **THEN** 回傳匹配 `^sha256:[a-f0-9]{64}$` 的字串

#### Scenario: 目錄 hash 確定性
- **WHEN** 對相同目錄呼叫兩次 `computeDirHash()`
- **THEN** 兩次結果相同

#### Scenario: 內容變更影響 hash
- **WHEN** 修改目錄中的檔案後重新計算 `computeDirHash()`
- **THEN** hash 值改變

### Requirement: shared 模組提供共用常數
`src/utils/shared.ts` SHALL 匯出 `NPM_PACKAGES`、`BUN_PACKAGES`、`REPOS`、`COPY_TARGETS` 常數。

#### Scenario: NPM_PACKAGES 內容
- **WHEN** 匯入 `NPM_PACKAGES`
- **THEN** 陣列包含 `"@fission-ai/openspec@latest"`

#### Scenario: REPOS 結構
- **WHEN** 匯入 `REPOS`
- **THEN** 每個項目包含 `url` 和 `dir` 屬性

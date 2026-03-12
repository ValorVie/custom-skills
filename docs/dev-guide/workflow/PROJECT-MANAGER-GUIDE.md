# Project Manager — VS Code 專案快速切換指南

## 目錄

- [簡介與定位](#簡介與定位)
- [安裝](#安裝)
- [快速開始：3 個核心指令](#快速開始3-個核心指令)
- [兩種使用模式](#兩種使用模式)
- [推薦設定](#推薦設定)
- [設定項說明](#設定項說明)
- [日常操作](#日常操作)
- [進階：Tag 分類](#進階tag-分類)
- [進階：編輯專案清單](#進階編輯專案清單)
- [進階：搭配 Profile](#進階搭配-profile)
- [Remote 專案](#remote-專案)
- [建議使用模式](#建議使用模式)
- [常見問題](#常見問題)
- [參考資料](#參考資料)

---

## 簡介與定位

**Project Manager** 是 Alessandro Fragnani 開發的 VS Code 擴充套件（Marketplace 約 700 萬安裝），核心用途是**快速切換專案**。

它解決的問題：

- 把資料夾或 workspace 存成專案，隨時快速開啟
- 自動掃描 Git / Mercurial / SVN / VS Code workspace
- 用 Tag 分類專案
- 在側邊欄管理專案清單
- 支援 Profile（不同專案載入不同擴充套件組合）
- 支援 Remote 專案（SSH / WSL / Container）

---

## 安裝

在 VS Code 中搜尋 `alefragnani.project-manager` 或透過 Command Palette：

```
ext install alefragnani.project-manager
```

---

## 快速開始：3 個核心指令

打開 Command Palette（macOS: `Cmd+Shift+P` / Windows・Linux: `Ctrl+Shift+P`）：

| 指令 | 用途 |
|------|------|
| `Project Manager: Save Project` | 把目前開著的資料夾存成專案（會自動建議名稱） |
| `Project Manager: List Projects to Open` | 列出所有專案，選一個在目前視窗開啟 |
| `Project Manager: List Projects to Open in New Window` | 同上，但一定開新視窗 |

學會這 3 個指令就能立刻開始使用。

---

## 兩種使用模式

### 模式 A：手動儲存常用專案

適合剛開始使用，不需要任何設定。

1. 開啟某個專案資料夾
2. 執行 `Project Manager: Save Project`
3. 取名，例如：`Core Backend`、`Infra Ops`、`AI Tools`
4. 之後用 `Project Manager: List Projects to Open` 快速開啟

**優點：** 最直覺、不會把雜 repo 都抓進來。

### 模式 B：自動掃描 repo 根目錄

適合專案數量多的人。設定 `baseFolders` 讓它自動偵測 Git repo：

```json
"projectManager.git.baseFolders": [
  "~/work",
  "~/repos",
  "~/projects"
]
```

**優點：** 不用一個個手動存，新 repo 自動出現在清單中。

---

## 推薦設定

在 `settings.json` 中加入：

```json
{
  "projectManager.git.baseFolders": [
    "~/work",
    "~/repos",
    "~/projects"
  ],
  "projectManager.git.ignoredFolders": [
    "node_modules",
    "vendor",
    "dist",
    "build",
    ".git",
    ".venv",
    "venv",
    "target",
    "__pycache__",
    ".cargo",
    ".gradle",
    "bower_components",
    "out",
    "tmp",
    "coverage",
    ".terraform"
  ],
  "projectManager.git.maxDepthRecursion": 4,
  "projectManager.ignoreProjectsWithinProjects": true,
  "projectManager.sortList": "Recent",
  "projectManager.groupList": true,
  "projectManager.showParentFolderInfoOnDuplicates": true,
  "projectManager.filterOnFullPath": true,
  "projectManager.cacheProjectsBetweenSessions": true,
  "projectManager.showProjectNameInStatusBar": true,
  "projectManager.tags": [
    "Work",
    "Infra",
    "AI",
    "Personal",
    "Archive"
  ]
}
```

---

## 設定項說明

| 設定 | 說明 |
|------|------|
| `git.baseFolders` | repo 的根目錄，從這些位置往下掃描 |
| `git.maxDepthRecursion` | 掃描深度，repo 多時不宜太深，否則會慢 |
| `git.ignoredFolders` | 掃描時忽略的目錄（見下方判斷標準） |
| `ignoreProjectsWithinProjects` | 忽略巢狀 repo / submodule，避免清單爆炸（見下方說明） |
| `sortList` | 排序方式：`Saved` / `Name` / `Path` / `Recent` |
| `groupList` | 按來源分組（Favorites、Git 等） |
| `showParentFolderInfoOnDuplicates` | 同名專案時顯示上層目錄，方便區分 |
| `filterOnFullPath` | 搜尋時比對完整路徑，提高篩選精度 |
| `cacheProjectsBetweenSessions` | 快取掃描結果，加快啟動速度 |
| `showProjectNameInStatusBar` | 在狀態列顯示目前專案名稱 |
| `tags` | 自訂 Tag 清單，用於專案分類 |

### `ignoreProjectsWithinProjects` 與巢狀 repo

此設定只有 `true` / `false`，無法單獨設定深度。但可以搭配 `maxDepthRecursion` 間接控制：

| 情境 | 設定 |
|------|------|
| repo 多、有 submodule，清單要乾淨 | `ignoreProjectsWithinProjects: true` |
| 想看巢狀 repo 但控制範圍 | `ignoreProjectsWithinProjects: false` + 降低 `maxDepthRecursion`（建議 2-3） |

當 `ignoreProjectsWithinProjects` 為 `false` 時，掃描到的所有巢狀 repo 都會出現在清單中，範圍由 `maxDepthRecursion` 決定。

### `git.ignoredFolders` 判斷標準

這個設定控制掃描 Git repo 時**不進入哪些子目錄**。值得加入的目錄符合以下任一條件：

1. **內部可能藏有 `.git`，會產生假 repo**：例如 `node_modules`、`vendor`、`.venv` — 套件管理器安裝的依賴有時保留原始 `.git` 目錄，導致清單中出現大量不相關的 repo
2. **目錄體積大，跳過可加速掃描**：例如 `target`、`.cargo`、`.gradle` — 編譯快取或依賴快取動輒數 GB，進入掃描浪費時間

**不需要加入的目錄：**

- 體積小且不可能包含 `.git` 的框架產物（如 `.next`、`.nuxt`、`.output`）
- 已被 `ignoreProjectsWithinProjects` 處理的巢狀 repo / submodule

---

## 日常操作

### 開啟專案

1. `Cmd/Ctrl + Shift + P`
2. 輸入 `Project Manager: List Projects to Open`
3. 輸入幾個字搜尋
4. `Enter`

### 保留目前視窗，另開專案

使用 `Project Manager: List Projects to Open in New Window`。

適合正在 debug A，想順手打開 B 看一下的情境。

---

## 進階：Tag 分類

### 設定 Tag

```json
"projectManager.tags": [
  "Work",
  "Infra",
  "AI",
  "Experiment",
  "Personal"
]
```

### 使用 Tag

- 編輯專案資訊時可加上 Tag
- 用 `Project Manager: Filter Projects by Tag` 篩選特定分類的專案

---

## 進階：編輯專案清單

執行 `Project Manager: Edit Projects` 會直接打開 `projects.json`：

```json
[
  {
    "name": "Core Backend",
    "rootPath": "~/work/core-backend",
    "tags": ["Work"],
    "enabled": true,
    "profile": "Full Dev"
  },
  {
    "name": "Infra Ops",
    "rootPath": "~/work/infra",
    "tags": ["Work", "Infra"],
    "enabled": true,
    "profile": "Infra"
  }
]
```

支援欄位：

| 欄位 | 說明 |
|------|------|
| `name` | 顯示名稱 |
| `rootPath` | 專案路徑（支援 `~` 和 `$home`） |
| `tags` | Tag 分類 |
| `enabled` | 是否顯示在清單中 |
| `profile` | 開啟時使用的 VS Code Profile |

---

## 進階：搭配 Profile

VS Code 的 Profile 功能可以為不同情境載入不同的擴充套件組合。Project Manager 已支援 Profile，可在 `projects.json` 中為專案指定 Profile：

```json
"profile": "Infra"
```

建議的 Profile 規劃：

| Profile | 適用情境 |
|---------|---------|
| Full Dev | 完整開發：語言伺服器、Linter、Git 工具全開 |
| Light Browse | 只看程式碼，不跑分析 |
| Infra | SSH / Docker / YAML / Shell |
| AI | AI 開發工具、MCP 相關擴充套件 |

---

## Remote 專案（SSH / WSL / Container）

### 運作原理

Project Manager 的 `rootPath` 支援 Remote URI 格式。當你透過 VS Code Remote-SSH 連線到遠端主機並儲存專案時，它會自動記錄完整的遠端路徑，之後從清單開啟時會自動建立 SSH 連線。

### 設定步驟

#### 1. 前置條件

確保已安裝 [Remote - SSH](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh) 擴充套件，且 `~/.ssh/config` 已設定好主機：

```
Host prod-server
  HostName 192.168.1.100
  User deploy
  IdentityFile ~/.ssh/id_ed25519

Host staging
  HostName staging.example.com
  User dev
  Port 2222
```

#### 2. 儲存 Remote 專案

1. 用 `Remote-SSH: Connect to Host` 連線到遠端主機
2. 開啟遠端的專案資料夾
3. 執行 `Project Manager: Save Project`
4. 取名，例如：`Prod - Web App`

儲存後，`projects.json` 中的路徑會是 Remote URI 格式：

```json
{
  "name": "Prod - Web App",
  "rootPath": "vscode-remote://ssh-remote+prod-server/home/deploy/web-app",
  "tags": ["Server", "Work"],
  "enabled": true
}
```

#### 3. 統一清單 vs 遠端自動掃描

管理 Remote 專案有兩種模式，核心取捨在於**清單是否統一**：

| | 預設模式（推薦） | 遠端掃描模式 |
|---|---|---|
| extensionKind | `"ui"`（預設，不用設） | 改為 `"workspace"` |
| Save Project 存到 | **本機** `projects.json` | **遠端** `projects.json` |
| 本機 + 遠端同一份清單 | **是** | 否（分開兩份） |
| 遠端 baseFolders 自動掃描 | 不支援 | **支援** |

**推薦預設模式：** 遠端專案數量通常不多，手動 `Save Project` 就夠了。保持預設讓所有專案（本機 + 遠端）出現在同一份清單，切換更方便。連線到遠端後執行 `Save Project`，路徑會自動記錄為 `vscode-remote://ssh-remote+host/path` 格式。

#### 4. 遠端自動掃描設定（選用）

以下只在你需要**自動掃描遠端主機上的 repo** 時才需要。注意啟用後，本機與遠端的專案清單會分開。

**背景：** VS Code Remote 架構分兩端 — UI 端（本機，管介面）和 Workspace 端（遠端，管檔案系統）。Project Manager 預設跑在 UI 端，所以 baseFolders 只會掃描本機目錄。

要讓它掃描遠端主機的目錄，需要兩步：

**步驟一：** 讓 Project Manager 在遠端執行。在本機 `settings.json` 加入：

```json
"remote.extensionKind": {
  "alefragnani.project-manager": [
    "workspace"
  ]
}
```

> **關於 `"workspace"` 值：** 這是 VS Code 的固定值，不是自訂名稱。VS Code 擴充套件只能跑在兩個位置：`"ui"`（本機，管介面）或 `"workspace"`（遠端，管檔案系統）。Project Manager 預設是 `"ui"`，這裡覆寫成 `"workspace"` 讓它在遠端執行。

**步驟二：** 在 Remote 端的 settings 設定 baseFolders。連線到遠端後，透過 Command Palette 搜尋 `Preferences: Open Remote Settings`，加入：

```json
"projectManager.git.baseFolders": [
  "/home/deploy/projects",
  "/opt/apps"
]
```

> **注意：** baseFolders 要寫在 Remote 端的 settings，而非本機的 settings.json，因為路徑是遠端主機上的目錄。

> **其他設定不需重複設定：** VS Code 的 settings 有合併機制 — Remote Settings 會自動繼承本機 User Settings。`ignoredFolders`、`maxDepthRecursion`、`sortList` 等設定只要在本機設過，遠端就會沿用。只有需要覆寫的值（如不同的 `baseFolders` 或特定主機的 `ignoredFolders`）才需要寫在 Remote Settings。

### 手動編輯 Remote 專案

也可以直接在 `projects.json` 手動新增 Remote 專案：

```json
[
  {
    "name": "Prod - Web App",
    "rootPath": "vscode-remote://ssh-remote+prod-server/home/deploy/web-app",
    "tags": ["Server"],
    "enabled": true
  },
  {
    "name": "Staging - API",
    "rootPath": "vscode-remote://ssh-remote+staging/home/dev/api",
    "tags": ["Server"],
    "enabled": true
  },
  {
    "name": "Dev Container - Backend",
    "rootPath": "vscode-remote://dev-container+backend/workspace",
    "tags": ["Docker"],
    "enabled": true
  }
]
```

URI 格式規則：

| 類型 | 格式 |
|------|------|
| SSH | `vscode-remote://ssh-remote+<ssh-config-host>/<absolute-path>` |
| WSL | `vscode-remote://wsl+<distro>/<absolute-path>` |
| Container | `vscode-remote://dev-container+<container>/<absolute-path>` |

其中 SSH 的 `<ssh-config-host>` 對應 `~/.ssh/config` 中的 `Host` 名稱。

### 建議：用 Tag 區分本機與遠端

```json
"projectManager.tags": [
  "Work",
  "Server",
  "Local",
  "Docker",
  "AI"
]
```

這樣在清單中可以用 `Filter Projects by Tag` 快速篩出所有 Server 端專案。

---

## 建議使用模式

### 最小落地方案

1. **設 baseFolders**：指向你的 repo 根目錄
2. **手動存 5 個最常用專案**：用 `Save Project`
3. **設 Tag**：建立 3-5 個分類

### 進階使用模式

| 策略 | 說明 |
|------|------|
| 常用專案做成 Favorites | 手動存最常開的 5-10 個專案 |
| 大量 repo 靠自動掃描 | 設 baseFolders 自動偵測 |
| Tag 分組 | 依工作類型分類：Work / Infra / AI / Personal |
| 重要專案用 workspace 檔 | 建立 `.code-workspace`，存進 Project Manager |

### 完整工作流

**Project Manager + `.code-workspace` + Profile** 的組合：

1. 用 `.code-workspace` 定義多 repo 工作情境
2. 用 Profile 控制每個情境載入的擴充套件
3. 用 Project Manager 快速切換這些情境

---

## 常見問題

### 1. 第一次掃描很慢

**原因：** baseFolders 範圍太大。

**解法：**
- 不要把 `~/`（整個家目錄）丟進去
- 只掃真正放 repo 的目錄
- 限制 `maxDepthRecursion`（建議 3-4）

### 2. 清單出現太多巢狀 repo / submodule

**解法：**

```json
"projectManager.ignoreProjectsWithinProjects": true
```

### 3. 同名專案無法區分

**解法：**

```json
"projectManager.showParentFolderInfoOnDuplicates": true
```

### 4. 自動偵測抓到太多雜 repo

**解法：**
- 常用的手動 `Save Project`，靠 Favorites 管理
- 自動偵測的當作候選
- 用 Tag 篩選重要專案

---

## 參考資料

- [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=alefragnani.project-manager)
- [GitHub Repository](https://github.com/alefragnani/vscode-project-manager)

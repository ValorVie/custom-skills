---
tags:
  - ai
  - mcp
  - cli
  - code-intelligence
  - knowledge-graph
date created: 2026-08-07T14:14:00+08:00
date modified: 2026-08-07T14:14:00+08:00
description: CodeGraph 的版本選擇、安裝驗證、專案索引、CLI 與 MCP 設定及移除方式
---

# CodeGraph 程式碼知識圖譜

CodeGraph 是本機程式碼索引工具。它以 Tree-sitter 解析原始碼，將符號、呼叫、匯入、
繼承、路由與部分框架關係寫入每個專案自己的 SQLite 圖資料庫。Agent 可以透過 CLI
或 MCP 查詢同一份索引。

| 項目 | 內容 |
|------|------|
| GitHub | <https://github.com/colbymchenry/codegraph> |
| 授權 | MIT |
| npm 套件 | `@colbymchenry/codegraph` |
| 索引位置 | 專案根目錄的 `.codegraph/` |
| 預設 MCP 工具 | `codegraph_explore` |

這份指南適合需要理解多語言程式碼、追蹤呼叫鏈或在修改前盤點影響範圍的開發者。
精確字串、Git 歷史、執行中服務與動態資料仍要使用對應工具查證。靜態圖譜不能取代
原始碼、測試或現場狀態。

## 先選 CLI 或 MCP

CLI 與 MCP 共用索引，也能取得相同的 `explore` 結果。差別在於誰負責同步與呼叫。

| 模式 | 適用情境 | 索引同步 | Agent 約束 |
|------|----------|----------|------------|
| CLI | 初次試用、腳本、低頻查詢 | 查詢前執行 `codegraph sync` | 由專案指令或 Skill 規定查詢順序 |
| MCP | 日常 Agent 對話、高頻探索 | MCP server 監看檔案並增量同步 | 每次連線時送出 CodeGraph 工具指引 |

MCP 能讓 Agent 每次連線時收到一致的工具說明，也能主動標示同步中的檔案。它不是
存取控制或正確性保證；系統指令、專案規則、檔案權限與人工審查仍然有效。

## 前置條件

- 使用本機磁碟上的 Git checkout。SQLite DB 不應放在網路磁碟，也不應跨作業系統共用。
- 先確認目標 repo 沒有把憑證、私鑰或其他不應索引的資料納入版本控制。
- 選定並固定一個已審查的 CodeGraph 版本，不在受控環境直接追蹤 `latest`。
- 使用 npm 安裝時需要 Node.js 與 npm；官方 release bundle 內含執行環境。

## 安裝

### 方式一：固定 npm 版本

將 `<reviewed-version>` 換成已審查的明確版本：

```bash
npm install --global @colbymchenry/codegraph@<reviewed-version>
npm audit signatures
codegraph version
```

這種方式操作簡單，但會寫入 npm 的全域安裝位置。共用工作站應先確認安裝前綴與更新
政策，不要使用 `sudo npm install --global`。

### 方式二：驗證 GitHub release bundle

以下以 Linux x64 為例。先把版本改成已審查的發行標籤：

```bash
CODEGRAPH_VERSION=vX.Y.Z
CODEGRAPH_PLATFORM=linux-x64
CODEGRAPH_ARCHIVE="codegraph-${CODEGRAPH_PLATFORM}.tar.gz"

gh release download "$CODEGRAPH_VERSION" \
  --repo colbymchenry/codegraph \
  --pattern "$CODEGRAPH_ARCHIVE" \
  --pattern SHA256SUMS

grep " $CODEGRAPH_ARCHIVE$" SHA256SUMS | sha256sum --check -
gh attestation verify "$CODEGRAPH_ARCHIVE" \
  --repo colbymchenry/codegraph
tar -xzf "$CODEGRAPH_ARCHIVE"
```

macOS 可將雜湊檢查改為 `shasum -a 256 --check`。解壓後保留完整目錄，將其中的
`bin/` 加入 `PATH`；不要只搬走啟動程式，因為它需要同一 bundle 內的執行環境與
原生函式庫。

### 互動式安裝程式的影響

```bash
codegraph install
```

安裝程式可能執行以下寫入：

- 把 CLI 放進 `PATH` 可見的位置。
- 修改選定 Agent 的 MCP 設定。
- 加入 Agent 指令片段。
- 為部分 Agent 寫入自動允許的工具權限。

受控環境先使用唯讀輸出，再人工合併：

```bash
codegraph install --print-config codex
codegraph install --print-config claude
codegraph install --print-config opencode
```

`--print-config` 不會寫入設定。若仍要執行安裝程式，先備份設定並使用
`--location=local`、明確的 `--target` 和 `--no-permissions`，不要依賴 `--yes` 的全域
預設值。

## 建立專案索引

每個 checkout 或 worktree 都有自己的 `.codegraph/`：

```bash
project_path=/absolute/path/to/project

codegraph init "$project_path"
codegraph status "$project_path"
```

索引是可重建的本機產物，不應提交或同步。若團隊尚未決定是否修改 `.gitignore`，可先
加入 repo 本機排除規則：

```bash
exclude_file=$(git -C "$project_path" rev-parse --git-path info/exclude)
grep -qxF '.codegraph/' "$exclude_file" ||
  printf '%s\n' '.codegraph/' >> "$exclude_file"
git -C "$project_path" status --short
```

不同機器、作業系統與 worktree 不共用 `.codegraph/`。跨機同步原始碼時，讓每台機器
自行重建索引。

## 控制索引範圍

CodeGraph 預設排除 `.gitignore`、常見相依套件／建置／快取目錄及大於 1 MB 的檔案。
已提交的檔案不會因為含有敏感內容就自動排除；初始化前仍要檢查 `git ls-files`。

需要排除已提交目錄時，在專案根目錄建立 `codegraph.json`：

```json
{
  "exclude": [
    "generated/",
    "fixtures/private/",
    "**/vendor/**"
  ]
}
```

非標準副檔名可以映射到支援語言：

```json
{
  "extensions": {
    ".template": "php",
    ".script": "lua"
  }
}
```

變更 `codegraph.json` 後重新建立完整索引：

```bash
codegraph index "$project_path" --force
```

## CLI 使用方式

`query`、`explore`、`callers`、`callees`、`impact` 與 `affected` 都接受
`--path`。跨 repo 使用時應明確傳入目標路徑；省略時才使用目前工作目錄：

```bash
project_path=/absolute/path/to/project
export CODEGRAPH_TELEMETRY=0
export CODEGRAPH_NO_UPDATE_CHECK=1

codegraph status "$project_path"
codegraph sync "$project_path"
codegraph explore --path "$project_path" \
  "trace an HTTP request from route to persistence"
```

常用指令：

| 指令 | 用途 |
|------|------|
| `codegraph query --path <path> <search> --json` | 搜尋符號 |
| `codegraph explore --path <path> <question>` | 取得相關原始碼、關係與影響摘要 |
| `codegraph callers --path <path> <symbol> --json` | 查呼叫者 |
| `codegraph callees --path <path> <symbol> --json` | 查被呼叫函式 |
| `codegraph impact --path <path> <symbol> --depth 2 --json` | 查變更影響範圍 |
| `codegraph affected --path <path> --stdin --quiet` | 由檔案清單找可能受影響的測試 |

CLI 模式的固定順序是 `status → sync → query/explore`。不要拿舊索引結果當成目前
checkout 的證據。

## MCP 設定

### Codex

可以放在使用者層或 trusted project 的 `.codex/config.toml`：

```toml
[mcp_servers.codegraph]
command = "codegraph"
args = ["serve", "--mcp"]

[mcp_servers.codegraph.env]
CODEGRAPH_TELEMETRY = "0"
CODEGRAPH_NO_UPDATE_CHECK = "1"
```

### Claude Code

在 MCP 設定的 `mcpServers` 內加入：

```json
{
  "codegraph": {
    "type": "stdio",
    "command": "codegraph",
    "args": ["serve", "--mcp"],
    "env": {
      "CODEGRAPH_TELEMETRY": "0",
      "CODEGRAPH_NO_UPDATE_CHECK": "1"
    }
  }
}
```

### OpenCode

在設定的 `mcp` 內加入：

```json
{
  "codegraph": {
    "type": "local",
    "command": ["codegraph", "serve", "--mcp"],
    "environment": {
      "CODEGRAPH_TELEMETRY": "0",
      "CODEGRAPH_NO_UPDATE_CHECK": "1"
    },
    "enabled": true
  }
}
```

重新啟動 Agent 後，預設只會看到 `codegraph_explore`。這通常已足夠；不要為了工具
數量而啟用全部低階工具。確實需要時，才設定 `CODEGRAPH_MCP_TOOLS`。

### 同一段對話查多個 repo

MCP tool 接受 `projectPath`。Agent 可以從控制 repo 的對話查另一個已索引 repo，無須
替每個 repo 建立一套 MCP server：

```text
使用 CodeGraph 說明認證流程，projectPath=/absolute/path/to/service
```

每個 `projectPath` 仍對應獨立 SQLite DB。CodeGraph 不會自動建立兩個 repo 之間的
圖譜關係；跨 repo 的契約要分別查詢後再核對。

## 隱私與版本控制

CodeGraph 的原始碼、查詢與圖譜留在本機，但 telemetry 預設可由安裝程式開啟，
MCP server 另有每日版本檢查。需要完全停用時設定：

```bash
export CODEGRAPH_TELEMETRY=0
export CODEGRAPH_NO_UPDATE_CHECK=1
```

`DO_NOT_TRACK=1` 也會同時停用兩者。驗證目前決策來源：

```bash
codegraph telemetry status
```

索引之前要排除憑證、個資、客戶資料、資料庫 dump 與其他不應進入開發工具的內容。
作業系統檔案權限才是存取邊界；MCP 的提示文字不是權限控制。

## 驗證

安裝和設定完成後，依序確認：

```bash
codegraph version
project_path=/absolute/path/to/project
codegraph status "$project_path"
codegraph sync "$project_path"
codegraph query --path "$project_path" "KnownSymbol" --json
codegraph explore --path "$project_path" \
  "explain the flow around KnownSymbol"
```

驗收條件：

- `status` 指向正確 repo，檔案數與語言合理。
- 修改檔案後，CLI `sync` 或 MCP watcher 能更新結果。
- `git status --short` 沒有把 `.codegraph/` 納入變更。
- 已知呼叫鏈能找到，刻意設計的反例不會被錯誤連結。
- Agent 能區分圖譜結果、原始碼、Git 歷史與執行狀態。

## 移除與回復

只移除單一專案索引：

```bash
codegraph uninit /absolute/path/to/project
```

移除 Agent 設定但保留 CLI：

```bash
codegraph uninstall --keep-cli
```

受控環境若是人工合併 MCP 設定，回復時也應人工移除 `codegraph` 設定區塊，再用 Agent 的
MCP 清單命令確認 server 已消失。最後依原本的 npm 或 release 安裝方式移除 CLI。

## 疑難排解

| 問題 | 原因 | 處理方式 |
|------|------|----------|
| `CodeGraph not initialized` | 目標 repo 沒有索引 | 在正確 repo 執行 `codegraph init` |
| 結果沒有最新修改 | CLI 沒有同步，或 watcher 正在等待防抖時間 | 執行 `codegraph status`、`codegraph sync`；MCP 回覆有新鮮度提示時直接讀原始碼 |
| `database is locked` | SQLite/WAL、非本機磁碟或異常中止 | 確認 DB 在本機磁碟；先查 daemon 與 status，不直接刪 lock |
| 找不到符號 | 語言、副檔名、忽略規則或動態分派無法解析 | 檢查 `codegraph.json`、忽略規則，並以原始碼搜尋補查 |
| MCP 找不到第二個 repo | `projectPath` 錯誤或尚未初始化 | 確認絕對路徑並執行 `codegraph status <path>` |
| Agent 過度相信圖譜 | MCP 內建指引偏向直接採用結果 | 在專案規則定義需要原始碼、測試或 Git 交叉驗證的情境 |

## 相關資源

- [CodeGraph README](https://github.com/colbymchenry/codegraph/blob/main/README.md)
- [CodeGraph releases](https://github.com/colbymchenry/codegraph/releases)
- [Telemetry contract](https://github.com/colbymchenry/codegraph/blob/main/TELEMETRY.md)
- [GitHub 發行產物證明](https://docs.github.com/en/actions/security-for-github-actions/using-artifact-attestations)
- [MCP Server 設定指南](../MCP-SERVER-GUIDE.md)

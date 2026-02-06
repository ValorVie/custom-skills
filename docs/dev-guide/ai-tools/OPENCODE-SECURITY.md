# OpenCode 資安設定指南

本指南說明如何設定 OpenCode 的檔案存取限制與安全防護，重點放在 `permission` 權限模型、拒讀敏感檔案、限制危險指令，以及團隊可落地的最佳實踐設定。

---

## 快速參考

| 防護層級 | 機制 | 適用範圍 | 可靠性 |
|----------|------|----------|--------|
| `permission.read` / `permission.edit` | 阻止讀取或修改敏感檔案 | 全域與專案 | 高 |
| `permission.bash` | 限制危險 shell 指令 | 全域與專案 | 高 |
| `permission.* = ask` | 預設先詢問再執行 | 全域與專案 | 中高 |
| `external_directory` | 限制工作目錄外存取 | 全域與專案 | 中高 |
| Agent 層 permission 覆寫 | 依 agent 身分套用更嚴格規則 | 指定 agent | 中高 |

---

## 設定層級與優先順序

OpenCode 設定是「合併」而非整份覆蓋，後載入來源會覆蓋衝突鍵值。

| 層級 | 位置 | 適用範圍 | 優先順序 |
|------|------|----------|----------|
| Remote config | `.well-known/opencode` | 組織預設 | 低 |
| Global config | `~/.config/opencode/opencode.json` | 個人所有專案 | 中 |
| Custom config | `OPENCODE_CONFIG` | 臨時覆寫 | 中高 |
| Project config | `opencode.json`（專案根目錄） | 當前專案 | 高 |
| Inline config | `OPENCODE_CONFIG_CONTENT` | 當前執行 | 最高 |

> 實務上建議：敏感檔案拒讀先放 Global，再由 Project 補充更嚴格規則。

---

## 權限模型（permission）

每條規則只能是以下三種動作：

- `allow`：直接允許
- `ask`：先詢問
- `deny`：直接拒絕

### 核心原則

1. 先用 catch-all（`"*"`）定基準
2. 再加特定 allow/deny 規則
3. 規則比對採「最後一條命中者優先」

### 常見可控鍵

- `read`：讀檔（可依路徑比對）
- `edit`：所有檔案修改（包含 `write`/`patch`/`multiedit`）
- `bash`：shell 指令（可依命令樣式比對）
- `external_directory`：存取工作目錄外路徑
- `task`：啟動 subagent
- `webfetch` / `websearch`：網路讀取與搜尋

---

## 檔案存取限制（重點）

OpenCode 可直接拒絕讀取敏感檔案，適合用於 API key、金鑰、憑證與 secrets 目錄。

### 全域拒讀範例

```json
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "read": {
      "*": "allow",
      "*.env": "deny",
      "*.env.*": "deny",
      "*.env.example": "allow",
      "~/.ssh/**": "deny",
      "~/.aws/**": "deny",
      "**/secrets/**": "deny",
      "**/*.pem": "deny",
      "**/*.key": "deny",
      "**/credentials.json": "deny"
    }
  }
}
```

### 重要注意

- `read` 擋不住 `bash`：若只擋 `read`，仍可能透過 `bash` 間接讀取敏感檔案。
- 因此需搭配 `permission.bash` 規則一起設計。

---

## 危險 Bash 指令限制

建議同時限制外傳、破壞與高風險系統操作。

```json
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "bash": {
      "*": "ask",
      "git status*": "allow",
      "git diff*": "allow",
      "git log*": "allow",
      "npm test*": "allow",
      "npm run lint*": "allow",
      "npm run build*": "allow",
      "curl *": "deny",
      "wget *": "deny",
      "ssh *": "deny",
      "scp *": "deny",
      "cat *.env*": "deny",
      "cat ~/.ssh/*": "deny",
      "rm -rf *": "deny",
      "dd *": "deny",
      "mkfs *": "deny"
    }
  }
}
```

---

## Agent 權限隔離

OpenCode 支援針對 agent 覆寫權限。適合建立「唯讀審查 agent」或「禁網文件 agent」。

```json
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "edit": "ask",
    "bash": "ask"
  },
  "agent": {
    "review": {
      "permission": {
        "read": "allow",
        "edit": "deny",
        "bash": "deny",
        "webfetch": "deny"
      }
    }
  }
}
```

---

## 最佳實踐：可直接使用的基線設定

以下範例採「預設詢問 + 明確拒絕敏感操作 + 最小必要允許」。

```json
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "*": "ask",

    "read": {
      "*": "allow",
      "*.env": "deny",
      "*.env.*": "deny",
      "*.env.example": "allow",
      "~/.ssh/**": "deny",
      "~/.aws/**": "deny",
      "**/secrets/**": "deny",
      "**/*.pem": "deny",
      "**/*.key": "deny",
      "**/credentials.json": "deny"
    },

    "edit": {
      "*": "ask",
      "docker-compose.prod.yml": "deny",
      "**/.github/workflows/**": "ask"
    },

    "bash": {
      "*": "ask",
      "git status*": "allow",
      "git diff*": "allow",
      "git log*": "allow",
      "npm test*": "allow",
      "npm run lint*": "allow",
      "npm run build*": "allow",
      "curl *": "deny",
      "wget *": "deny",
      "ssh *": "deny",
      "scp *": "deny",
      "cat *.env*": "deny",
      "cat ~/.ssh/*": "deny",
      "rm -rf *": "deny",
      "dd *": "deny",
      "mkfs *": "deny"
    },

    "external_directory": {
      "*": "ask",
      "~/projects/personal/**": "allow"
    },

    "task": "ask",
    "webfetch": "ask",
    "websearch": "ask"
  }
}
```

### 這份設定的設計理由

1. 對敏感檔案採明確 deny，而不是只靠習慣避免。
2. 對 shell 採白名單式 allow + 高風險 deny。
3. 對 subagent 與網路工具保留人工確認。
4. 對工作目錄外路徑做額外閘門。

---

## 團隊落地建議

### 最低限度（個人）

- 在 `~/.config/opencode/opencode.json` 設定 `read` 拒讀敏感檔案
- 對 `bash` 設 `ask`

### 標準防護（團隊）

- 專案根目錄提交 `opencode.json`
- 統一 deny 規則（`*.env`、`secrets`、金鑰）
- PR 檢查：確認安全規則未被放寬

### 高度防護（敏感資料）

- `permission` 全面最小授權
- 只給特定 agent 最低必要權限
- 在 CI 或容器化環境執行，避免本機高權限暴露

---

## 已知限制與注意事項

1. `read` 與 `bash` 需同時治理，否則可能出現間接讀取。
2. 規則比對「最後命中優先」，請小心規則順序。
3. 設定會跨層級合併，專案層可能覆蓋全域策略，需定期稽核。
4. OpenCode 預設偏寬鬆，未配置前大多操作是 `allow`。

---

## 參考資源

- [OpenCode Config](https://opencode.ai/docs/config/)
- [OpenCode Permissions](https://opencode.ai/docs/permissions/)
- [OpenCode Tools](https://opencode.ai/docs/tools/)
- [OpenCode Agents](https://opencode.ai/docs/agents/)
- [Oh My OpenCode configurations](https://github.com/code-yeongyu/oh-my-opencode/blob/dev/docs/configurations.md)

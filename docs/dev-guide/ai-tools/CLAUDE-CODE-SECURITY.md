# Claude Code 資安設定指南

本指南說明如何設定 Claude Code 的檔案存取限制與資安防護，涵蓋權限控制、沙箱隔離、Hooks 安全驗證等常見設定方式。

---

## 快速參考

| 防護層級 | 機制 | 適用範圍 | 可靠性 |
|----------|------|----------|--------|
| 權限規則 `permissions.deny` | 阻止特定工具存取檔案/指令 | 全域或專案 | 中（已知有繞過問題） |
| 沙箱隔離 Sandboxing | OS 層級的檔案系統與網路隔離 | 執行環境 | 高 |
| Hooks 安全驗證 | 自訂腳本攔截危險操作 | 全域或專案 | 中高 |
| Docker 容器化 | 完全隔離的執行環境 | 執行環境 | 最高 |

---

## 檔案存取限制

### 設定層級總覽

Claude Code 的設定採用**層疊式優先順序**，企業政策優先權最高：

| 層級 | 檔案位置 | 適用範圍 | 優先順序 |
|------|----------|----------|----------|
| 企業政策 | `managed-settings.json`（管理員部署） | 整個組織 | 最高（不可覆寫） |
| 使用者（全域） | `~/.claude/settings.json` | 所有專案 | 高 |
| 專案（共用） | `.claude/settings.json` | 該專案所有成員 | 中 |
| 專案（個人） | `.claude/settings.local.json` | 僅自己 | 低 |

### 全域檔案存取限制

在 `~/.claude/settings.json` 中設定 `permissions.deny`，可阻止 Claude Code 在所有專案中存取指定檔案：

```json
{
  "permissions": {
    "deny": [
      "Read(.env)",
      "Read(.env.*)",
      "Read(~/.ssh/**)",
      "Read(~/.aws/**)",
      "Read(**/secrets/**)",
      "Read(**/*.pem)",
      "Read(**/*.key)",
      "Read(**/credentials.json)",
      "Edit(.env*)",
      "Edit(secrets.yaml)"
    ]
  }
}
```

**語法說明：**
- `*` — 匹配任意字元（不跨目錄）
- `**` — 遞迴匹配所有子目錄
- 格式為 `工具名稱(路徑模式)`，支援 `Read`、`Edit`、`Write`、`Bash` 等工具

### 專案層級檔案存取限制

在專案根目錄的 `.claude/settings.json` 中設定，與團隊共用：

```json
{
  "permissions": {
    "deny": [
      "Read(.env)",
      "Read(.env.*)",
      "Read(./config/secrets/**)",
      "Edit(docker-compose.prod.yml)"
    ]
  }
}
```

### `.claudeignore`

專案根目錄可放置 `.claudeignore` 檔案，語法同 `.gitignore`：

```
.env
.env.*
secrets/
*.pem
*.key
```

> **注意**：`.claudeignore` **僅支援專案層級**，沒有全域設定方式。且近期有[報導](https://www.theregister.com/2026/01/28/claude_code_ai_secrets_files/)指出其存在可被繞過的問題，**不建議作為唯一防線**。

---

## 權限允許清單

建議採用**允許清單優先**策略，僅開放已知安全的操作：

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test)",
      "Bash(npm run build)",
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git log *)"
    ],
    "deny": [
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(ssh *)",
      "Bash(rm -rf *)",
      "Read(.env)",
      "Read(.env.*)",
      "Read(~/.ssh/**)"
    ]
  }
}
```

---

## 危險 Bash 指令限制

阻止可能造成破壞或資料外洩的指令：

```json
{
  "permissions": {
    "deny": [
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(ssh *)",
      "Bash(scp *)",
      "Bash(rm -rf *)",
      "Bash(chmod 777 *)",
      "Bash(> /dev/sda*)",
      "Bash(dd *)",
      "Bash(mkfs *)"
    ]
  }
}
```

> **重要**：`deny` 規則僅阻止對應的工具呼叫。例如 `Read(.env)` 只阻止 Read 工具，Claude 仍可能透過 `Bash(cat .env)` 讀取。需同時設定 `Bash(cat .env)` 的 deny 規則或使用沙箱隔離。

---

## 沙箱隔離（Sandboxing）

Claude Code 內建沙箱功能，基於 OS 層級原語（Linux Bubblewrap、macOS Seatbelt）提供：

- **檔案系統隔離** — 限制 Claude 只能存取指定目錄
- **網路隔離** — 限制 Claude 只能連接至核准的伺服器

### 為何兩層都重要

| 缺少的隔離 | 風險 |
|------------|------|
| 無網路隔離 | 被注入的 Claude 可外洩 SSH 金鑰等敏感檔案 |
| 無檔案系統隔離 | 被注入的 Claude 可植入後門至系統資源 |

沙箱設定的詳細說明請參考 [Anthropic 官方沙箱文件](https://code.claude.com/docs/en/sandboxing)。

---

## Hooks 安全驗證

透過 Hooks 機制，可在工具執行前後加入自訂安全檢查腳本。

### 設定位置

- 全域：`~/.claude/settings.json` 中的 `hooks` 區段
- 專案：`.claude/settings.json` 中的 `hooks` 區段

### 範例：阻擋危險指令與敏感檔案存取

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/security-validator.py"
          }
        ]
      }
    ]
  }
}
```

安全驗證腳本可檢查：
- 是否嘗試存取敏感路徑（`~/.ssh/`、`~/.aws/`）
- 是否執行破壞性指令（`rm -rf`、`chmod 777`）
- 是否嘗試網路外洩（`curl`、`wget` 搭配敏感檔案路徑）

---

## Docker 容器化執行

在需要最高安全性的場景下，建議在 Docker 容器中執行 Claude Code：

```bash
# 基本概念：限制可存取的檔案與網路
docker run -it \
  -v $(pwd):/workspace:rw \
  -v ~/.claude:/home/user/.claude:ro \
  --network=none \
  claude-code-image
```

優點：
- 完全的檔案系統隔離（僅掛載工作目錄）
- 可完全禁用網路（`--network=none`）
- 即使所有 deny 規則被繞過，容器外的檔案仍不可存取

---

## 建議的安全設定組合

### 最低限度防護

適用於個人開發環境：

```json
// ~/.claude/settings.json
{
  "permissions": {
    "deny": [
      "Read(.env)",
      "Read(.env.*)",
      "Read(~/.ssh/**)",
      "Read(~/.aws/**)",
      "Read(**/*.pem)",
      "Read(**/*.key)"
    ]
  }
}
```

### 標準防護

適用於團隊專案：

```json
// .claude/settings.json（專案共用）
{
  "permissions": {
    "allow": [
      "Bash(npm run *)",
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git log *)"
    ],
    "deny": [
      "Read(.env)",
      "Read(.env.*)",
      "Read(**/secrets/**)",
      "Bash(curl *)",
      "Bash(wget *)",
      "Edit(docker-compose.prod.yml)"
    ]
  }
}
```

### 高度防護

適用於處理敏感資料的環境，結合沙箱 + Hooks + deny 規則 + Docker。

---

## 已知限制與注意事項

1. **deny 規則僅限對應工具**：`Read(.env)` 不會阻止 `Bash(cat .env)`，需分別設定
2. **`.claudeignore` 存在繞過風險**：不應作為唯一防線，建議搭配 `permissions.deny`
3. **deny 規則穩定性**：歷史上曾有 [deny 規則未正確執行的問題](https://github.com/anthropics/claude-code/issues/6699)，建議定期測試驗證
4. **路徑語法**：絕對路徑可能需要使用 `//` 開頭而非 `/`，請以實際測試為準
5. **`--dangerously-skip-permissions`**：此旗標會繞過所有安全檢查，僅應在隔離的自動化環境中使用
6. **定期更新**：Claude Code 已有多個 CVE，許多與權限繞過相關，務必保持更新

---

## 參考資源

- [Claude Code Settings 官方文件](https://code.claude.com/docs/en/settings)
- [Claude Code Sandboxing 官方文件](https://code.claude.com/docs/en/sandboxing)
- [Anthropic 沙箱工程文章](https://www.anthropic.com/engineering/claude-code-sandboxing)
- [Claude Code 權限完整指南](https://www.eesel.ai/blog/claude-code-permissions)
- [Claude Code 安全最佳實踐（Backslash）](https://www.backslash.security/blog/claude-code-security-best-practices)
- [安全驗證 Hook 範例](https://gist.github.com/sgasser/efeb186bad7e68c146d6692ec05c1a57)

# documentation Spec Delta

## MODIFIED Requirements

### Requirement: README Documentation (README 文件)

README MUST (必須) 包含使用說明。

> **變更說明**：更新指令範例，將 `maintain` 改為 `update`。

#### Scenario: 指令說明表格

給定 README.md 檔案
則指令總覽表格應該包含：

| 指令 | 說明 |
|------|------|
| `ai-dev install` | 首次安裝 AI 開發環境 |
| `ai-dev update` | 每日更新：更新工具並同步設定 |
| `ai-dev project init` | 初始化專案（openspec + uds） |
| `ai-dev project update` | 更新專案配置 |
| `ai-dev status` | 檢查環境狀態與工具版本 |
| `ai-dev list` | 列出已安裝的 Skills、Commands、Agents |
| `ai-dev toggle` | 啟用/停用特定資源 |
| `ai-dev tui` | 啟動互動式終端介面 |

#### Scenario: 每日更新章節

給定 README.md 檔案
則「每日維護」章節應該顯示 `ai-dev update` 指令範例

# Proposal: rename-maintain-to-update

## Summary

將 `ai-dev maintain` 指令重新命名為 `ai-dev update`，使指令名稱更符合其「更新」的語意，並同步更新所有相關文檔。

## Background

目前的 `maintain` 指令實際執行的是「更新」操作：
1. 更新全域 NPM 套件
2. 拉取 Git 儲存庫最新變更
3. 重新同步 Skills

「update」比「maintain」更直觀地表達這些操作的本質，且與常見的 CLI 慣例一致（如 `apt update`、`brew update`、`uds update`）。

## Scope

### 程式碼變更

| 檔案 | 變更內容 |
|------|----------|
| `script/commands/maintain.py` | 重新命名為 `update.py`，函式 `maintain()` 改為 `update()` |
| `script/main.py` | 更新 import 與 command 註冊 |
| `script/tui/app.py` | 按鈕標籤 "Maintain" 改為 "Update"，command 參數更新 |

### 文檔變更

| 檔案 | 變更內容 |
|------|----------|
| `README.md` | 所有 `ai-dev maintain` 改為 `ai-dev update` |
| `docs/AI開發環境設定指南.md` | 所有 `maintain` 相關說明改為 `update` |
| `CHANGELOG.md` | 新增變更記錄 |

### 規格變更

| 檔案 | 變更內容 |
|------|----------|
| `openspec/specs/setup-script/spec.md` | `maintain` 改為 `update` |
| `openspec/specs/cli-distribution/spec.md` | `maintain` 改為 `update` |
| `openspec/specs/skill-npm-integration/spec.md` | `maintain` 改為 `update` |
| `openspec/specs/documentation/spec.md` | `maintain` 改為 `update` |

## Out of Scope

- 不變更 `install`、`status`、`list`、`toggle`、`tui`、`project` 等其他指令
- 不變更 `code-simplifier` 等 skill/agent 中使用的 "maintain" 一詞（指「維護」程式碼品質，非指令名稱）
- 不變更 `openspec/changes/archive/` 中的歷史記錄

## Dependencies

無外部依賴。

## Risks

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 使用者習慣舊指令 | 低 | `maintain` 為內部工具，使用者數量有限；可考慮加入 alias 過渡 |
| 遺漏更新某處文檔 | 低 | 透過 `rg maintain` 全面搜尋確認 |

## Success Criteria

1. `ai-dev update` 指令正常運作，行為與原 `maintain` 完全相同
2. `ai-dev maintain` 不再存在（或作為 alias）
3. 所有文檔中的 `maintain` 相關說明已更新為 `update`
4. 規格文件已同步更新
5. TUI 介面顯示 "Update" 按鈕

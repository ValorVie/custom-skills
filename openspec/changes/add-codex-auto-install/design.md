## Context

### 背景

ai-dev 是一個統一的 AI 開發環境設定 CLI 工具，負責安裝和管理多個 AI 開發工具（Claude Code、OpenCode、Codex、Gemini CLI 等）。目前，`ai-dev install` 和 `update` 指令會自動安裝/更新 NPM 套件，但 Codex CLI 因為改用 Bun 安裝方式，尚未被納入自動管理。

### 當前狀態

- NPM 套件安裝邏輯已成熟 (`NPM_PACKAGES` 配置在 `shared.py`)
- Claude Code 的檢查/提示模式可作為參考（顯示安裝指引但不強制安裝）
- Bun 套件管理與 NPM 類似，但指令和全域套件查詢方式不同

### 約束條件

1. **向後相容**：不能破壞現有的 NPM 套件安裝流程
2. **漸進式採用**：不自動安裝 Bun，僅提供指引
3. **跨平台**：支援 macOS、Linux、Windows
4. **錯誤處理**：使用現有的 `run_command` 機制

## Goals / Non-Goals

**Goals:**
- 在 `ai-dev install` 時自動安裝 Codex CLI（若 Bun 已安裝）
- 在 `ai-dev update` 時自動更新 Codex CLI
- 提供清晰的 Bun 安裝指引（當 Bun 未安裝時）
- 新增 `--skip-bun` 參數允許跳過 Bun 套件管理
- 維持與現有 NPM 安裝流程的一致性（UX 和程式碼結構）

**Non-Goals:**
- 不自動安裝 Bun 執行環境
- 不改變 Codex 的設定或配置管理
- 不支援 Bun 套件的其他功能（僅限全域安裝）
- 不取代 NPM 套件管理（兩者並存）

## Decisions

### 決策 1：Bun 套件配置獨立於 NPM 套件

**選擇**：新增獨立的 `BUN_PACKAGES` 列表，而非擴充 `NPM_PACKAGES`

**理由**：
- Bun 和 NPM 是不同的套件管理器，安裝指令不同 (`bun install` vs `npm install`)
- 分離配置允許獨立控制（`--skip-npm` 和 `--skip-bun` 分開）
- 未來若需更多 Bun 套件，無需修改現有 NPM 邏輯

**替代方案**：統一管理所有套件（ rejected：會增加複雜度，且 Bun 和 NPM 的套件生態不完全相容）

### 決策 2：Bun 未安裝時顯示指引而非中斷

**選擇**：當 Bun 未安裝時，顯示安裝指引並繼續執行其他步驟

**理由**：
- 與 Claude Code 的處理方式保持一致（檢查但不強制）
- Codex 是可選工具，不應阻擋整個安裝流程
- 使用者可能選擇不安裝 Codex

**替代方案**：中斷安裝並要求先安裝 Bun（ rejected：過於強制，違反漸進式採用原則）

### 決策 3：Bun 版本檢查使用 `bun --version`

**選擇**：直接執行 `bun --version` 取得版本資訊

**理由**：
- Bun 官方支援 `--version` 參數
- 輸出格式穩定（純版本號字串）
- 與現有 `get_npm_package_version` 模式一致

**替代方案**：解析 `bun pm ls -g` 輸出（ rejected：過於複雜，且版本資訊可能不易取得）

### 決策 4：將 Bun 工具函式放在 `system.py`

**選擇**：在 `script/utils/system.py` 新增 Bun 相關函式

**理由**：
- `system.py` 已包含 `check_command_exists` 和 `run_command`
- Bun 檢查屬於系統/環境檢查範疇
- 保持 `shared.py` 專注於配置常數

**替代方案**：新增獨立的 `bun.py` 模組（ rejected：過度設計，目前僅需 2-3 個函式）

## Risks / Trade-offs

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| **Bun 未安裝** | 中 | 顯示清晰指引，繼續執行其他步驟 |
| **Bun 指令不存在** | 低 | 使用 `check_command_exists` 預先檢查，避免拋出異常 |
| **與現有 Codex 安裝衝突** | 低 | Bun 會覆蓋/更新現有安裝，行為與 npm 類似；Codex 官方推薦使用 Bun |
| **網路問題導致安裝失敗** | 低 | 使用現有的 `run_command` 錯誤處理，不中斷整個流程 |
| **Bun 版本變更影響輸出格式** | 低 | 版本解析邏輯簡單（純字串），即使格式變更也不會嚴重影響功能 |
| **Windows 支援問題** | 中 | Bun 官方支援 Windows；使用 PowerShell 指令符合 Windows 慣例 |

### Trade-offs

- **額外依賴**：新增 Bun 相關功能需要使用者安裝 Bun，但這是可選的
- **維護成本**：需要追蹤 Bun 和 Codex 的更新，但變更不頻繁
- **程式碼複雜度**：新增約 100-150 行程式碼，但結構清晰易於維護

## Implementation Plan

### Phase 1: 基礎設施 (30 分鐘)
1. 在 `shared.py` 新增 `BUN_PACKAGES` 常數
2. 在 `system.py` 新增 Bun 檢查函式
3. 匯出 `BUN_PACKAGES` 到 `shared.py` 的 `__all__`

### Phase 2: Install 指令 (1 小時)
1. 修改 `install.py` 新增 `--skip-bun` 參數
2. 實作 Bun 檢查和安裝邏輯
3. 處理 Bun 未安裝時的提示訊息

### Phase 3: Update 指令 (30 分鐘)
1. 修改 `update.py` 新增 `--skip-bun` 參數
2. 實作 Bun 套件更新邏輯

### Phase 4: 測試與驗證 (1-2 小時)
1. 測試 `ai-dev install` 各種情境
2. 測試 `ai-dev update` 各種情境
3. 測試 `--skip-bun` 參數

### Phase 5: 文件更新 (30 分鐘)
1. 更新 `README.md`
2. 更新 `docs/AI開發環境設定指南.md`

## Open Questions

1. **是否需要支援多個 Bun 套件？**
   - 目前只有 `@openai/codex`，但未來可能需要更多
   - 設計已考慮擴充性（`BUN_PACKAGES` 是列表）

2. **Bun 版本要求？**
   - 目前未定義最低版本要求
   - 假設使用者安裝的 Bun 版本足夠新（Codex 需要較新的 Bun）

3. **是否需要快取 Bun 檢查結果？**
   - 目前每次執行都檢查，對效能影響極小
   - 若未來檢查邏輯變複雜，可考慮快取

## Migration Plan

此變更為**新增功能**，無需遷移現有資料或配置。

### 部署步驟
1. 合併 PR
2. 使用者執行 `ai-dev update` 更新 CLI 工具
3. 下次執行 `ai-dev install` 或 `update` 時自動生效

### 回滾策略
- 若發現問題，可透過 `--skip-bun` 參數暫時停用
- 可快速移除 `BUN_PACKAGES` 相關邏輯

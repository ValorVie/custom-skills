## 1. 基礎設施

- [x] 1.1 在 `script/utils/shared.py` 新增 `BUN_PACKAGES` 常數
- [x] 1.2 在 `script/utils/system.py` 新增 `check_bun_installed()` 函式
- [x] 1.3 在 `script/utils/system.py` 新增 `get_bun_version()` 函式
- [x] 1.4 在 `script/utils/system.py` 新增 `get_bun_package_version()` 函式
- [x] 1.5 將 `BUN_PACKAGES` 和 Bun 相關函式匯出至 `shared.py` 的 `__all__`

## 2. Install 指令強化

- [x] 2.1 修改 `script/commands/install.py` 新增 `--skip-bun` 參數
- [x] 2.2 實作 Bun 安裝檢查邏輯（顯示版本或提示未安裝）
- [x] 2.3 實作 Bun 未安裝時的安裝指引顯示
- [x] 2.4 實作 Bun 套件安裝迴圈（含版本檢查）
- [x] 2.5 確保 `--skip-bun` 參數正確跳過所有 Bun 相關操作

## 3. Update 指令強化

- [x] 3.1 修改 `script/commands/update.py` 新增 `--skip-bun` 參數
- [x] 3.2 實作 Bun 套件更新邏輯
- [x] 3.3 實作 Bun 未安裝時的提示訊息
- [x] 3.4 確保 `--skip-bun` 參數正確跳過所有 Bun 相關操作

## 4. 測試驗證

- [x] 4.1 測試 `ai-dev install` 在 Bun 已安裝時的行為
- [x] 4.2 測試 `ai-dev install` 在 Bun 未安裝時的行為
- [x] 4.3 測試 `ai-dev install --skip-bun` 的行為
- [x] 4.4 測試 `ai-dev update` 在 Bun 已安裝時的行為
- [x] 4.5 測試 `ai-dev update` 在 Bun 未安裝時的行為
- [x] 4.6 測試 `ai-dev update --skip-bun` 的行為
- [x] 4.7 驗證現有的 NPM 套件安裝不受影響

## 5. 文件更新

- [x] 5.1 更新 `README.md` 中的安裝說明（提及 Bun 和 Codex）
- [x] 5.2 更新 `docs/AI開發環境設定指南.md` 中的 Codex 章節
- [x] 5.3 驗證 `ai-dev install --help` 輸出包含 `--skip-bun`
- [x] 5.4 驗證 `ai-dev update --help` 輸出包含 `--skip-bun`

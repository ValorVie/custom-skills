## 1. 建立 CLI 命令

- [x] 1.1 建立 `script/commands/derive_tests.py`
- [x] 1.2 實作 `find_spec_files()` - 搜尋 specs 檔案（支援目錄和單一檔案）
- [x] 1.3 實作 `derive-tests` 命令 - 讀取並輸出 specs 內容
- [x] 1.4 實作路徑不存在時的錯誤處理
- [x] 1.5 整合到 `script/main.py`

## 2. 建立 Claude Code 命令

- [x] 2.1 建立 `commands/claude/custom-skills-derive-tests.md`
- [x] 2.2 定義 Step 1: 執行 CLI 讀取 specs
- [x] 2.3 定義 Step 2: AI 理解 WHEN/THEN 場景語義
- [x] 2.4 定義 Step 3: AI 讀取專案程式碼結構
- [x] 2.5 定義 Step 4: AI 生成測試程式碼（AAA 格式）
- [x] 2.6 定義 Step 5: AI 決定檔案位置並寫入
- [x] 2.7 定義生成結果摘要格式

## 3. 驗證

- [x] 3.1 測試 `ai-dev derive-tests` 讀取目錄
- [x] 3.2 測試 `ai-dev derive-tests` 讀取單一檔案
- [x] 3.3 測試路徑不存在時的錯誤處理
- [x] 3.4 測試 `/custom-skills-derive-tests` 端對端流程

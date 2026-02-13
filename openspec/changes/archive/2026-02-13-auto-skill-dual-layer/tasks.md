## 1. inject-knowledge-index.py 重寫

- [x] 1.1 將 `find_skill_root()` 替換為 `find_all_skill_roots()`，回傳 `dict` 包含 user/project 兩個路徑
- [x] 1.2 新增 `merge_knowledge_base(roots)` 函式，以 `id` 為鍵合併雙層 categories 並記錄各層 count
- [x] 1.3 新增 `merge_experience(roots)` 函式，以 `skillId` 為鍵合併雙層 skills 並記錄各層 count
- [x] 1.4 新增 `format_count_annotation(counts)` 函式，產生來源標註文字（單層/雙層格式）
- [x] 1.5 更新 `main()` 使用新的合併函式產生帶標註的輸出

## 2. SKILL.md 更新

- [x] 2.1 Step 0 快取新增 `skill_roots` 變數定義（user/project 路徑）
- [x] 2.2 Step 3 跨技能經驗讀取改為雙層：讀取兩個層級的索引和 .md，標註來源
- [x] 2.3 Step 4 知識庫讀取改為雙層：讀取兩個層級的索引和 .md，標註來源
- [x] 2.4 Step 5 記錄流程新增層級選擇詢問（使用者層級/專案層級）
- [x] 2.5 Step 5 新增專案層級目錄初始化流程（從 `~/.config/custom-skills/skills/auto-skill/` 複製）
- [x] 2.6 存儲路徑章節改為雙層級結構說明，包含層級選擇建議

## 3. 驗證

- [x] 3.1 直接執行 inject 腳本確認輸出包含 `[使用者]` / `[專案]` 標註
- [x] 3.2 測試僅一個層級存在時的輸出格式正確
- [x] 3.3 測試兩層 count 都為 0 時不輸出該分類
- [x] 3.4 測試 JSON 解析失敗時靜默跳過不影響另一層級

## 1. 插件結構建立

- [x] 1.1 建立 `plugins/auto-skill-hooks/.claude-plugin/plugin.json`（name: auto-skill-hooks, version: 1.0.0）
- [x] 1.2 建立 `plugins/auto-skill-hooks/hooks/hooks.json`（SessionStart hook 配置）
- [x] 1.3 建立 `plugins/auto-skill-hooks/scripts/` 目錄

## 2. Hook 腳本實作

- [x] 2.1 建立 `inject-knowledge-index.py`：讀取 knowledge-base/_index.json 和 experience/_index.json，過濾空條目，輸出索引摘要
- [x] 2.2 手動測試腳本：`python3 plugins/auto-skill-hooks/scripts/inject-knowledge-index.py`，確認輸出格式正確

## 3. 插件啟用

- [x] 3.1 在 `~/.claude/settings.json` 新增 `"auto-skill-hooks@custom-skills": true`

## 4. 全域 CLAUDE.md 建立

- [x] 4.1 建立 `~/.claude/CLAUDE.md` 檔案（若不存在）
- [x] 4.2 寫入「知識庫與經驗協議」區塊，包含讀取規則、記錄規則、路徑指引

## 5. SKILL.md 精簡

- [x] 5.1 移除 Step 0.5（自動加固全局規則）
- [x] 5.2 移除 Step 0（對話內快取定義）
- [x] 5.3 移除 Step 1（逐回合關鍵詞抽取）
- [x] 5.4 移除 Step 2（話題切換偵測）
- [x] 5.5 簡化 Step 3-4 為指向 CLAUDE.md 的說明
- [x] 5.6 移除 QMD 升級章節
- [x] 5.7 保留並整理：條目格式、記錄判斷準則、存儲路徑、動態分類

## 6. 驗證

- [ ] 6.1 啟動新 Claude Code 對話，確認 SessionStart hook 輸出索引內容
- [ ] 6.2 在 knowledge-base 中手動新增一筆測試條目，確認下次對話可見
- [ ] 6.3 確認 Claude 在相關任務中能根據索引讀取對應 .md 檔案
- [ ] 6.4 確認 /auto-skill 手動呼叫仍可正常運作
- [ ] 6.5 確認停用 auto-skill-hooks 後 ecc-hooks 不受影響

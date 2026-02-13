## 1. Clone Policy 核心機制

- [x] 1.1 在 `script/utils/shared.py` 新增 `_load_clone_policy(skill_dir: Path) -> dict | None` 函式，讀取並驗證 `.clonepolicy.json`
- [x] 1.2 在 `script/utils/shared.py` 新增 `_merge_index_json(src_file: Path, dst_file: Path) -> None` 函式，實作 key-merge 策略（以 `id`/`skillId` 為 key 合併陣列）
- [x] 1.3 在 `script/utils/shared.py` 新增 `_copy_skill_with_policy(src: Path, dst: Path, policy: dict, force: bool, skip_conflicts: bool) -> None` 函式，實作逐檔複製邏輯：
  - 遍歷來源目錄所有檔案
  - 依 pattern 匹配決定策略（key-merge / skip-if-exists / default）
  - default 策略：hash 比對 + 互動提示（尊重 `--force` 和 `--skip-conflicts`）
  - 自動排除 `.clonepolicy.json` 本身

## 2. 整合到 _copy_with_log

- [x] 2.1 修改 `_copy_with_log()` 的 skills 複製邏輯（約 L656-666），在 `shutil.copytree` 前檢查 `.clonepolicy.json` 是否存在，若存在則呼叫 `_copy_skill_with_policy`
- [x] 2.2 確保 `--force` 和 `--skip-conflicts` flag 值能傳遞到 `_copy_skill_with_policy`（可能需要修改 `_copy_with_log` 的參數簽名）
- [x] 2.3 含 `.clonepolicy.json` 的 skill 在衝突檢測階段跳過目錄層級檢測（ManifestTracker 仍記錄 hash 用於孤兒清理）

## 3. Auto-skill 配置

- [x] 3.1 建立 `skills/auto-skill/.clonepolicy.json`，內容包含 knowledge-base 和 experience 的保護規則

## 4. 測試驗證

- [x] 4.1 驗證場景：首次 clone auto-skill（目標不存在）→ 所有模板檔案完整複製
- [x] 4.2 驗證場景：再次 clone（目標已有使用者資料）→ knowledge-base/*.md 和 experience/*.md 跳過，_index.json 合併，SKILL.md 提示
- [x] 4.3 驗證場景：上游 _index.json 新增分類 → 合併後目標包含新分類且保留既有 count
- [x] 4.4 驗證場景：無 .clonepolicy.json 的 skill → 行為完全不變
- [x] 4.5 驗證場景：.clonepolicy.json 格式錯誤 → 顯示警告並 fallback 為 copytree
- [x] 4.6 驗證場景：`--force` flag → default 策略直接覆蓋不提示

# Implementation Tasks

## 1. 新增 ECC 路徑函式

- [x] 1.1 在 `script/utils/paths.py` 新增 `get_ecc_dir()` 函式
  - 回傳 `~/.config/everything-claude-code`

## 2. 更新 update 指令

- [x] 2.1 在 `script/commands/update.py` 引入 `get_ecc_dir`
- [x] 2.2 將 `get_ecc_dir()` 加入 `repos` 清單

## 3. 新增更新檢測功能

- [x] 3.1 建立 `check_for_updates(repo: Path, branch: str | None) -> bool` 函式
  - 在 fetch 後，比較 `HEAD` 與 `origin/{branch}` 的 commit
  - 若有差異則回傳 `True`
- [x] 3.2 修改更新迴圈，記錄有更新的儲存庫
- [x] 3.3 在更新完成後顯示有新更新的儲存庫摘要

## 4. 驗證

- [ ] 4.1 手動測試 `ai-dev update` 確認 ECC 被正確更新
- [ ] 4.2 測試更新提示功能顯示正確

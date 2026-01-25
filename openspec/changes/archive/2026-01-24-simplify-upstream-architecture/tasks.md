# Tasks: Simplify Upstream Architecture

## Phase 1: CLI 指令重構

### 1.1 修改 `ai-dev update`
- [x] 移除 `skip_skills` 參數
- [x] 移除 `sync_project` 參數
- [x] 移除 `copy_skills()` 呼叫
- [x] 更新 docstring 說明

**驗證**: `ai-dev update --help` 不再顯示 skills 相關選項 ✓

### 1.2 新增 `ai-dev clone` 指令
- [x] 建立 `script/commands/clone.py`
- [x] 實作 `clone()` 函數呼叫 `copy_skills()`
- [x] 加入 `--sync-project/--no-sync-project` 選項
- [x] 註冊到 main.py

**驗證**: `ai-dev clone --help` 顯示正確說明 ✓

### 1.3 更新 shared.py
- [x] 移除 `sync_repos_to_sources()` 函數
- [x] 移除 `_is_in_custom_skills_project()` 函數（保留於其他用途）
- [x] 移除 `_get_source_path()` 函數
- [x] 移除 `load_upstream_sources()` 函數
- [x] 移除 `get_sources_dir()` 函數
- [x] 還原 `copy_sources_to_custom_skills()` 直接從 `~/.config/` 讀取
- [x] 還原 `copy_skills()` 移除 `sync_sources` 參數

**驗證**: shared.py 無 sources 相關邏輯 ✓

## Phase 2: 清理專案

### 2.1 移除 sources/ 目錄
- [x] 刪除 `sources/` 目錄及所有內容

**驗證**: `sources/` 目錄已刪除 ✓

### 2.2 更新 upstream/sources.yaml
- [x] 移除 `target_dir` 欄位
- [x] 更新註解說明用途（僅用於 skill 追蹤參考）

**驗證**: sources.yaml 格式正確 ✓

## Phase 3: Skill 重新定義

### 3.1 更新 upstream-sync skill
- [x] 重寫 SKILL.md 明確職責
- [x] 移除 `--sync` 選項（不再同步到 sources/）
- [x] 更新工作流程圖
- [x] 更新腳本移除 sources 相關邏輯

**驗證**: 腳本語法正確 ✓

### 3.2 更新 upstream-compare skill
- [ ] 重寫 SKILL.md 明確職責（如有需要）
- [ ] 更新比較腳本從 `~/.config/` 讀取（如有需要）

**驗證**: 待測試

## Phase 4: 重新安裝與測試

### 4.1 更新版本
- [x] 更新 `pyproject.toml` 版本號 (0.7.0)

### 4.2 重新安裝
- [x] 執行 `uv tool install . --force`

### 4.3 整合測試
- [x] `ai-dev --version` 顯示 0.7.0
- [x] `ai-dev update --help` 不顯示 skills 選項
- [x] `ai-dev clone --help` 顯示正確說明
- [ ] `ai-dev update --skip-npm` 只拉取 repo（待用戶測試）
- [ ] `ai-dev clone` 正確分發到各工具目錄（待用戶測試）

## Phase 5: 文件更新

### 5.1 更新 Spec
- [x] 新增 `clone-command` spec
- [x] 新增 `upstream-skills` spec

### 5.2 更新 README
- [ ] 更新使用說明（可選）

---

## Dependencies

```
Phase 1 ──→ Phase 2 ──→ Phase 3 ──→ Phase 4 ──→ Phase 5
   │                        │
   └──────────┬─────────────┘
              │
      可平行執行
```

## Verification Checklist

完成後確認：

- [x] `ai-dev update` 不再分發 skills
- [x] `ai-dev clone` 正確分發 skills（指令存在）
- [x] `sources/` 目錄已刪除
- [x] upstream-sync skill 職責明確
- [ ] 整合測試通過（待用戶測試）

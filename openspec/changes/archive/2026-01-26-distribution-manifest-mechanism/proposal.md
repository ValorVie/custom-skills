## Why

分發工具（`ai-dev clone`）使用 `shutil.copytree(dirs_exist_ok=True)` 複製檔案，這種「覆蓋/合併」模式不會刪除目標目錄中已存在但來源沒有的檔案。當工具重命名（如 `git-commit-custom` → `custom-skills-git-commit`）後，舊名稱的檔案會殘留在目標目錄，導致：

1. Claude Code 載入時出現兩個功能相似的工具
2. 用戶可能繼續使用過時的舊版本
3. 目標目錄累積越來越多孤兒檔案

此外，當用戶自行修改分發的檔案後，下次分發會直接覆蓋，造成用戶修改遺失。

## What Changes

- 新增 manifest 檔案機制，追蹤所有由 custom-skills 分發的檔案及其內容 hash
- Manifest 統一存放在 `~/.config/ai-dev/manifests/` 目錄，按平台分檔
- 分發時計算檔案 hash（單檔案直接計算，目錄遞迴計算）
- 分發前檢測衝突：比對目標檔案 hash 與 manifest 記錄，若不一致則提醒用戶
- 提供衝突處理選項：`--force`（強制覆蓋）、`--skip-conflicts`（跳過）、`--backup`（備份後覆蓋）
- 分發後自動比對新舊 manifest，清理孤兒檔案（舊有但新沒有的）
- 不影響用戶自訂的 skills/commands（不在 manifest 中的檔案不會被刪除或覆蓋）

## Capabilities

### New Capabilities

- `distribution-manifest`: 追蹤分發檔案的 manifest 機制，包含：
  - Hash 計算（單檔案 + 目錄遞迴）
  - Manifest 讀寫
  - 衝突檢測與處理
  - 孤兒檔案識別與清理

### Modified Capabilities

（無既有規格需要修改）

## Impact

### 影響的程式碼

- `script/utils/manifest.py`（新增）- manifest 相關功能
- `script/utils/shared.py`
  - `copy_custom_skills_to_targets()` - 整合 manifest 流程
  - `_copy_with_log()` - 記錄已複製的檔案
- `script/commands/clone.py` - 新增命令列參數

### 影響的目錄

新增目錄結構：
```
~/.config/ai-dev/
└── manifests/
    ├── claude.yaml
    ├── opencode.yaml
    ├── antigravity.yaml
    ├── codex.yaml
    └── gemini.yaml
```

### 命令列介面變更

`ai-dev clone` 新增選項：
- `--force` - 強制覆蓋所有衝突
- `--skip-conflicts` - 跳過有衝突的檔案
- `--backup` - 備份衝突檔案後覆蓋

### 向後相容性

- 首次執行時若無舊 manifest，不會刪除任何檔案（安全行為）
- 首次執行不報告衝突（因無基準可比）
- 現有分發邏輯不變，僅新增追蹤和清理步驟

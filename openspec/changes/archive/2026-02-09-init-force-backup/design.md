## Context

`ai-dev project init --force` 的正向初始化流程（`project.py:326-364`）會遍歷 `project-template/` 中的所有項目，對目錄型項目先 `_safe_rmtree` 刪除再 `shutil.copytree` 重建。這會導致使用者在目標專案中自定義的檔案（如 `.github/workflows/deploy.yml`）被覆蓋而遺失。

目前已有的備份機制在 `manifest.py:backup_file()`，但僅用於 `clone --backup`，未整合進 init 流程。

## Goals / Non-Goals

**Goals:**
- init --force 覆蓋目錄前，精準備份有差異的檔案
- 備份位置直覺易找（專案根目錄）
- 多次 force 不互相覆蓋

**Non-Goals:**
- 不處理反向同步（場景 B，custom-skills → project-template）的備份
- 不提供自動還原機制（使用者手動從備份複製回來）
- 不複用 `manifest.py:backup_file()`（該機制存放在 `~/.config/ai-dev/backups/`，不符合「專案根目錄」需求）

## Decisions

### 1. 備份觸發時機：目錄覆蓋前逐一比對

在 init 函式的 force 分支中（`project.py:354-357`），在 `_safe_rmtree(dst)` 之前插入備份邏輯。

**為什麼不在整個 init 開始前一次性備份：** 逐目錄處理可以精準控制，只備份即將被覆蓋的目錄，避免不必要的備份。

### 2. 差異比對策略：遞迴逐檔比對

新增 `_collect_diff_files(src_dir, dst_dir)` 函式，遞迴比對兩個目錄：
- 「目標有但模板沒有」的檔案 → 備份（會被 rmtree 刪除）
- 「兩邊都有但內容不同」的檔案 → 備份目標版本
- 「兩邊都有且內容相同」的檔案 → 不備份

內容比對使用 `filecmp.cmp(shallow=False)` 做 byte-level 比對，簡單可靠。

### 3. 備份目錄結構：保留相對路徑

備份目錄結構：
```
_backup_after_init_force/
  20260209_143021/
    .github/
      workflows/
        deploy.yml        # 目標有但模板沒有
        claude.yml        # 兩邊都有但內容不同
```

保留原始的目錄層級結構，讓使用者可以直覺地找到並還原檔案。

### 4. 備份時機統一管理

建立一個共用的 timestamp（`datetime.now().strftime("%Y%m%d_%H%M%S")`），在 init 流程開始時生成，所有需要備份的目錄共用同一個 timestamp 子目錄。

### 5. 檔案型項目（非目錄）的備份

對於單一檔案的覆蓋（`project.py:360`），如果目標檔案存在且內容不同，也一併備份到同一個 timestamp 目錄下。

## Risks / Trade-offs

- **[Risk] 大型目錄比對耗時** → 實際上 `.github/` 和 `.standards/` 通常檔案數量很少，效能不是問題
- **[Risk] 備份目錄累積佔空間** → 使用者自行清理，且 `.gitignore` 已排除不會進版控
- **[Trade-off] 不複用 manifest.py 的備份機制** → 簡化實作，避免改動既有 API，且存放位置需求不同

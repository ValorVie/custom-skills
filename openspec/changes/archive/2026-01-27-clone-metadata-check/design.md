## Context

`ai-dev clone` 執行後，會從上游來源複製檔案到開發專案目錄。這個過程可能引入非內容異動（檔案權限、換行符），導致 `git status` 顯示大量看似「已修改」但實際上內容未變的檔案。

目前的 clone 流程：
1. `integrate_to_dev_project()` 從外部來源複製檔案
2. `copy_skills()` 分發到各工具目錄
3. 無檢測機制來識別非內容異動

## Goals / Non-Goals

**Goals:**
- 在 clone 完成後自動檢測非內容異動
- 分類異動類型：權限變更 vs 換行符變更
- 提供互動式選項讓使用者處理
- 支援記住使用者偏好（可選）

**Non-Goals:**
- 不在 clone 過程中預防（只做事後檢測）
- 不修改上游來源的權限/換行符設定
- 不處理二進位檔案差異
- 不處理非 git 目錄的情況

## Decisions

### 1. 檢測時機：clone 完成後立即執行

**選擇**：在 `clone()` 函數結束前，於 `is_dev_dir` 為 True 時執行檢測。

**理由**：
- 只有開發目錄需要關注 git 狀態
- 立即反饋，使用者不需額外執行指令

**替代方案**：
- 獨立的 `ai-dev check-metadata` 指令 → 增加使用者操作步驟
- 在 `git status` 之前自動執行 → 過於侵入式

### 2. 檢測方法：git diff 解析

**選擇**：使用 `git diff --raw` 取得完整差異資訊，解析 mode change 和內容變更。

**理由**：
- `--raw` 格式包含 old mode / new mode 資訊
- 可一次取得所有需要的資訊
- 比多次 `git diff` 呼叫更高效

**格式範例**：
```
:100644 100755 abc123 def456 M	path/to/file
```
- 100644 → 100755 表示權限從 rw-r--r-- 變成 rwxr-xr-x

**替代方案**：
- `git diff --summary` + `git diff --name-only` → 需要多次呼叫
- 直接讀取 `.git/index` → 過於底層，維護成本高

### 3. 換行符檢測：內容比對

**選擇**：對於有內容差異的檔案，讀取並正規化換行符後比對。

**理由**：
- Git 的 diff 不直接標示「只有換行符差異」
- 需要實際比對內容才能確認

**實作**：
```python
def is_only_line_ending_diff(file_path: str) -> bool:
    # 讀取 git 版本和工作目錄版本
    # 正規化換行符後比對
    pass
```

### 4. 使用者介面：Rich + Typer 互動式選單

**選擇**：使用 Rich 的 Prompt 搭配 Typer 的現有 CLI 框架。

**理由**：
- 專案已使用 Rich 作為輸出格式化
- 一致的使用者體驗
- 支援顏色和格式化

### 5. 處理選項的實作

| 選項 | 實作 |
|------|------|
| 還原變更 | `git checkout -- <files>` |
| 忽略權限 | `git config core.fileMode false` |
| 保留變更 | 不執行任何動作 |
| 顯示清單 | Rich Table 列出所有檔案和異動類型 |

### 6. 程式碼組織：新增 git_helpers 模組

**選擇**：在 `script/utils/` 新增 `git_helpers.py`。

**理由**：
- 保持 clone.py 簡潔
- Git 相關工具可供其他功能重用
- 單一職責原則

**模組結構**：
```python
# script/utils/git_helpers.py

def detect_metadata_changes(repo_path: Path) -> MetadataChanges:
    """檢測非內容異動。"""

def handle_metadata_changes(changes: MetadataChanges, console: Console) -> None:
    """互動式處理非內容異動。"""

def revert_files(files: list[str], repo_path: Path) -> None:
    """還原指定檔案到 git 記錄狀態。"""

def set_filemode_config(repo_path: Path, value: bool) -> None:
    """設定 git core.fileMode 配置。"""
```

## Risks / Trade-offs

**[風險] subprocess 呼叫 git 可能失敗**
→ 緩解：使用 try/except 包裝，失敗時優雅降級（顯示警告但不中斷流程）

**[風險] 大量檔案時效能問題**
→ 緩解：`git diff --raw` 單次呼叫，避免逐檔案處理

**[風險] 非 git 目錄執行會出錯**
→ 緩解：在檢測前先確認 `.git` 目錄存在

**[取捨] 不支援配置檔記住偏好（初版）**
→ 理由：簡化初版實作，後續可擴充

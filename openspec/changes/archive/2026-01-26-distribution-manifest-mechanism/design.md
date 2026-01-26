## Context

目前 `ai-dev clone` 使用 `shutil.copytree(dirs_exist_ok=True)` 分發檔案，這是「覆蓋/合併」模式，不會清理目標目錄中的舊檔案。當工具重命名後，舊檔案會殘留。

現有分發流程位於 `script/utils/shared.py`：
- `copy_custom_skills_to_targets()` - 主要分發函式
- `_copy_with_log()` - 複製並輸出日誌
- `COPY_TARGETS` - 定義各平台的目標路徑

## Goals / Non-Goals

**Goals:**

- 追蹤所有由 ai-dev 分發的檔案及其內容 hash
- 自動清理重命名或移除後的孤兒檔案
- 偵測用戶修改並提醒衝突
- 保護用戶自訂的資源不被刪除
- 向後相容，首次執行不破壞現有環境

**Non-Goals:**

- 不處理版本回滾（manifest 只記錄最新狀態）
- 不自動合併用戶修改（衝突時由用戶決定）
- 不處理跨平台檔案同步衝突

## Decisions

### Decision 1: Manifest 檔案位置

**選擇**：統一存放在 `~/.config/ai-dev/manifests/`

```
~/.config/ai-dev/
└── manifests/
    ├── claude.yaml
    ├── opencode.yaml
    ├── antigravity.yaml
    ├── codex.yaml
    └── gemini.yaml
```

**考量的替代方案**：
- A) 分散存放在各平台的配置目錄 → 管理分散，備份不便
- B) 存放在各平台的子目錄如 `skills/.manifest` → 可能被工具讀取為 skill

**理由**：
- 集中管理，備份/遷移方便
- 不污染各平台的配置目錄
- 用戶容易找到「ai-dev 的所有東西」

### Decision 2: 檔案追蹤與 Hash 計算

**選擇**：追蹤檔案名稱 + 全目錄遞迴 hash

- **單檔案**（commands/agents/workflows）：計算檔案內容的 SHA-256 hash
- **目錄**（skills）：遞迴計算所有檔案內容的組合 hash
  - 遍歷目錄所有檔案
  - 計算每個檔案的 hash
  - 按檔名排序後組合成總 hash

**考量的替代方案**：
- A) 只追蹤關鍵檔案（如 SKILL.md）→ 其他檔案改動不偵測
- B) 只追蹤檔名不算 hash → 無法偵測內容修改

**理由**：
- 精確偵測任何檔案變化
- Skills 目錄檔案數量通常不多，計算成本可接受
- 完整保護用戶修改

### Decision 3: 衝突檢測機制

**選擇**：分發前比對目標檔案 hash 與 manifest 記錄的 hash

```
衝突檢測流程:
1. 讀取舊 manifest（含 hash）
2. 計算目標檔案當前 hash
3. 比對：
   - 目標 hash == manifest hash → 未修改，安全覆蓋
   - 目標 hash != manifest hash → 用戶已修改，提醒衝突
   - 目標不存在 → 新檔案，直接複製
   - manifest 無記錄 → 用戶自訂檔案，不處理
```

**衝突處理選項**：
- `--force`：強制覆蓋所有衝突
- `--skip-conflicts`：跳過有衝突的檔案
- `--backup`：備份衝突檔案後覆蓋（→ `.backup/`）
- 預設：顯示衝突清單，詢問用戶

### Decision 4: 分發流程整合點

**選擇**：建立 `ManifestTracker` 類別，在分發流程中注入

```
分發流程:
1. 讀取舊 manifest（如果存在）
2. 建立 ManifestTracker 實例
3. 檢測衝突，若有衝突則根據選項處理
4. 執行複製，每次複製後呼叫 tracker.record(name, hash)
5. 比對新舊清單，取得孤兒列表
6. 刪除孤兒檔案
7. 寫入新 manifest（含 hash）
```

**理由**：
- Tracker 模式解耦，易於測試
- 分發過程中記錄確保只追蹤我們的檔案
- 衝突檢測在複製前進行，避免覆蓋後才發現

### Decision 5: 孤兒清理時機

**選擇**：在所有複製完成後、manifest 寫入前清理

**理由**：
- 確保新檔案已就位
- 清理失敗不影響 manifest 寫入
- 一次性輸出所有清理日誌

### Decision 6: 版本號來源

**選擇**：從 `pyproject.toml` 讀取專案版本號

**理由**：
- 單一真相來源
- 用戶可追溯分發時的版本

## Risks / Trade-offs

### Risk 1: 首次分發的孤兒遺留

**風險**：升級到 manifest 版本時，舊版本遺留的孤兒檔案不會被清理

**緩解**：
- 文檔說明這是預期行為
- 提供 `ai-dev clean --orphans` 指令（未來擴展）讓用戶手動清理

### Risk 2: Manifest 檔案損壞

**風險**：manifest 檔案被意外修改或損壞

**緩解**：
- 使用 YAML 格式，易於人工修復
- 損壞時視為無舊 manifest，不刪除任何檔案（安全行為）

### Risk 3: Hash 計算效能

**風險**：大量檔案時 hash 計算可能較慢

**緩解**：
- Skills 目錄通常檔案數量有限
- 可考慮快取機制（未來優化）

### Risk 4: 衝突處理的用戶體驗

**風險**：頻繁的衝突提醒可能煩擾用戶

**緩解**：
- 提供 `--force` 選項快速覆蓋
- 衝突摘要清晰，一次顯示所有衝突
- 記住用戶偏好（未來優化）

## Implementation Notes

### Manifest 檔案結構

```yaml
managed_by: ai-dev
version: "2.1.0"
last_sync: "2026-01-26T10:00:00+08:00"
target: claude  # 目標平台
files:
  skills:
    commit-standards:
      hash: "sha256:a1b2c3d4..."
    custom-skills-git-commit:
      hash: "sha256:e5f6g7h8..."
  commands:
    commit.md:
      hash: "sha256:i9j0k1l2..."
    custom-skills-git-commit.md:
      hash: "sha256:m3n4o5p6..."
  agents:
    reviewer.md:
      hash: "sha256:q7r8s9t0..."
  workflows:
    code-review.workflow.yaml:
      hash: "sha256:u1v2w3x4..."
```

### 新增模組

```python
# script/utils/manifest.py (新檔案)

def compute_file_hash(path: Path) -> str:
    """計算單檔案的 SHA-256 hash"""

def compute_dir_hash(path: Path) -> str:
    """遞迴計算目錄的組合 hash"""

@dataclass
class FileRecord:
    name: str
    hash: str

@dataclass
class ManifestTracker:
    """追蹤分發過程中的檔案"""
    target: str
    skills: dict[str, FileRecord]
    commands: dict[str, FileRecord]
    agents: dict[str, FileRecord]
    workflows: dict[str, FileRecord]

    def record_skill(self, name: str, source_path: Path) -> None: ...
    def record_command(self, name: str, source_path: Path) -> None: ...
    def record_agent(self, name: str, source_path: Path) -> None: ...
    def record_workflow(self, name: str, source_path: Path) -> None: ...
    def to_manifest(self, version: str) -> dict: ...

def get_manifest_path(target: str) -> Path:
    """取得指定平台的 manifest 路徑"""
    return Path.home() / ".config" / "ai-dev" / "manifests" / f"{target}.yaml"

def read_manifest(target: str) -> dict | None:
    """讀取 manifest，不存在或損壞時返回 None"""

def write_manifest(target: str, manifest: dict) -> None:
    """寫入 manifest"""

def find_orphans(old_manifest: dict | None, new_manifest: dict) -> dict[str, list[str]]:
    """比對新舊 manifest，返回孤兒清單"""

def detect_conflicts(
    target: str,
    old_manifest: dict | None,
    new_files: dict[str, dict[str, FileRecord]]
) -> list[ConflictInfo]:
    """檢測衝突"""

def cleanup_orphans(target: str, orphans: dict[str, list[str]]) -> None:
    """清理孤兒檔案並輸出日誌"""
```

### 修改函式

```python
# script/utils/shared.py

def copy_custom_skills_to_targets(
    sync_project: bool = True,
    force: bool = False,
    skip_conflicts: bool = False,
    backup: bool = False,
) -> None:
    # 新增: 為每個平台建立 tracker 並整合 manifest 流程
    # 新增: 衝突檢測與處理參數
```

## Context

目前 `ai-dev` CLI 透過硬編碼的 `REPOS` 字典（`script/utils/shared.py:61-80`）管理外部 repo，所有 repo URL 都在原始碼中定義。`add-repo` 指令則將 repo 寫入 `upstream/sources.yaml`（在開源 repo 內），用於追蹤上游第三方專案。

使用者端已有 `~/.config/ai-dev/manifests/` 目錄存放分發追蹤資訊，但尚無使用者層級的 repo 設定檔。

分發流程（`copy_custom_skills_to_targets()`）目前只從 `~/.config/custom-skills/` 單一來源讀取資源，透過 `ManifestTracker` 追蹤並分發到各 AI 工具目錄。

## Goals / Non-Goals

**Goals:**

- 讓使用者能透過 CLI 註冊自訂 repo，設定存放在使用者層級（不進入開源 repo）
- Custom repo 遵循統一的目錄結構規範，確保可預期的資源配置
- 無縫整合進現有的 install / update / clone 流程
- 使用現有的 manifest 系統追蹤 custom repo 資源

**Non-Goals:**

- 不實作 custom repo 的 upstream diff 分析（`upstream-sync` / `upstream-compare` 不涵蓋）
- 不將 custom repo 資源整合回開發專案（`integrate_to_dev_project` 排除）
- 不實作 custom repo 間的衝突解決（同名資源以先註冊者優先）
- 不處理 `hooks/` 和 `plugins/` 的分發邏輯（保留目錄規範，實作留待未來）

## Decisions

### 1. 設定檔位置：`~/.config/ai-dev/repos.yaml`

**選擇**: 放在 `~/.config/ai-dev/` 目錄下，與 `manifests/` 同層級。

**替代方案**:
- `~/.config/custom-skills/custom-repos.yaml`：與 custom-skills repo 混在一起，語意不清
- `~/.config/ai-dev/config.yaml`：通用設定檔會隨功能增長變得複雜

**理由**: `~/.config/ai-dev/` 已是使用者層級的工具設定目錄，repos.yaml 語意明確且獨立。

### 2. 設定檔格式

```yaml
# ~/.config/ai-dev/repos.yaml
repos:
  company-ai-tools:
    url: https://github.com/mycompany/company-ai-tools.git
    branch: main
    local_path: ~/.config/company-ai-tools/
    added_at: "2026-01-29T10:00:00"
```

**選擇**: 以 repo 名稱為 key，包含 `url`、`branch`、`local_path`、`added_at` 欄位。

**理由**: 與現有 `upstream/sources.yaml` 和 `REPOS` 字典的模式一致，降低認知負擔。`added_at` 提供審計追蹤。

### 3. Repo 結構規範：必要目錄但允許空

**選擇**: 根目錄必須包含 `agents/`、`skills/`、`commands/`、`hooks/`、`plugins/` 五個目錄。缺少時發出**警告**而非錯誤，不阻擋註冊。

**替代方案**:
- 嚴格驗證（缺少即失敗）：過於僵硬，不適合初期導入
- 不驗證：失去規範的引導意義

**理由**: 警告模式在規範引導與實務彈性之間取得平衡。repo 維護者可逐步補齊目錄結構。

### 4. 分發策略：合併進現有 ManifestTracker

**選擇**: 在 `copy_custom_skills_to_targets()` 中，於現有 custom-skills 資源分發之後，逐一讀取 custom repos 的資源並加入同一個 `ManifestTracker`。

**替代方案**:
- 獨立 manifest 追蹤：每個 custom repo 用獨立的 manifest 檔案，增加複雜度但隔離性更好

**理由**: 合併 manifest 讓使用者在各 AI 工具中看到統一的資源集合，衝突檢測也自然涵蓋。同名資源的處理依照現有的衝突機制（force/skip/backup）。

### 5. Custom repo 的資源目錄映射

Custom repo 採用**按平台子目錄**的組織方式（與 custom-skills 一致）：

```
company-ai-tools/
├── skills/              → 所有平台共用
├── commands/
│   ├── claude/          → Claude Code
│   ├── opencode/        → OpenCode
│   └── gemini/          → Gemini CLI
├── agents/
│   ├── claude/          → Claude Code
│   └── opencode/        → OpenCode
├── hooks/               → 保留，暫不分發
└── plugins/             → 保留，暫不分發
```

**理由**: 與 `~/.config/custom-skills/` 的目錄結構完全一致，讓 `_copy_with_log()` 可直接復用。

### 6. Clone 失敗處理：graceful skip

**選擇**: clone 失敗時（如無權限存取私有 repo）輸出警告並跳過，不中斷整個 install/update 流程。

**理由**: 使用者可能在不同環境（公司/個人）使用同一份設定，私有 repo 在個人環境中無法 clone 是預期行為。

### 7. Manifest 增加 `source` 欄位

**選擇**: 在 manifest 的每個資源條目中增加 `source` 欄位，記錄資源來源。

```yaml
files:
  skills:
    git-workflow-guide:
      hash: sha256:d427e6f9...
      source: custom-skills          # 來自開源 repo
    company-review-tool:
      hash: sha256:a1b2c3d4...
      source: company-ai-tools       # 來自 custom repo
```

**理由**: 合併 manifest 的便利性加上來源追蹤，讓使用者可以知道每個資源來自哪裡。也為未來的 `ai-dev list --source` 篩選、選擇性更新等功能提供基礎。

**實作方式**: 擴充 `ManifestTracker` 的 `record_*` 方法，接受 `source` 參數。`to_manifest()` 輸出時包含 `source` 欄位。現有的 custom-skills 資源 source 預設為 `"custom-skills"`。

## Risks / Trade-offs

- **[風險] 同名資源衝突** → 依賴現有衝突檢測機制（`detect_conflicts`）。多個 custom repo 間的資源若同名，後分發者覆蓋先分發者。建議使用者以公司前綴命名（如 `myco-`）避免衝突。
- **[風險] 設定檔手動被刪除** → `load_custom_repos()` 在檔案不存在時回傳空結構，不影響既有流程。
- **[已解決] 合併 manifest 的來源追蹤** → 合併 manifest 中為每個資源增加 `source` 欄位，記錄該資源來自 `custom-skills` 或哪個 custom repo 名稱，確保可追溯。
- **[取捨] hooks/plugins 暫不分發** → 結構規範先行，實作留待需求明確時再加。避免過早設計分發邏輯。

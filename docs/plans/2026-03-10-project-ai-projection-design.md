# 設計文件：ai-dev 專案 AI 投影與本地排除架構

**日期：** 2026-03-10
**狀態：** 已實作
**範圍：** ai-dev CLI — `project init`、`project exclude` 與新增的專案投影命令

---

## 實作備註

已完成的命令面如下：

- `ai-dev project init`
- `ai-dev project hydrate`
- `ai-dev project reconcile`
- `ai-dev project doctor`
- `ai-dev project exclude`

目前實作採用 project projection manifest 與 managed block，並將 `.git/info/exclude` 收斂為只隱藏 AI 生成物；`.standards/`、`.editorconfig`、`.gitattributes`、`.gitignore` 等 tracked scaffold 仍保持可見。

---

## 背景

[Confirmed] 目前 `ai-dev project init` 會直接將 `project-template/` 的 AI 檔案複製到目標專案，若目標是 Git repo，接著詢問是否將這些檔案寫入 `.git/info/exclude`；該選擇與 pattern 會記錄到 `.ai-dev-project.yaml`。  
[Source: Code] script/commands/project.py:360  
[Source: Code] script/commands/project.py:528  
[Source: Code] script/utils/project_tracking.py:121

[Confirmed] 現有 `.git/info/exclude` 管理是 marker block 模式，且 `.ai-dev-project.yaml` 會被永遠加入排除項。  
[Source: Code] script/utils/git_exclude.py:9  
[Source: Code] script/utils/git_exclude.py:17  
[Source: Code] script/utils/git_exclude.py:57

[Confirmed] `ai-dev` 已有一層全域 manifest 系統，存放於 `~/.config/ai-dev/manifests/<target>.yaml`，用於分發到 Claude/Codex/Gemini/OpenCode/Antigravity 等工具目錄時的 hash 追蹤、衝突檢測與孤兒清理。  
[Source: Code] script/utils/manifest.py:189  
[Source: Code] script/utils/manifest.py:206  
[Source: Code] script/utils/shared.py:1030  
[Source: Code] script/utils/shared.py:1164

[Confirmed] 但「專案目錄同步」目前是 `copy_custom_skills_to_targets(sync_project=True)` 底下的特例分支，明確不走 manifest 追蹤。  
[Source: Code] script/utils/shared.py:935  
[Source: Code] script/utils/shared.py:1172  
[Source: Code] script/utils/shared.py:1553

這造成三個問題：

1. 專案 AI 檔雖可透過 `.git/info/exclude` 藏起來，但專案投影仍缺乏一致的衝突檢測與孤兒清理機制。
2. `.ai-dev-project.yaml` 同時承擔「專案意圖」與「本機投影狀態」，責任混雜。
3. 專案投影與既有 manifest 體系平行存在，後續要擴充會持續繞過既有機制。

---

## 優先順序

使用者確認的優先順序：

1. 不讓專案內 AI 檔污染 Git 狀態、commit 與 PR
2. 暫不處理 `sync push/pull` 的重新設計與跨裝置同步
3. 架構要保留未來支援跨裝置與多專案共用設定的演進空間

---

## 方案比較

### 方案 A：維持現狀，持續擴充 `.ai-dev-project.yaml`

- 優點：最少改動，可快速延續既有 `project init` 行為
- 缺點：專案投影仍是 manifest 之外的旁路；本機投影狀態與專案意圖混在同一檔，之後擴充會越來越重

### 方案 B：沿用既有 manifest 體系，新增「專案投影 manifest」

- 優點：將專案投影納入與全域分發相同的思維模型
- 優點：可重用既有的 hash、衝突檢測、孤兒清理概念
- 優點：本次可先完成本地投影與 Git 隔離，不必同時處理 sync
- 缺點：需要新增一層本機 manifest 與命令分工

### 方案 C：中央檔案庫 + symlink 投影到專案

- 優點：表面上節省磁碟空間，所有專案共享同一份實體檔
- 缺點：Git 會追蹤 symlink 本身，仍有進版本庫風險
- 缺點：Windows symlink 權限與 Syncthing/跨平台行為都更脆弱

**[Recommended] 採用方案 B。**

理由：

- 它直接解決優先順序 1
- 不把未完成的 sync 設計綁進來
- 充分利用既有 `~/.config/ai-dev/manifests/` 機制，而不是再發明第三套中央追蹤層

---

## 目標與非目標

### 目標

1. 將專案 AI 檔投影納入可追蹤、可重建、可檢查的本機流程
2. 保留 `.ai-dev-project.yaml`，但將其收斂成「專案意圖檔」
3. 將實際生成到專案內的 AI 檔一律透過 `.git/info/exclude` 隱藏
4. 對專案投影建立 manifest-based 的衝突檢測與孤兒清理

### 非目標

1. 本次不重新設計 `ai-dev sync push/pull`
2. 本次不處理跨裝置同步測試與 path normalization
3. 本次不採用 symlink 作為專案投影方式
4. 本次不要求專案目錄完全零 ai-dev 狀態檔；`.ai-dev-project.yaml` 可保留在 repo 根目錄

---

## 架構分層

### Layer 1：Global Target Manifests

既有 `~/.config/ai-dev/manifests/<target>.yaml` 繼續只負責全域工具目錄分發，例如 `~/.claude`、`~/.codex/skills`。  
[Source: Code] script/utils/manifest.py:194  
[Source: Code] /Users/arlen/.config/ai-dev/manifests/codex.yaml:1

本次不修改其責任邊界。

### Layer 2：Project Intent

`.ai-dev-project.yaml` 保留於專案根目錄，但收斂成意圖檔，只描述：

- `project_id`
- `schema_version`
- `template`
- `projection.targets`
- `projection.profile`
- `projection.allow_local_generation`

**不再作為完整本機狀態帳本。**

### Layer 3：Project Projection Manifests

新增本機 manifest：

```text
~/.config/ai-dev/manifests/projects/<project-id>.yaml
```

此檔追蹤：

- 專案投影最後一次執行結果
- 生成檔清單與 hash
- `.git/info/exclude` block 版本與 patterns
- 上次 hydrate/reconcile 的來源版本
- 本機專案路徑提示（僅本機用途）

### Layer 4：Generated Project Files

實際給 AI 工具讀取的檔案仍實體展開在專案內，例如：

- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `.claude/`
- `.codex/`
- `.gemini/`
- `.github/skills/`
- `.github/prompts/`

這些檔案一律由 ai-dev 生成，並寫入 `.git/info/exclude` 管理區塊。  
[Source: Code] script/utils/git_exclude.py:101

---

## 資料模型

### `.ai-dev-project.yaml`（專案意圖）

```yaml
managed_by: ai-dev
schema_version: "2"
project_id: qdm-web
template:
  name: qdm-ai-base
  url: https://github.com/ValorVie/qdm-ai-base.git
  branch: main
projection:
  targets:
    - claude
    - codex
    - gemini
  profile: default
  allow_local_generation: true
managed_files:
  - AGENTS.md
  - .claude/
```

說明：

- `managed_files` 可保留，作為模板管理與專案投影的交集清單
- 舊版 `git_exclude` 區段視為 migration input，不再是長期主資料來源

### `~/.config/ai-dev/manifests/projects/<project-id>.yaml`（本機投影 manifest）

```yaml
managed_by: ai-dev
schema_version: "1"
project_id: qdm-web
project_root: /absolute/path/to/project
template_version: 1.2.6
projection:
  targets:
    - claude
    - codex
  profile: default
exclude:
  enabled: true
  block_version: "1"
  patterns:
    - .claude/
    - .codex/
    - AGENTS.md
files:
  AGENTS.md:
    kind: managed_block
    hash: sha256:...
  .claude:
    kind: directory
    hash: sha256:...
```

---

## 命令責任

### `ai-dev project init`

責任：

- 建立或更新 `.ai-dev-project.yaml`
- 確保 `project_id` 存在
- 首次初始化時可自動串接 `hydrate`

不負責：

- 全面覆蓋專案內所有 AI 檔
- 自行扛完整衝突處理流程

### `ai-dev project hydrate`

責任：

- 根據 `.ai-dev-project.yaml` 將 AI 檔投影到專案內
- 更新 `.git/info/exclude`
- 更新 `~/.config/ai-dev/manifests/projects/<project-id>.yaml`

### `ai-dev project reconcile`

責任：

- 比對意圖檔、投影 manifest、實際專案檔案
- 處理來源新增/刪除、孤兒檔、exclude block 漂移
- 提供 `skip/backup/force` 衝突策略

### `ai-dev project doctor`

責任：

- 做唯讀檢查
- 顯示缺失檔案、衝突、exclude block 漏失、manifest 失聯
- 提供修復建議或提示改跑 `hydrate/reconcile`

### `ai-dev project exclude`

責任：

- 保留為本地排除控制命令
- 但資料來源改以 project projection manifest 為主，而不是只讀 `.ai-dev-project.yaml`

---

## 衝突處理策略

### 目錄型生成物

例如 `.claude/`、`.codex/`、`.gemini/`：

- 使用目錄 hash 追蹤
- 預設互動模式採 `backup`
- 非互動模式預設 `skip`
- 僅在明確指定時使用 `force`

### 單檔根目錄生成物

例如 `AGENTS.md`、`CLAUDE.md`、`GEMINI.md`：

**[Recommended] 改為 managed block 模式，不採整檔覆蓋。**

理由：

- 這些檔案最容易被使用者手動微調
- 沿用 `.git/info/exclude` 已有的 marker block 經驗，可避免每次 hydrate 都製造全檔衝突  
  [Source: Code] script/utils/git_exclude.py:9

---

## 驗證策略

本次只做本機範圍驗證：

1. 單元測試
   - project intent schema
   - project projection manifest 讀寫
   - managed block merge
   - exclude block roundtrip

2. 整合測試
   - `project init -> hydrate`
   - 確認生成檔存在
   - 確認 `.git/info/exclude` 有 ai-dev 區塊
   - 確認 `git status` 不顯示生成檔

3. 衝突測試
   - 手改 `AGENTS.md` 的 managed block
   - 手改 `.claude/` 內檔案
   - 刪除生成檔
   - 來源移除某檔後 `reconcile` 是否正確清理孤兒

**明確排除：**

- `sync push/pull` 整合測試
- 跨裝置 path normalization
- 多機器重建驗證

---

## 遷移策略

### 對既有專案

`project init` / `hydrate` 第一次執行時：

1. 讀取既有 `.ai-dev-project.yaml`
2. 若存在 `git_exclude` 區段，將其視為 migration input
3. 將 `enabled/patterns/keep_tracked` 搬入 project projection manifest
4. 保留 `.ai-dev-project.yaml` 中與 template / managed_files 相關的既有資訊

### 對既有命令

- `project init`：從「複製模板 + 記錄排除」收斂成「註冊意圖 + 初次 hydrate」
- `project exclude`：改讀 project projection manifest 為主

---

## 決策摘要

**本次採納：**

- 保留 `.ai-dev-project.yaml`
- 新增 `~/.config/ai-dev/manifests/projects/<project-id>.yaml`
- 專案投影納入 manifest-based 流程
- 專案 AI 檔仍展開在 repo 內，但一律本地排除
- 本次不處理 `sync push/pull`

**本次不採納：**

- symlink 投影
- 將所有狀態全部繼續塞回 `.ai-dev-project.yaml`
- 直接把專案投影硬接進現有 sync 設計

# Design: ECC 白名單分發機制

## 設計目標

1. **預設拒絕**：ECC 上游新增 skill 不會自動分發。
2. **單一決策點**：每個 skill 的「要 / 不要」只在 `distribution.yaml` 的 `enabled` 清單表達。
3. **分類純文件化**：分類資訊僅影響人類審視效率，不影響 runtime。
4. **可控的審視流程**：catalog 與 ECC 的差異由獨立工具偵測，由人工決定如何更新。

## Ground Truths

- ECC 是會變動的上游，新增/重命名/刪除都會發生。
- 分發決策是「逐個 skill」的二元選擇。
- 維護者需要在決策時看見分類，runtime 不需要分類。
- 預設拒絕 + 顯式啟用 → 才能保證可控性。
- catalog 與 ECC 現況的「差異」是觸發審視的唯一可靠訊號。

## 檔案結構

```
upstream/
├── distribution.yaml        ← 設定（小）
└── ecc-catalog.yaml         ← 純資料（大，供人審視）
```

### `distribution.yaml`（簡化後）

```yaml
version: 1
source: everything-claude-code
source_path: ~/.config/everything-claude-code/

distribute:
  skills:
    source_path: skills/
    targets: [claude, antigravity, opencode, gemini, codex]
    enabled:                  # ← 唯一白名單；未列入者不分發
      - accessibility
      - agent-architecture-audit
      # ... 共 133 項初始值
  commands:                   # ← 維持原樣（黑名單）
    claude:
      source_path: commands/
    opencode:
      source_path: .opencode/commands/
  agents:                     # ← 維持原樣（黑名單）
    claude:
      source_path: agents/
    opencode:
      source_path: .opencode/prompts/agents/
    gemini:
      source_path: agents/

skip_directories: []

exclude:                      # ← 只剩 commands/agents 的排除
  commands:
    claude: []
    opencode: []
  agents:
    claude: []
    opencode: []
    gemini: []
# 注意：exclude.skills 已移除（白名單取代）
```

### `ecc-catalog.yaml`（新增）

```yaml
version: 1
last_synced: "2026-05-12"
last_synced_ecc_commit: "<sha>"      # 紀錄上次 audit 時的 ECC HEAD

categories:
  engineering-methods:
    description: "通用工程方法論：適用所有專案的開發、審查、品質流程"
    skills:
      - name: architecture-decision-records
        added: "2026-03-01"
        note: ""
      - name: code-tour
        added: "2026-03-01"
      # ...

  agent-llm:
    description: "Agent 與 LLM 系統建構"
    skills: [...]

  frontend-ui:
    description: "前端、UI、動畫"
    skills: [...]

  backend-frameworks:
    description: "後端與框架"
    skills: [...]

  data-storage:
    description: "資料儲存與資料庫"
    skills: [...]

  network-infra:
    description: "網路、Homelab、基礎設施"
    skills: [...]

  testing-qa:
    description: "測試、QA、E2E"
    skills: [...]

  docs-knowledge:
    description: "文件、知識管理、研究"
    skills: [...]

  scientific:
    description: "科學與學術"
    skills: [...]

  tools-ops:
    description: "工具、Ops、整合"
    skills: [...]

  process-rfc:
    description: "規範、流程、RFC、PR"
    skills: [...]

  security:
    description: "安全"
    skills: [...]

  ai-cost-tooling:
    description: "AI 工具、Token 預算、成本控制"
    skills: [...]

  uncategorized:
    description: "尚未分類（audit 偵測到 ECC 新增、未在 catalog 中的項目）"
    skills: []                       # ← audit 偵測到差異時提示人工填入
```

## Runtime 邏輯

### `_load_distribution_config()`（簡化）

```python
def _load_distribution_config() -> dict | None:
    config_path = get_custom_skills_dir() / "upstream" / "distribution.yaml"
    if not config_path.exists():
        return None
    with open(config_path) as f:
        config = yaml.safe_load(f)
    if config and "source_path" in config:
        config["source_path"] = str(Path(config["source_path"]).expanduser())
    return config
    # ↑ 移除 ecc-profile.yaml 合併邏輯
```

### `_prescan_ecc()`（白名單過濾）

```python
skills_config = distribute.get("skills", {})
if skills_config and target in skills_config.get("targets", []):
    enabled = set(skills_config.get("enabled", []))
    src = source_base / skills_config["source_path"]
    if src.exists():
        for item in src.iterdir():
            if (item.is_dir()
                and not item.name.startswith(".")
                and item.name not in skip_dirs
                and item.name in enabled              # ← 改成白名單判斷
                and item.name not in npx_managed):
                record(item.name, item, source="ecc")
```

## Audit 子命令

### 使用範例

```bash
$ ai-dev ecc audit
偵測 ECC 與 ecc-catalog.yaml 差異...

[NEW] 5 個 skill 在 ECC 但未在 catalog
  + ecc-new-skill-a       (suggested: uncategorized)
  + ecc-new-skill-b       (suggested: uncategorized)
  ...

[GONE] 1 個 skill 在 catalog 但已從 ECC 移除
  - old-skill             (was in: backend-frameworks)

[RENAMED?] 1 個疑似重命名
  ? old-flow → new-flow   (levenshtein distance: 2)

建議 patch（複製至 upstream/ecc-catalog.yaml）：
---
  uncategorized:
    skills:
      - name: ecc-new-skill-a
        added: "2026-05-12"
      - name: ecc-new-skill-b
        added: "2026-05-12"
---

下一步：
  1. 編輯 upstream/ecc-catalog.yaml，將新項目移到適合的 category
  2. 編輯 upstream/distribution.yaml，將要啟用的加入 distribute.skills.enabled
  3. 重新執行 ai-dev clone
```

### 行為規範

- 不自動寫檔，僅輸出建議
- 不阻塞 install/clone/update
- 退出碼：0 表示無差異；1 表示有 NEW/GONE/RENAMED（可供 CI 偵測）

## install/clone 警告

當 `_load_distribution_config()` 被呼叫且 `ecc-catalog.yaml` 存在時，比對 ECC 目錄與 catalog（廉價：只比較名稱集合）。若有 NEW，印黃色警告：

```
⚠ ECC 上游新增 N 個 skill 未在 ecc-catalog.yaml 審視（預設不分發）
  執行 `ai-dev ecc audit` 查看詳情
```

非阻塞，繼續分發。

## 遷移策略

1. **產生初始 catalog**：把目前實際分發中的 133 個 skill 依現有 `distribution.yaml` 註解的分組，分入 13 個 categories。
2. **產生初始白名單**：`distribute.skills.enabled` 填入 133 個（行為兼容）。
3. **移除 `exclude.skills`** 與 `ecc-profile.yaml` 合併邏輯。
4. **第一次升級時跑 audit**：使用者拿到新版本後執行 `ai-dev ecc audit` 即可看到 ECC 與初始 catalog 之間的差異。

## Out of Scope

- commands / agents 不白名單化（量小、變動少）
- groups 切換、tag 過濾、CLI 互動式啟用（YAGNI，未來可加）
- 自動把 audit 結果寫進 catalog（會消滅「審視」這個關鍵動作）
- 跨機器設定同步機制（git 已能處理）

## Open Questions

無（micro-decisions 已於 explore 階段決議）。

## 初始分類映射（133 → 13 categories）

依先前 explore 階段的分類整理。`note`、`added` 欄位可後續補完，名稱為主依據。實作任務會輸出完整 yaml；以下為摘要：

- engineering-methods (~24)
- agent-llm (~18)
- frontend-ui (~14)
- backend-frameworks (~11)
- data-storage (~4)
- network-infra (~12)
- testing-qa (~7)
- docs-knowledge (~13)
- scientific (~5)
- tools-ops (~17)
- process-rfc (~8)
- security (~3)
- ai-cost-tooling (~6)
- uncategorized (0，初始為空)

> 跨類項目以 primary category 為準，重複歸類不影響白名單（白名單以名稱為鍵）。

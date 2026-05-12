# Design: ECC 白名單分發機制

## 設計目標

1. **預設拒絕**：ECC 上游新增 skill 不會自動分發。
2. **維護者單一決策點**：repo 範圍的「要 / 不要」由 `distribution.yaml` 的 `enabled` 清單表達。
3. **終端使用者可個人化**：透過 `~/.config/ai-dev/ecc-profile.yaml` 在不 fork repo 的前提下，加減個人想要的 skill；git pull 不會與個人覆寫衝突。
4. **分類純文件化**：分類資訊僅影響人類審視效率，不影響 runtime。
5. **可控的審視流程**：catalog 與 ECC 的差異由獨立工具偵測，由人工決定如何更新。

## Ground Truths

- ECC 是會變動的上游，新增/重命名/刪除都會發生。
- 分發決策是「逐個 skill」的二元選擇。
- 維護者需要在決策時看見分類，runtime 不需要分類。
- 預設拒絕 + 顯式啟用 → 才能保證可控性。
- catalog 與 ECC 現況的「差異」是觸發審視的唯一可靠訊號。
- 終端使用者比維護者多得多，且不會 fork repo；個人化必須走 user-level 檔案而非 repo 編輯。
- repo 的 `enabled` 是維護者意圖，使用者覆寫是個人意圖；兩者疊加而非取代。

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

## End-User Customization (`ecc-profile.yaml` v2)

### 檔案位置與格式

```yaml
# ~/.config/ai-dev/ecc-profile.yaml
version: 2                       # ← 區隔 legacy v1（blacklist 時代）
enabled_extra:                   # 額外啟用 repo.enabled 沒列的 skill
  - django-pro
  - fastapi-pro
enabled_remove:                  # 從 repo.enabled 拿掉不想要的 skill
  - angular-developer
```

### 合併公式

```
   final_enabled = (repo.enabled ∪ user.enabled_extra) \ user.enabled_remove
                                                       ↑
                                            remove 後執行（衝突時拒絕勝出）
```

### 合併規則

- **同名衝突**：同一個 skill 同時出現在 `enabled_extra` 與 `enabled_remove` → `remove` 勝（保險預設：個人覆寫只會少分發，不會多分發超出意圖）。
- **extra 中不存在的 skill**：與 repo.enabled 列了不存在的 skill 同等處理，印一次性黃色警告（非阻塞）。
- **remove 中不在 repo.enabled 的 skill**：靜默忽略（不視為錯誤）。
- **ecc-profile.yaml 不存在或為空**：等同 `extra=[], remove=[]`，行為與 repo.enabled 一致。
- **覆寫不需要存在於 catalog**：catalog 是維護者視角的審視工具，使用者個人覆寫不應被 catalog 限制。

### Legacy v1 自動相容

舊版欄位 `include_skills` / `exclude_skills` 的精神可平移到 whitelist 世界：

| Legacy 鍵         | 新鍵              | 平移依據                              |
|-------------------|-------------------|---------------------------------------|
| `include_skills`  | `enabled_extra`   | 「強制納入」→「白名單外額外啟用」     |
| `exclude_skills`  | `enabled_remove`  | 「個人額外排除」→「白名單中拿掉」     |

`_load_distribution_config()` 偵測到僅有 legacy 鍵時 SHALL：
1. 自動把欄位視為新鍵載入（語意等價）
2. 印出一次性 deprecation hint 引導使用者改名（不阻塞、不自動寫檔）

兩種鍵同時存在時，**新鍵優先**，legacy 鍵忽略並警告。

## Upgrade Behavior

### enabled 變動造成的本地檔案異動

```
   T0  使用者 ~/.claude/skills/ 有 enabled_effective = {A, B, C}
   T1  maintainer 從 repo.enabled 拿掉 B 並 commit
   T2  使用者 git pull && ai-dev clone
       ──────────────────────────────────
       new enabled_effective = {A, C}
       ManifestTracker 視 B 為 ECC 孤兒 → 從 ~/.claude/skills/ 刪除
```

**保護機制**：若使用者想保留 B，於 `~/.config/ai-dev/ecc-profile.yaml` 加 `enabled_extra: [B]`。下次 `ai-dev clone` 時：

```
   enabled_effective = ({A, C} ∪ {B}) \ {} = {A, B, C}   → B 保留
```

### 通知機制

`_distribute_ecc_selective()` 在分發前比對前後 enabled 集合差異（透過 old_manifest），若有 ECC 來源的 skill 將被孤兒清理，印出黃色提示：

```
  ⚠ 本次分發將移除 N 個 ECC skill（不再列於 enabled）:
      - angular-developer
      - laravel-plugin-discovery
    如欲保留請於 ~/.config/ai-dev/ecc-profile.yaml 的 enabled_extra 加入名稱。
```

非阻塞，繼續執行。`--force` / `--skip-conflicts` 不影響此提示。

## Runtime 邏輯

### `_load_distribution_config()`（含合併）

```python
def _load_distribution_config() -> dict | None:
    config_path = get_custom_skills_dir() / "upstream" / "distribution.yaml"
    if not config_path.exists():
        return None
    with open(config_path) as f:
        config = yaml.safe_load(f)
    if config and "source_path" in config:
        config["source_path"] = str(Path(config["source_path"]).expanduser())

    # 合併使用者層級覆寫
    profile = _load_ecc_profile()        # 讀 ~/.config/ai-dev/ecc-profile.yaml
    if profile is not None:
        skills_cfg = config.setdefault("distribute", {}).setdefault("skills", {})
        repo_enabled = list(skills_cfg.get("enabled", []))
        extra = list(profile.get("enabled_extra", []))
        remove = set(profile.get("enabled_remove", []))
        merged = [n for n in (repo_enabled + extra) if n not in remove]
        # 去重保序
        seen: set[str] = set()
        skills_cfg["enabled"] = [n for n in merged if not (n in seen or seen.add(n))]

    return config


def _load_ecc_profile() -> dict | None:
    path = get_ai_dev_config_dir() / "ecc-profile.yaml"
    if not path.exists():
        return None
    with open(path) as f:
        profile = yaml.safe_load(f) or {}

    # Legacy v1 自動相容（include_skills → enabled_extra, exclude_skills → enabled_remove）
    if "include_skills" in profile or "exclude_skills" in profile:
        _print_legacy_profile_hint_once()
        profile.setdefault("enabled_extra", profile.get("include_skills", []))
        profile.setdefault("enabled_remove", profile.get("exclude_skills", []))
    return profile
```

### `_prescan_ecc()`（白名單過濾）

```python
skills_config = distribute.get("skills", {})
if skills_config and target in skills_config.get("targets", []):
    enabled = set(skills_config.get("enabled", []))   # ← 已含使用者覆寫
    src = source_base / skills_config["source_path"]
    if src.exists():
        for item in src.iterdir():
            if (item.is_dir()
                and not item.name.startswith(".")
                and item.name not in skip_dirs
                and item.name in enabled              # ← 白名單判斷
                and item.name not in npx_managed):
                record(item.name, item, source="ecc")
```

> `_distribute_ecc_selective()` 使用同一份合併後的 `enabled`，因此使用者覆寫對 prescan / 衝突偵測 / 實際分發三階段都生效，行為一致。

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
3. **移除 `exclude.skills`**（白名單取代）。
4. **重寫 `ecc-profile.yaml` 合併邏輯**：改為白名單語意（`enabled_extra` / `enabled_remove`），保留 legacy 鍵自動相容。
5. **第一次升級時跑 audit**：使用者拿到新版本後執行 `ai-dev ecc audit` 即可看到 ECC 與初始 catalog 之間的差異。
6. **legacy ecc-profile.yaml**：偵測到 `include_skills` / `exclude_skills` → 自動以等價語意載入並印一次性 hint，不破壞既有使用者設定。

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

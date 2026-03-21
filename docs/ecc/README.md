# ECC (Everything Claude Code) Skills 管理

## 這是什麼

ECC 是 Claude Code 社群維護的技能庫，提供 100+ 個涵蓋各領域的 skills。
ai-dev 會在 `install` / `update` 時從 ECC 選擇性分發 skills 到使用者環境。

本目錄集中管理 ECC skills 的分類、篩選規則與參考文件。

## 檔案說明

| 檔案 | 用途 |
|------|------|
| `README.md` | 本文件 — 架構說明與維護指引 |
| `ECC-skills-參考指南.md` | 每個 ECC skill 的分類、說明與建議 |
| `ecc-skills-profile.yaml` | 機讀分類設定（分類 + relevance + action） |
| `ecc-skills-classification-2026-03-21.md` | 初始審計報告（歷史紀錄） |

## 分發機制

### 呼叫鏈

```
ai-dev install / ai-dev update
  │
  └─ copy_skills()                                    # script/utils/shared.py
       └─ copy_custom_skills_to_targets()
            │
            ├─ Step 5:  複製 ai-dev 自有 skills        # source="custom-skills"
            │           來源: ~/.config/custom-skills/skills/ (52 項)
            │
            ├─ Step 5.5: 複製 custom repos             # source="custom-repo"
            │
            └─ Step 5.6: _distribute_ecc_selective()   # source="ecc"
                         │
                         ├─ 讀取 upstream/distribution.yaml
                         ├─ 從 ~/.config/everything-claude-code/skills/ 掃描所有 skills
                         ├─ 排除 distribution.yaml exclude.skills 列出的項目
                         ├─ 跳過與 custom-skills 同名的項目（custom-skills 優先）
                         └─ 複製剩餘項目到 ~/.claude/skills/
```

### 關鍵檔案

| 檔案 | 位置 | 作用 |
|------|------|------|
| `distribution.yaml` | `upstream/distribution.yaml` | **runtime 分發規則** — `exclude.skills` 直接決定哪些 ECC skills 不會被複製到使用者環境 |
| `_distribute_ecc_selective()` | `script/utils/shared.py:1454` | 讀取 distribution.yaml，執行實際複製 |
| `_load_distribution_config()` | `script/utils/shared.py:1373` | 載入並解析 distribution.yaml |
| `_prescan_ecc()` | `script/utils/shared.py:1396` | 預掃描 ECC 資源（用於 ManifestTracker 衝突偵測） |

### 衝突解決

當 ECC skill 與 ai-dev 自有 skill 同名時，ai-dev 自有版本優先（Step 5 先執行，Step 5.6 的 `shutil.copytree(dirs_exist_ok=True)` 會跳過已存在的）。

## 目前狀態

- ECC 上游共 116 個 skills
- `distribution.yaml` 已排除 18 個語言/框架特定 skills
- 實際分發到使用者環境約 91 個 ECC skills（扣除與 ai-dev 同名的不會重複）
- 未來目標：根據使用者實際需求進一步精簡排除清單

## 維護流程

1. ECC 上游新增 skill 時 → 更新 `ECC-skills-參考指南.md` 與 `ecc-skills-profile.yaml`
2. 決定排除某 skill 時 → 加入 `upstream/distribution.yaml` 的 `exclude.skills`
3. 執行 `ai-dev update` 後排除即生效

## 未來目標

**短期：** 透過維護 `distribution.yaml` 的 exclude 清單，精簡不相關的 ECC skills。

**中期：** 設計使用者層級的 profile 機制，讓使用者可在自己的 config 目錄（如 `~/.config/ai-dev/ecc-profile.yaml`）覆寫專案預設的排除清單，無需修改專案檔案。屆時 `_distribute_ecc_selective()` 需讀取兩層設定：
1. 專案層級 `upstream/distribution.yaml`（預設）
2. 使用者層級 `~/.config/ai-dev/ecc-profile.yaml`（覆寫）

**長期：** 提供 TUI 介面讓使用者互動式選擇要啟用的 ECC skill 分類。

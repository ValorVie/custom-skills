# 設計文件：auto-skill shadow projection 與遷移策略

**日期：** 2026-03-13
**狀態：** 已核准
**範圍：** ai-dev CLI — `auto-skill` projection、legacy 遷移、`clone`/`update` 狀態分工

---

## 背景

`[已確認]` 目前 `auto-skill` 的 canonical state 已集中到 `~/.config/ai-dev/skills/auto-skill`，但工具目錄仍直接指向 canonical state。  
`[Source: Code]` `script/utils/paths.py`  
`[Source: Code]` `script/utils/auto_skill_state.py`  
`[Source: Code]` `script/utils/auto_skill_projection.py`

`[已確認]` `.clonepolicy.json` 目前只在 canonical state merge 時生效，工具目錄投影時不參與判斷。  
`[Source: Code]` `script/utils/shared.py`  
`[Source: Code]` `skills/auto-skill/.clonepolicy.json`

---

## 問題

目前模型有兩個核心缺口：

1. **legacy 資料夾遷移不安全**  
   若工具目錄下仍是傳統真實資料夾，直接切換成 symlink 會先刪掉目標，導致 `.clonepolicy.json` 應保留的內容來不及當成基底。

2. **投影更新不尊重 `.clonepolicy.json`**  
   已經是投影狀態時，後續更新只是在更新 canonical state，沒有 target-specific 保留層，因此無法同時滿足：
   - 主檔案更新到最新版本
   - `knowledge-base/*.md`、`experience/*.md` 依 policy 保留

---

## 使用者需求

本次已確認的需求如下：

1. 若目前 target 是傳統資料夾，遷移到投影前要先保留既有內容。
2. 遷移時應使用該傳統資料夾中的 `.clonepolicy.json` 當作保留規則基底。
3. 若目前 target 已是投影，後續更新仍必須尊重 `.clonepolicy.json`。
4. 主檔案應可更新到最新 canonical 版本。
5. 已經健康的 projection 不應因更新流程退化成重新刪除/重建 target link。

---

## 方案比較

### 方案 A：維持 direct canonical projection

- 優點：改動最小
- 缺點：沒有 target-specific 保留層
- 缺點：無法滿足 `.clonepolicy.json` 在 target 投影更新時的語義

### 方案 B：改成檔案級 symlink/copy overlay

- 優點：最細緻，完全可按檔案套用 policy
- 缺點：會大幅重寫現有 `clone` 與 manifest 模型
- 缺點：維運與除錯成本最高

### 方案 C：新增 per-target shadow state，再由 target 投影 shadow

- 優點：保留 canonical state 與 target projection 的分層
- 優點：可在 shadow 重建時套用 `.clonepolicy.json`
- 優點：legacy 遷移與已投影 target 都能用同一套合成流程
- 優點：target 仍維持「投影」而非一般 copy

**`[Recommended]` 採用方案 C。**

---

## 設計決策

### D1. 三層模型

定義三層：

1. **Canonical state**
   - `~/.config/ai-dev/skills/auto-skill`
2. **Per-target shadow state**
   - `~/.config/ai-dev/projections/<target>/auto-skill`
3. **Tool target projection**
   - `~/.claude/skills/auto-skill`
   - `~/.codex/skills/auto-skill`
   - `~/.gemini/skills/auto-skill`
   - 其他支援工具

target 不再直接指向 canonical state，而是指向各自的 shadow。

### D2. `update` 與 `clone` 的責任

- `ai-dev update`
  - 更新 repo 與 canonical state
  - 不修改任何 target shadow
  - 不修改任何工具目錄 link

- `ai-dev clone`
  - 依 target 狀態重建或重用 shadow
  - 必要時切換 target 指向 shadow

### D3. target 狀態分類

`clone` 時需判斷 target 屬於哪種狀態：

- `legacy_dir`
- `canonical_link`
- `shadow_link`
- `missing`
- `broken_link`

### D4. policy 權威來源

- **首次從 `legacy_dir` 遷移時**：優先使用 legacy target 內的 `.clonepolicy.json`
- **其他情況**：使用最新 canonical/template 的 `.clonepolicy.json`

### D5. shadow 重建語義

shadow 重建流程：

1. 選擇保留基底
2. 複製到 temp shadow
3. 以選定的 policy 將 canonical state merge 進 temp shadow
4. 成功後再替換正式 shadow

對應語義：

- `skip-if-exists`：保留基底中的檔案
- `key-merge`：合併 `_index.json`
- `default`：以 canonical 最新主檔覆蓋

### D6. projection metadata

每個 target 需要獨立 metadata，至少記錄：

- `target`
- `revision`
- `mode`
- `migrated_from`
- `policy_source`

用途：

- 判斷 `shadow_link` 是否已與當前 canonical 同步
- 區分首次遷移與後續更新

### D7. 失敗回復

- shadow 一律先在 temp 目錄建置
- temp shadow 建好前，不刪 target 與舊 shadow
- 若替換 shadow 失敗，回復舊 shadow
- 若切換 target link 失敗，保留舊 target 狀態

---

## 資料流

### Flow 1：`ai-dev update`

1. 更新 template / upstream repo
2. refresh canonical state
3. 計算 canonical revision
4. 不觸碰任何 target

### Flow 2：`ai-dev clone`

1. 讀取 target 狀態
2. 決定保留基底與 policy 來源
3. 若 shadow revision 已最新，直接重用
4. 否則重建 shadow
5. 確保 target 指向 shadow

---

## 驗證策略

1. `legacy_dir` 遷移後保留 `skip-if-exists` 檔案
2. `_index.json` 在遷移與更新時使用 `key-merge`
3. `shadow_link` 在 revision 未變時保持等冪
4. `shadow_link` 在 revision 變更時更新主檔但保留 policy 指定檔案
5. `canonical_link` 可平順轉換為 `shadow_link`
6. shadow 重建失敗時可回復
7. `copy_custom_skills_to_targets()` 能整合 shadow projection


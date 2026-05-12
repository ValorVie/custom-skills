---
name: custom-skills-ecc-analyze
description: |
  審視 ECC（everything-claude-code）分發名單，包含兩個模式：
  (A) 既有清單瘦身：分析 distribution.yaml.enabled 與本地 skills/ 的重疊性與品質，輸出 enabled_remove 建議；
  (B) 新項目導入評估：根據 ecc-catalog.yaml 與上次更新範圍，介紹 ECC 上游新增 skill、分析適用情境、建議是否加入 enabled。
  Use when: (1) 評估 ECC 分發名單是否該瘦身、(2) ECC 上游新增 skill 後決定要不要導入、
  (3) 想為終端使用者產 ecc-profile.yaml starter、(4) 季度 / 半年一次定期審視。
  Triggers: "分析 ECC skill", "ECC 重疊", "ECC 清單瘦身", "ECC 新項目", "ECC 上游新增",
  "要不要導入", "ecc analyze", "ecc new items review", "ecc profile starter", "ECC 品質審視".
---

# Custom Skills — ECC Analyze

針對 ECC 分發名單做兩個模式的審視：

- **Mode A — 既有清單瘦身**：審視當前 `distribution.yaml.enabled` 是否有重疊／品質問題，輸出 `enabled_remove` 建議
- **Mode B — 新項目導入評估**：根據 `ecc-catalog.yaml` 與上次更新範圍，介紹 ECC 上游新增的 skill、分析適用情境、建議哪些該加入 `enabled`

輸出皆在 `upstream/reports/`，不自動改 `distribution.yaml`。

## 如何選 Mode

```
   ┌──────────────────────────────────────────────────────────┐
   │  使用者問題                            → 觸發 Mode       │
   ├──────────────────────────────────────────────────────────┤
   │  "分析 ECC 清單" / "瘦身 enabled"      → Mode A           │
   │  "上游新增了什麼" / "要不要加 XX"      → Mode B           │
   │  "全面審視 ECC"                        → A + B 都跑      │
   └──────────────────────────────────────────────────────────┘
```

兩個 Mode 共用 Step 5 的 5 個品質 bucket 與 guardrails，差別在輸入面（既有清單 vs 新增清單）與輸出建議方向（remove vs add）。

---

# Mode A — 既有清單瘦身

針對已經 enabled 的 skill 找出該移除的。

## 工作流程

```
┌────────────────────────────────────────────────────────────────────┐
│                  Mode A — Pruning Pipeline                         │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  1. 取集合          2. 標籤本地         3. 過濾 ECC                │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐               │
│  │ enabled  │  ───▶ │ classify │  ───▶ │ keep ECC │               │
│  │ + local  │       │ local    │       │ in scope │               │
│  └──────────┘       │ by role  │       └──────────┘               │
│                     └──────────┘             │                     │
│                                              ▼                     │
│  4. 重疊比對       5. 品質分群         6. 報告                     │
│  ┌──────────┐      ┌──────────┐       ┌──────────┐                │
│  │ pair by  │ ───▶ │ 5 buckets│  ───▶ │ markdown │                │
│  │ purpose  │      │ A-E      │       │ + yaml   │                │
│  └──────────┘      └──────────┘       └──────────┘                │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Step 1 — 取集合

讀兩個來源：

```bash
# 本地 skill 目錄
ls custom-skills/skills/

# ECC enabled 清單
uv run python -c "
import yaml
d = yaml.safe_load(open('upstream/distribution.yaml'))
print('\n'.join(d['distribute']['skills']['enabled']))
"
```

也要讀 ECC skill 的 description（用於語意比對）：

```bash
ECC=~/.config/everything-claude-code/skills
for n in <names>; do
  desc=$(awk '/^description:/{sub(/^description:[ ]*/,""); print; exit}' "$ECC/$n/SKILL.md")
  echo "[ECC] $n :: $desc"
done
```

> 為什麼用 description 而非全文：description 是 skill 的 trigger 條件，最能代表「使用情境」。要判斷重疊，比對「何時用」比比對「實作細節」更穩。

---

## Step 2 — 標籤本地 skill 的角色

把本地 skill 按角色分群，因為角色相同的 skill 才有機會跟 ECC 重疊：

```
   個人工具流          → custom-* (10)
   工作入口層          → mp-* (6)
   內部 scaffold       → auto-skill, uds
   個人化輸出          → wiki, work-log-*
   思考框架            → first-principles
   領域特化            → cloud-infra-security
   跨 AI 工具          → discuss-multi-ai
```

`mp-*`、`auto-skill`、`uds`、`work-log-*` 是內部專屬，**不會跟 ECC 重疊**（ECC 沒這些概念）。**Step 4 只需比對其餘群組**。

---

## Step 3 — 過濾 ECC

排除明顯不需要審視的 ECC skill：

- 已知為「ECC 內部工具」（如 `ecc-guide`, `nanoclaw-repl`, `hermes-imports`）→ 留待 Step 5 品質群處理
- ECC 上游剛新增、catalog 還沒收錄 → 跳過（執行 `ai-dev ecc audit` 處理）

---

## Step 4 — 重疊比對

對每個本地 skill 找 1-3 個語意最近的 ECC skill：

```
   ┌────────────────────────────────────────┐
   │  本地 skill X                          │
   │  ↓ 在 ECC enabled 中找語意鄰近候選     │
   │  Y1, Y2, Y3                            │
   │                                        │
   │  針對每個 (X, Yk) 評估：              │
   │  - 觸發條件是否高度重疊？             │
   │  - 輸出產物是否相似？                 │
   │  - 抽象層級是否相同？                 │
   │                                        │
   │  分級：高 / 中 / 低-中 / 低           │
   └────────────────────────────────────────┘
```

**重疊強度判準**：

| 強度 | 判準 | 推薦動作 |
|------|------|----------|
| **高** | 觸發條件高度重疊、輸出相似、抽象層級相同 | `enabled_remove` 較弱的一方 |
| **中** | 觸發條件部分重疊、scope 不同 | 留兩個，但備註 |
| **低-中** | 領域接近、實際用法不同 | 留 |
| **低** | 同樣關鍵字但本質不同 | 留 |

**判斷哪一方該留**（衝突時）：
- 本地版較專注、不易被通用版取代 → 留本地、移 ECC
- ECC 版能涵蓋本地未做的場景 → 留 ECC、考慮淘汰本地
- 兩邊都有獨特價值 → 留兩個（不衝突）

---

## Step 5 — 品質分群（5 個 bucket）

把 ECC enabled 中**可能該移除**的項目分入五群：

### A. 明確 deprecated

判準：description 含 `[DEPRECATED]` / `deprecated` / `legacy` 等字樣。
動作：**必移除**。

### B. 高度小眾語言/框架

判準：description 鎖定特定框架/語言，且該框架/語言屬以下任一：
- GitHub star < 1k
- 全球 dev 占比 < 1%
- 命名指向特定區域工具（Cisco、Quarkus 等）

動作：問使用者是否使用該語言/框架；不用 → 移除。

### C. 學術/科研專用

判準：description 含 `scientific`, `literature`, `patent`, `genomic`, `scholar` 等學術詞彙。
動作：問使用者是否做學術研究；不做 → 整群移除。

### D. 命名劣質、辨識度低

判準：
- 名字是縮寫且無 expansion（`ck` 之類）
- 名字以作者命名（`santa-method`, `ralphinho-*`）
- 名字浮誇與內容不符（`agentic-os` 實質是 file-memory）
- description 假設讀者已讀過某 paper（無 self-contained context）

動作：列出讓使用者決定。default 傾向移除（觸發描述模糊容易誤觸發）。

### E. 邊界價值 / 可被內建取代

判準：
- 功能已被 Claude Code / 平台內建取代（`/compact` 取代 `strategic-compact`）
- 單一原則做成整 skill（一行 rule 即可表達）
- 只在極窄場景觸發（< 5% 機率用到）
- 多個近似 skill 互相疊代（`motion-foundations` × `motion-advanced` × `motion-patterns` × `motion-ui`）

動作：列為「邊界」，附上判斷依據讓使用者決定。

---

## Step 6 — 報告輸出（Mode A）

**輸出位置**：`upstream/reports/ecc-skill-analysis-YYYY-MM-DD.md`

**報告結構**：

```markdown
# ECC Skill 分析報告 — 重疊與品質審視

- 日期、分析對象、比對基準、資料來源

## 一、與本地 skill 的重疊性分析
  ### 本地 skill 角色拆解（ASCII 圖）
  ### 重疊矩陣（表格：本地 | ECC 候選 | 強度 | 推薦動作 | 理由）
  ### 重疊小結（建議 enabled_remove 的 yaml 片段）

## 二、品質與通用性問題
  ### A. 明確 deprecated（表格）
  ### B. 高度小眾語言/框架（表格 + 移除建議欄）
  ### C. 學術/科研專用（表格）
  ### D. 命名劣質、辨識度低（表格 + 問題說明）
  ### E. 邊界價值 / 可被內建取代（表格 + 為何邊界）

## 三、建議的 ~/.config/ai-dev/ecc-profile.yaml
  （完整可貼入的 yaml，含中文註解分群）

## 四、後續
  - 重新評估週期
  - 觸發指令
```

**yaml 區塊的撰寫原則**：
- 用註解把 enabled_remove 按來源分群（重疊 / deprecated / 小眾 / 學術 / 邊界 / 二選一）
- 「二選一」項目用 `#` 註解列出讓使用者解註，**不要 default 移除**
- 加總分發數量變化（移前 / 移後）

---

# Mode B — 新項目導入評估

針對 ECC 上游新增的 skill，介紹內容、分析適用情境、給出導入建議。

## 工作流程

```
┌────────────────────────────────────────────────────────────────────┐
│              Mode B — New Items Review Pipeline                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  1. 找新項目          2. 介紹內容        3. 適用度評估             │
│  ┌──────────┐         ┌──────────┐       ┌──────────┐             │
│  │ catalog  │ ───▶    │ read     │ ───▶  │ 通用度   │             │
│  │ diff /   │         │ SKILL.md │       │ 觸發頻率 │             │
│  │ added    │         │ desc +   │       │ 替代性   │             │
│  └──────────┘         │ 30 lines │       └──────────┘             │
│                       └──────────┘             │                   │
│                                                ▼                   │
│  4. 重疊檢查         5. 5 bucket 過濾    6. 三段建議               │
│  ┌──────────┐        ┌──────────┐       ┌──────────┐              │
│  │ 對比本地 │  ───▶  │ A-E 任一 │  ───▶ │ ✅ / ⚠️ / ❌  │            │
│  │ + enabled│        │ → 拒絕   │       │ + 理由   │              │
│  └──────────┘        └──────────┘       └──────────┘              │
│                                                │                   │
│                                                ▼                   │
│                                          7. 報告 +                 │
│                                            enabled patch          │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

## Step 1 — 找新項目

三種來源任一可用（依場景選）：

**方式 A：使用 `ai-dev ecc audit`**
```bash
ai-dev ecc audit
# 看 [NEW] 區段：ECC 有但 catalog 沒有的項目
```

**方式 B：catalog 的 `added` 欄位**

若 catalog 已被 audit 補入 uncategorized，比對 `added >= 上次評估日期`：

```bash
uv run python -c "
import yaml
from datetime import date
last_review = '2026-05-12'   # 上次評估日，或從報告檔名取
cat = yaml.safe_load(open('upstream/ecc-catalog.yaml'))
new_items = []
for cat_key, cat_data in cat['categories'].items():
    for s in cat_data.get('skills') or []:
        added = s.get('added', '') if isinstance(s, dict) else ''
        if added >= last_review:
            new_items.append((cat_key, s['name'], added))
for c, n, a in sorted(new_items, key=lambda x: x[2]):
    print(f'{a}  [{c}]  {n}')
"
```

**方式 C：git log catalog 變動**
```bash
git log -p upstream/ecc-catalog.yaml | head -200
```

確認新項目清單後，記下範圍與日期 cutoff。

## Step 2 — 介紹每個新項目

對每個新項目讀其 SKILL.md：

```bash
ECC=~/.config/everything-claude-code/skills
for n in <new-names>; do
  echo "=== $n ==="
  sed -n '1,40p' "$ECC/$n/SKILL.md"
  echo
done
```

**為每個新項目產出一段介紹**，含：
- 一行摘要（從 description 萃取）
- 主要功能（從前 30 行 SKILL.md 抓核心概念）
- 範例使用情境（從 description 的 "Use when..." 段或自行歸納 2-3 條）

## Step 3 — 適用情境評估（四維）

每個項目打分 1-3：

| 維度 | 1（低） | 2（中） | 3（高） |
|------|---------|---------|---------|
| **通用度** | 特定工具 / 框架 | 特定技術棧 | ≥ 50% 專案適用 |
| **觸發頻率** | 罕見 | 每月幾次 | 每週多次 |
| **不可替代性** | 平台已內建 / 本地有 | 部分覆蓋 | 無近似工具 |
| **學習成本** | 需讀 paper / 大量背景 | 中等 | self-contained |

**總分判讀**：
- 10-12 分 → 強烈建議
- 7-9 分 → 條件性
- ≤ 6 分 → 不建議

> 這是輔助框架，不是硬規則。description 模糊（D 群）或邊界價值（E 群）直接降一級。

## Step 4 — 重疊檢查

對比現有 enabled + 本地 `skills/` 找：

```
   新項目 X
   ├─ 與本地某個高度重疊？      → 「換手」或「不導入」
   ├─ 與某個 enabled 高度重疊？  → 「不導入」或「替換掉舊的」
   ├─ 補強某個既有？             → 「同時保留」並備註定位差異
   └─ 完全獨立？                 → 進入下一步
```

## Step 5 — 5 個品質 bucket 過濾（與 Mode A 共用）

任何一個 bucket 命中即降級或拒絕：

- **A. Deprecated**：description 含 `[DEPRECATED]` / `legacy` → 拒絕
- **B. 高度小眾語言/框架**：鎖定特定小眾框架 → 詢問是否使用該技術棧
- **C. 學術/科研專用**：含 `scientific` / `literature` / `patent` 詞彙 → 詢問是否做學術
- **D. 命名劣質、辨識度低**：縮寫無人懂 / 作者命名 / 浮誇 / 假設讀者背景 → 不導入（觸發描述模糊容易誤觸發）
- **E. 邊界價值**：被內建取代 / 單一原則做整 skill / 極窄場景 → 條件性或不導入

## Step 6 — 三段建議

每個新項目歸類為下列三段之一：

### ✅ 強烈建議導入
- 通用 + 高品質 + 無重疊 + 適用情境清楚
- 直接列入「下次 commit 加進 `distribute.skills.enabled`」

### ⚠️ 條件性導入
- 限定情境但有用（例：你寫 Vue 才有用、做 e2e 才有用）
- 列出觸發條件，由使用者判斷
- 提供「若決定導入」的 patch 片段

### ❌ 不建議導入
- 附原因（小眾 / 重疊 / 品質 bucket 命中）
- 註明可能在未來情境再評估的條件

## Step 7 — 報告輸出（Mode B）

**輸出位置**：`upstream/reports/ecc-new-items-review-YYYY-MM-DD.md`

**報告結構**：

```markdown
# ECC 新項目導入評估 — YYYY-MM-DD

- 上次評估日、本次 cutoff、新項目數量、catalog 版本

## 一、新項目總覽（表格）
| 名稱 | category | added | 通用 | 頻率 | 替代性 | 學習 | 總分 | 建議 |
|------|----------|-------|------|------|--------|------|------|------|

## 二、強烈建議導入（N 個）
  ### <skill-name>
  - 一行摘要
  - 主要功能（2-4 點）
  - 適用情境（2-3 例）
  - 評分理由

## 三、條件性導入（N 個）
  ### <skill-name>
  - 一行摘要 + 觸發條件
  - 「若你 X 才有用」
  - 評分理由

## 四、不建議導入（N 個）
  ### <skill-name>
  - 為何不建議（命中哪個 bucket / 重疊誰）
  - 未來重新評估的條件（若有）

## 五、建議 patch（要加進 distribution.yaml.enabled）

  ```yaml
  # === <category> ===
  - <skill-1>
  - <skill-2>
  ```

  記得同步更新 category 計數的註解。

## 六、後續
- 上次評估日更新為本次日期，下次 cutoff 從此處開始
```

**patch 撰寫原則**：
- 只列「強烈建議」項目（條件性的留給使用者自行加）
- 按 `ecc-catalog.yaml` 的 category 分群
- 標註各 category 預期數量變化

---

# Guardrails（兩個 Mode 共用）

1. **不自動寫 `ecc-profile.yaml` / `distribution.yaml`**：只產報告，最終由使用者決定
2. **不刪除任何檔案**：建議僅以 yaml 片段表達
3. **資料來源以 description 為主**：必要時再讀 SKILL.md 前 30-50 行；避免讀整檔案（成本控制）
4. **每個判斷要有依據**：每個建議都附「為什麼」一句話，否則不列入
5. **新舊不混淆**：Mode A 處理既有 enabled，Mode B 處理新項目；同時跑時也分開報告

---

## 範例輸出

- **Mode A 完整實例**：[`upstream/reports/ecc-skill-analysis-2026-05-12.md`](../../upstream/reports/ecc-skill-analysis-2026-05-12.md)
- Mode B 範例：首次執行後產出於 `upstream/reports/ecc-new-items-review-YYYY-MM-DD.md`

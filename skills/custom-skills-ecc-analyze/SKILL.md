---
name: custom-skills-ecc-analyze
description: |
  分析 ECC 白名單（upstream/distribution.yaml.enabled）與本地 skills/ 的重疊性與品質，
  輸出 `enabled_remove` 建議到 upstream/reports/。
  Use when: (1) 評估 ECC 分發名單是否該瘦身、(2) ECC 上游大批新增 skill 後審視、
  (3) 想為終端使用者產 ecc-profile.yaml starter、(4) 季度 / 半年一次定期審視。
  Triggers: "分析 ECC skill", "ECC 重疊", "ECC 清單瘦身", "ecc analyze", "ecc audit overlap",
  "ecc profile starter", "ECC 品質審視".
---

# Custom Skills — ECC Analyze

針對 ECC `enabled` 白名單做兩個維度的審視：

1. **重疊性**：哪些 ECC skill 與本地 `skills/` 高度重疊，是否該由本地取代
2. **品質與通用性**：哪些 ECC skill 屬於 deprecated / 過度小眾 / 命名劣質 / 邊界價值

輸出：`upstream/reports/ecc-skill-analysis-YYYY-MM-DD.md` 與一份可直接套用的 `ecc-profile.yaml` 建議區塊。

---

## 工作流程

```
┌────────────────────────────────────────────────────────────────────┐
│                        Analysis Pipeline                           │
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

## Step 6 — 報告輸出

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

## Guardrails

1. **不自動寫 `ecc-profile.yaml`**：只產報告，最終由使用者複製貼上
2. **不修改 `distribution.yaml`**：分析結果只進 `upstream/reports/`，repo enabled 由維護者另行決定
3. **不刪除任何檔案**：移除建議僅以 yaml `enabled_remove` 表達
4. **資料來源以 description 為主**：避免讀整個 SKILL.md（速度、token 成本）
5. **品質判斷要有依據**：每個移除建議都附上「為什麼」一句話，否則不列入

---

## 範例輸出

完整實例：[`upstream/reports/ecc-skill-analysis-2026-05-12.md`](../../upstream/reports/ecc-skill-analysis-2026-05-12.md)

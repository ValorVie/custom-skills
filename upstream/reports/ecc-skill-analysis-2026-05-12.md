# ECC Skill 分析報告 — 重疊與品質審視

- **日期**：2026-05-12
- **分析對象**：`upstream/distribution.yaml` 中 `distribute.skills.enabled` 的 133 個 ECC skill
- **比對基準**：本地 `custom-skills/skills/` 24 個 skill
- **資料來源**：`~/.config/everything-claude-code/skills/<name>/SKILL.md` 的 `description`

---

## 一、與本地 skill 的重疊性分析

### 本地 skill 角色拆解

```
   custom-* (10)     ─── 專案專屬工具
   mp-* (6)          ─── MP 工作入口層
   auto-skill, uds   ─── 內部 scaffold 機制
   wiki, work-log-*  ─── 個人化輸出
   first-principles  ─── 思考框架
   cloud-infra-sec.  ─── 安全清單
   discuss-multi-ai  ─── 多 AI 審議
```

### 重疊矩陣

| 本地 skill | ECC 重疊候選 | 強度 | 推薦動作 | 理由 |
|------------|--------------|------|----------|------|
| `wiki` | `knowledge-ops` | **高** | `remove knowledge-ops` | 都是知識庫管理；`wiki` 具體（資料→wiki 文章），`knowledge-ops` 抽象（multi-storage layers） |
| `custom-skills-tool-overlap-analyzer` | `workspace-surface-audit` | **高** | `remove workspace-surface-audit` | 兩者都是工具盤點，本地版專注 overlap、ECC 版偏 ECC-native 推薦 |
| `custom-skills-tool-overlap-analyzer` | `automation-audit-ops`、`repo-scan` | 中 | 留 | 一個偏 hook/MCP、一個偏跨檔分類，角度不同 |
| `custom-skills-git-commit` | `git-workflow` | 中 | 留 | 動作工具 vs pattern 指南，使用情境不同 |
| `discuss-multi-ai` | `agent-eval`、`council` | 中 | 留 | benchmark、四聲審議、跨工具同題審查三角不同 |
| `custom-simplify` | `plankton-code-quality` | 低-中 | 留 | review-time vs write-time 不同階段 |
| `custom-skill-creator` | `skill-stocktake` | 低 | 留 | creator vs auditor 互補 |
| `custom-skills-doc-writer` / `-doc-updater` | `code-tour`、`documentation-lookup` | 低 | 留 | 三者功能完全不同 |
| `custom-skills-plan-analyze` | `plan-orchestrate` | 低 | 留 | analyze vs 產 `/orchestrate` 指令 |
| `custom-skills-threads-research` | `deep-research`、`market-research`、`data-scraper-agent` | 低 | 留 | 本地專做 Threads、後者通用 |
| `cloud-infrastructure-security` | `security-review`、`security-scan` | 低-中 | 留 | 雲端基礎設施 vs 一般 OWASP scope 不同 |
| `first-principles` | `council`、`strategic-compact` | 低 | 留 | 不同決策框架可互補 |
| `custom-skills-dev` | `agentic-engineering`、`ai-first-engineering` | 低 | 留 | 專案專屬 vs 通用方法論 |

### 重疊小結

僅有 **2 個 ECC skill** 與本地形成高度重疊，建議 `enabled_remove`：

```yaml
enabled_remove:
  - knowledge-ops
  - workspace-surface-audit
```

---

## 二、品質與通用性問題

問題分為五群。

### A. 明確 deprecated（**必移除**）

| skill | 證據 |
|-------|------|
| `continuous-learning` | description 開頭即標註「[DEPRECATED - use continuous-learning-v2]」 |

### B. 高度小眾語言/框架

| skill | 適用場景 | 移除建議 |
|-------|----------|----------|
| `tinystruct-patterns` | 一個幾乎沒人用的 Java 框架 | 強烈建議移除 |
| `fsharp-testing` | F#（全球專案數很小） | 若不寫 F# 移除 |
| `quarkus-patterns` / `-security` / `-tdd` / `-verification` | Quarkus JVM × 4 個 | 不寫 Quarkus 一次移除 4 個 |
| `nestjs-patterns` | NestJS 特定框架 | 看是否使用 |
| `nuxt4-patterns` | Vue 生態 | 看是否使用 |
| `angular-developer` | Angular | 多數人已不用 |
| `laravel-plugin-discovery` | PHP/Laravel | 不寫 PHP 移除 |
| `cisco-ios-patterns` / `netmiko-ssh-automation` / `network-bgp-diagnostics` | netops × 3 | 非 netops 移除 |
| `windows-desktop-e2e` | Windows 桌面 | 不寫桌面移除 |
| `ios-icon-gen` | iOS 圖示 | 偶用留、不用移 |

### C. 學術/科研專用

| skill | 用途 |
|-------|------|
| `scientific-db-pubmed-database` | 生醫文獻 |
| `scientific-db-uspto-database` | 美國專利 |
| `scientific-pkg-gget` | 基因組查詢 |
| `scientific-thinking-literature-review` | 學術文獻回顧 |
| `scientific-thinking-scholar-evaluation` | 學者評估 |

不做生醫/學術 5 個一起拿掉。

### D. 命名劣質、辨識度低

| skill | 問題 |
|-------|------|
| `ck` | 名字像縮寫無人懂；功能與 claude-mem 重疊，需檢視 |
| `agent-sort` | 名字看不出「為 repo 產 ECC install plan」 |
| `agentic-os` | 「persistent multi-agent OS」用語浮誇，實質是 file-memory + scheduled automation |
| `santa-method` | 用作者名命名，看不出是 multi-agent adversarial verification |
| `ralphinho-rfc-pipeline` | 同上，看不出是 RFC-driven multi-agent DAG |
| `gan-style-harness` | 假設讀者知道 GAN 概念並讀過 Anthropic 2026/03 paper |

不打算用就移除；description 模糊容易誤觸發。

### E. 邊界價值 / 可被內建取代

| skill | 為何邊界 |
|-------|----------|
| `strategic-compact` | Claude Code 已有 `/compact` + 自動壓縮 |
| `regex-vs-llm-structured-text` | 單一決策原則做成整 skill，實質是 rule |
| `hermes-imports` | 只在「Hermes → ECC 遷移」場景觸發 |
| `nanoclaw-repl` | 操作 ECC 內部實驗 REPL，與分發路徑無關 |
| `claude-devfleet` / `dmux-workflows` | 特定多 agent 編排工具 |
| `motion-foundations` / `motion-advanced` / `motion-patterns` / `motion-ui` | × 4 個 motion 動畫 skill，不做動畫一起移；做動畫評估是否需全四個 |
| `agentic-engineering` vs `ai-first-engineering` | 題目重疊，挑一個 |

---

## 三、建議的 `~/.config/ai-dev/ecc-profile.yaml`

```yaml
version: 2

enabled_remove:
  # — 與本地高度重疊
  - knowledge-ops
  - workspace-surface-audit

  # — 明確 deprecated
  - continuous-learning

  # — 小眾框架/語言（依實際技術棧調整）
  - tinystruct-patterns
  - fsharp-testing
  - quarkus-patterns
  - quarkus-security
  - quarkus-tdd
  - quarkus-verification
  - angular-developer
  - laravel-plugin-discovery
  - cisco-ios-patterns
  - netmiko-ssh-automation
  - network-bgp-diagnostics
  - windows-desktop-e2e

  # — 學術/科研
  - scientific-db-pubmed-database
  - scientific-db-uspto-database
  - scientific-pkg-gget
  - scientific-thinking-literature-review
  - scientific-thinking-scholar-evaluation

  # — 邊界價值
  - strategic-compact
  - regex-vs-llm-structured-text
  - hermes-imports
  - nanoclaw-repl

  # — 二選一（評估後再決定）
  # - agentic-engineering          # 與 ai-first-engineering 題目重疊
  # - motion-foundations
  # - motion-advanced
  # - motion-patterns
  # - motion-ui                    # 不做動畫 4 個一起移
```

套用後分發數量：133 − 25-29 ≈ 104-108 個。

執行 `ai-dev clone` 時會印黃色提示告知將被孤兒清理的 skill，必要時透過 `enabled_extra` 救回。

---

## 四、後續

- 重新評估週期建議：ECC 上游每次有大批新增（≥ 10 個）或每季一次。
- 觸發指令：見 skill `custom-skills-ecc-analyze`（位於 `custom-skills/skills/`）。

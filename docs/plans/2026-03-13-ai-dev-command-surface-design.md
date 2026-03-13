# 設計文件：ai-dev 指令面盤點與 maintain 命令重構

**日期：** 2026-03-13
**狀態：** 提案中
**範圍：** ai-dev CLI 全部指令面、`custom-skills` 專案特殊處理、`maintain` 命令群設計

---

## 摘要

本文件盤點 `ai-dev` 目前全部頂層命令與子命令群組，指出語意重疊、命名誤導、責任混雜與 `custom-skills` 專案特例的耦合點，並提出新的命令分層模型。

本次核心建議如下：

1. 將 `custom-skills` repo 自身維護責任從 `project init --force` 與 `clone --sync-project` 中抽離
2. 新增 `ai-dev maintain clone` 與 `ai-dev maintain template`
3. 讓 `ai-dev project *` 回到「一般專案模板 / AI 投影」責任
4. 為 `project-template/` 新增人工維護的 allowlist manifest，避免再用隱性規則反推模板內容

---

## 背景

[Confirmed][Source: Code] `ai-dev` 的 CLI 目前同時包含環境安裝、全域分發、一般專案初始化、模板 repo 管理、上游 registry、標準 profile 管理、同步服務、測試輔助與記憶同步等多個子系統。  
[Source: Code] script/main.py:1

[Confirmed][Source: Code] `project init --force` 在一般專案代表「強制重新初始化」，但在 `custom-skills` repo 內卻會直接切換成「專案 → project-template 反向同步」。  
[Source: Code] script/commands/project.py:362  
[Source: Code] script/commands/project.py:443  
[Source: Code] script/commands/project.py:477

[Confirmed][Source: Code] `clone` 名義上是分發到工具目錄，但在 `custom-skills` 開發目錄執行時，前段會先做「整合外部來源到開發目錄」，後段才做全域分發。  
[Source: Code] script/commands/clone.py:53  
[Source: Code] script/commands/clone.py:96  
[Source: Code] script/utils/shared.py:1703

[Confirmed][Source: Code] `install` 也帶有 `--sync-project`，並沿用 `copy_skills(sync_project=...)` 這條路徑，因此安裝流程也可能對當前 `custom-skills` 專案目錄產生副作用。  
[Source: Code] script/commands/install.py:75  
[Source: Code] script/commands/install.py:301  
[Source: Code] script/utils/shared.py:1209

[Confirmed][Source: Code] `update` 會同時更新一般 repo 與 `repos.yaml` 中的 custom repo；若 custom repo 的 `type == "template"`，它不直接更新專案，而是提示使用者去各專案執行 `ai-dev init-from --update`。  
[Source: Code] script/commands/update.py:299  
[Source: Code] script/commands/update.py:321  
[Source: Code] script/commands/update.py:332  
[Source: Code] script/commands/init_from.py:235

這些行為 individually 合理，但整體指令面出現三種問題：

1. 同一個命令名稱在不同上下文代表不同責任
2. 同一個旗標名稱在不同命令中實際效果不同
3. 一般使用者流程與 `custom-skills` repo 維護流程混在同一條命令路徑

---

## 現況盤點

### 頂層命令總覽

| 類別 | 命令 | 目前主要責任 | 問題摘要 |
|------|------|--------------|----------|
| Environment | `install` | 安裝工具、clone repo、分發內容 | 夾帶專案同步副作用 |
| Environment | `update` | 更新工具、repo、canonical state | 同時碰 template repo 提示 |
| Distribution | `clone` | 分發到工具目錄 | 開發模式會先整合外部來源到 repo |
| Inspection | `status` | 環境與 repo 狀態檢查 | 責任清楚 |
| Inspection | `list` | 列出資源 | 責任清楚 |
| Distribution | `toggle` | 啟用/停用工具端資源 | 責任清楚 |
| Registry | `add-repo` | upstream registry | 與 `add-custom-repo` 模型並列 |
| Registry | `add-custom-repo` | custom repo registry | tool/template 混在同一份設定檔 |
| Registry | `update-custom-repo` | 更新 custom repo | 與 `update` 部分責任重疊 |
| Project Template | `init-from` | 從 template repo 合併到一般專案 | 與 `project init` 並列但心智模型不同 |
| Utility | `test` | 跑測試 | 責任清楚 |
| Utility | `coverage` | 跑 coverage | 責任清楚 |
| Utility | `derive-tests` | 輸出 spec 內容 | 名稱和實際功能有落差 |
| UI | `tui` | 啟動 TUI | 責任清楚 |
| Subsystem | `project *` | 一般專案 scaffold / AI 投影 / 更新 | 夾帶 custom-skills 模板維護特例 |
| Subsystem | `standards *` | standards profile 管理 | 責任清楚 |
| Subsystem | `hooks *` | ECC hooks plugin 管理 | 責任清楚 |
| Subsystem | `sync *` | 檔案同步 repo | 與 `mem *` 同為同步，但領域不同 |
| Subsystem | `mem *` | claude-mem server sync | 責任清楚，但與主產品心智模型距離較遠 |

### `project` 命令群組

| 命令 | 目前行為 | 評估 |
|------|----------|------|
| `project init` | 複製 tracked scaffold、建 intent、hydrate AI 檔 | 核心責任合理 |
| `project init --force` | 一般專案為強制重建；`custom-skills` repo 變成模板反向同步 | 最嚴重的語意錯位 |
| `project hydrate` | 依 intent 重新生成 AI 檔 | 合理 |
| `project reconcile` | 收斂 manifest / intent / 生成檔 | 合理 |
| `project doctor` | 檢查 projection 狀態 | 合理 |
| `project update` | 整合 `uds update` + `openspec update` | 名稱過於泛，實際是 standards/spec 子系統更新 |
| `project exclude` | 管理 `.git/info/exclude` | 合理 |

### `custom-skills` 專案的特殊處理清單

目前存在 4 個明確特例入口：

1. `project init --force`  
   在 repo 內轉成 `project-template/` 反向同步。  
   [Source: Code] script/commands/project.py:475

2. `clone --sync-project`  
   在 repo 內先執行 `integrate_to_dev_project()`，把外部來源整合回開發目錄。  
   [Source: Code] script/commands/clone.py:98  
   [Source: Code] script/utils/shared.py:1703

3. `copy_skills(sync_project=True)`  
   分發完成後再把 `~/.config/custom-skills` 的 `skills/commands/agents` 複製回專案根目錄。  
   [Source: Code] script/utils/shared.py:1209  
   [Source: Code] script/utils/shared.py:1590

4. `install --sync-project`  
   `install` 藉由 `copy_skills(sync_project=...)` 重用上一條特例。  
   [Source: Code] script/commands/install.py:305

這 4 條路徑都與「一般使用者操作 ai-dev」無關，屬於「維護 `custom-skills` repo 自身」的工作流。

---

## 問題分析

## 1. 命令名稱與責任不一致

[Confirmed][Source: Code] `clone` 的 help 與 docstring都描述成「分發到工具目錄」，但實作在開發者模式下會先做 repo 整合。  
[Source: Code] script/commands/clone.py:79  
[Source: Code] script/commands/clone.py:92

[Inferred][Source: Code] 使用者看到 `clone` 很難直覺聯想到：

- 它可能改動目前的開發專案
- 它會刷新 `auto-skill` canonical state
- 它會處理 custom repos 與 ECC 分發

`clone` 事實上承擔的是「全域分發 orchestrator + 開發者維護入口」，不是單純 copy/distribute。

## 2. `sync_project` 旗標語意漂移

[Confirmed][Source: Code] `clone --sync-project` 的意思是「整合外部來源到 custom-skills 開發目錄」。  
[Source: Code] script/commands/clone.py:55

[Confirmed][Source: Code] `install --sync-project` 的意思是「在 install 過程結束時，把分發內容同步回當前專案目錄」。  
[Source: Code] script/commands/install.py:83  
[Source: Code] script/commands/install.py:306

[Inferred][Source: Code] 同一個旗標名稱實際對應兩種概念：

- external source integration
- distributed content back-sync

這會讓 README 與 CLI help 難以簡潔描述，也讓使用者更難預測副作用。

## 3. 一般專案流程與 `custom-skills` 自維護混在 `project` 命令

[Confirmed][Source: Code] `project init` 是一般專案用 scaffold/hydrate 命令，但 `--force` 被偷渡成模板維護入口。  
[Source: Code] script/commands/project.py:443  
[Source: Code] script/commands/project.py:477

[Inferred][Source: Code] 這導致 `project init --force` 無法再可靠地代表「重新初始化」，也讓測試策略變複雜，因為相同命令在不同 cwd 下要驗證兩套完全不同的語意。

## 4. template repo 與 tool repo 管理模型混雜

[Confirmed][Source: Code] `custom_repos.py` 用單一 `repos.yaml` 管理 `tool` 與 `template` 兩種 repo。  
[Source: Code] script/utils/custom_repos.py:48

[Confirmed][Source: Code] `update` 會一併更新這兩種 repo，但更新後的後續動作不同：

- `tool` repo：最終靠 `clone` 分發
- `template` repo：最終靠 `init-from --update` 套回各專案

[Source: Code] script/commands/update.py:299  
[Source: Code] script/commands/update.py:333

[Inferred][Source: Code] 目前 registry 層沒有把「分發來源」與「專案模板來源」兩種領域清楚分開，導致使用者需要額外記憶後續命令。

## 5. `project-template/` 缺少顯式治理清單

[Confirmed][Source: Code] 目前模板反向同步依賴 `project-template/` 當下已存在的內容作為同步清單，沒有外部 allowlist manifest。  
[Source: Code] script/commands/project.py:368  
[Source: Code] script/commands/project.py:382

[Confirmed][Source: Code] 現有模板的第一層內容混合 tracked scaffold 與 AI 設定投影來源，例如 `.standards`、`.editorconfig`、`AGENTS.md`、`.claude/`、`.codex/`、`.github/skills/` 等。  
[Source: Code] project-template/

[Inferred][Source: Code] 若沒有顯式清單，就很難回答這些問題：

- 哪些頂層項目是模板的正式邊界？
- 哪些檔案應該由 `project-template/` 人工維護，不應從 repo 根目錄覆蓋？
- 新增頂層項目時，何時應納入模板？

---

## 重構目標

### 目標

1. 讓命令名稱與實際責任一致
2. 將 `custom-skills` repo 自維護行為抽離到獨立命令群
3. 讓一般使用者不必理解 `custom-skills` repo 特例也能使用核心流程
4. 為 `project-template/` 建立顯式 allowlist 治理
5. 保留過渡期相容性，但逐步淘汰誤導性入口

### 非目標

1. 本次不直接重寫 `sync *` 或 `mem *` 子系統
2. 本次不重命名所有既有命令
3. 本次不處理 TUI 重新分類
4. 本次不改變 `auto-skill` canonical/shadow 架構

---

## 方案比較

### 方案 A：最小切割

- 移除 `project init --force` 反向同步
- 新增 `maintain template`
- 新增 `maintain clone`
- 保留 `clone --sync-project` / `install --sync-project`，但標示 deprecated

**優點**

- 風險最低
- 改動範圍可控

**缺點**

- 歷史語意仍殘留
- README 與 CLI help 仍需描述雙軌行為

### 方案 B：命令責任重切分

- `install/update/status` 只做環境與 repo 管理
- `clone/list/toggle/hooks` 只做全域分發與工具端資源
- `project *` 只做一般專案 scaffold / AI 投影
- `maintain *` 專責 `custom-skills` repo 維護
- `init-from` 與 custom/template repo registry 在報告中明確改列為 template workflows

**優點**

- 最符合心智模型
- 可從說明文件、CLI help、測試結構一起收斂
- 新命令群責任邊界最清楚

**缺點**

- 需要 deprecation 過渡
- README 與測試要同步大修

### 方案 C：激進改名

- `clone` 改名為 `distribute`
- `project init` 改名為 `project scaffold`
- `init-from` 改名為 `project template apply`

**優點**

- 長期最乾淨

**缺點**

- 破壞性最大
- 不適合當前這一輪先落地

**[Recommended] 採用方案 B。**

---

## 建議的新命令領域模型

### Domain 1: Environment

處理本機工具、套件、repo 基礎環境。

- `ai-dev install`
- `ai-dev update`
- `ai-dev status`

**原則：**

- 不碰 `custom-skills` 開發專案同步
- 不承擔模板維護
- `install` 僅負責安裝與初始分發

### Domain 2: Distribution

處理全域工具目錄分發與資源狀態。

- `ai-dev clone`
- `ai-dev list`
- `ai-dev toggle`
- `ai-dev hooks *`

**原則：**

- `clone` 只做 `~/.config/custom-skills` → tool targets 的分發
- 不再整合外部來源回 repo
- 不再同步回 `custom-skills` 專案目錄

### Domain 3: Project

處理一般專案的 scaffold / AI 投影 / 專案意圖。

- `ai-dev project init`
- `ai-dev project hydrate`
- `ai-dev project reconcile`
- `ai-dev project doctor`
- `ai-dev project exclude`
- `ai-dev project update`
- `ai-dev init-from`

**原則：**

- `project init --force` 永遠代表強制初始化
- `project` 內不再出現 `custom-skills` 專案特例

### Domain 4: Maintain

專責維護 `custom-skills` repo 自身。

- `ai-dev maintain clone`
- `ai-dev maintain template`

**原則：**

- 只有維護者需要理解這組命令
- 將 repo 自我更新流程從一般使用者流程中剝離

### Domain 5: Registry

管理來源註冊與 repo 類型。

- `ai-dev add-repo`
- `ai-dev add-custom-repo`
- `ai-dev update-custom-repo`

**未來可再演進：**

- 將 `tool repo` 與 `template repo` 分成不同子命令或不同 registry

### Domain 6: Utilities

獨立子系統，保留現有分組。

- `ai-dev standards *`
- `ai-dev sync *`
- `ai-dev mem *`
- `ai-dev test`
- `ai-dev coverage`
- `ai-dev derive-tests`
- `ai-dev tui`

---

## `maintain` 命令設計

## `ai-dev maintain clone`

### 目的

將目前散落在 `clone --sync-project`、`install --sync-project`、`copy_skills(sync_project=True)` 的 `custom-skills` repo 自維護流程收斂為單一入口。

### 責任

1. 將外部來源整合到 `custom-skills` 開發目錄
2. 視需要同步分發產物回 repo 工作樹
3. 只在確認當前目錄是 `custom-skills` repo 時可執行

### 預設行為

建議第一版只做目前 `integrate_to_dev_project()` 的責任：

- UDS → repo
- Obsidian skills → repo
- Anthropic skill-creator → repo
- auto-skill canonical refresh

### 後續可選責任

若仍需要「把 `~/.config/custom-skills` 的 skills/commands/agents 回寫到 repo」這件事，建議不要藏在 `clone`，而是明確放到 `maintain clone --from-dist` 或另一個子命令。

### 建議 CLI

```bash
ai-dev maintain clone
ai-dev maintain clone --no-auto-skill
ai-dev maintain clone --from-dist
```

第一版可先只實作：

```bash
ai-dev maintain clone
```

## `ai-dev maintain template`

### 目的

用顯式清單把 `custom-skills` repo 根目錄中「應進入 `project-template/` 的檔案/資料夾」同步到模板，完全取代 `project init --force` 的反向同步特例。

### 責任

1. 讀取人工維護的模板 allowlist manifest
2. 依 manifest 將 repo 根目錄同步到 `project-template/`
3. 針對 merge file 使用既有合併策略
4. 不再以 `project-template/` 當下內容反推同步邊界

### 建議 CLI

```bash
ai-dev maintain template
ai-dev maintain template --check
ai-dev maintain template --list
```

### 建議模式

- `--check`: 僅檢查 repo 根目錄與模板的差異，不寫入
- `--list`: 顯示目前 manifest 定義的 allowlist
- 預設：依 manifest 套用同步

---

## `project-template` allowlist manifest 設計

## 問題

目前 `project-template/` 的同步邊界是隱性的，依賴目錄現況。這會讓模板治理變成「看現在有什麼就同步什麼」。

## 建議

新增顯式 manifest，例如：

```text
project-template.manifest.yaml
```

### 建議格式

```yaml
version: 1

include:
  - .editorconfig
  - .gitattributes
  - .gitignore
  - .standards/
  - AGENTS.md
  - CLAUDE.md
  - GEMINI.md
  - INSTRUCTIONS.md
  - .claude/
  - .codex/
  - .gemini/
  - .opencode/
  - .agent/
  - .agents/
  - .github/

exclude:
  - .claude/settings.local.json
  - .claude/disabled.yaml
```

### 原則

1. `include` 是唯一權威來源
2. `exclude` 僅做局部裁剪，不再作為主邊界工具
3. 所有新增頂層項目必須顯式加入 `include` 才可進模板

### 第一版建議納管的頂層項目

[Confirmed][Source: Code] 目前 `project-template/` 已存在以下第一層項目，可作為第一版 allowlist 初稿：  
[Source: Code] project-template/

- `.agent/`
- `.agents/`
- `.claude/`
- `.codex/`
- `.editorconfig`
- `.gemini/`
- `.gitattributes`
- `.github/`
- `.gitignore`
- `.opencode/`
- `.standards/`
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `INSTRUCTIONS.md`

### 建議人工維護的例外

[Confirmed][Source: Code] 目前已有 `EXCLUDE_FROM_TEMPLATE = {"settings.local.json"}`。  
[Source: Code] script/commands/project.py:36

因此至少應繼續排除：

- `.claude/settings.local.json`

另外建議評估是否將以下內容改為手動維護或排除：

- `.claude/disabled.yaml`
- 任何使用者機器本地化設定檔

---

## 具體調整建議

## 1. 移除 `project init --force` 的模板反向同步

**調整前**

- 一般專案：強制初始化
- `custom-skills` repo：模板同步

**調整後**

- 永遠只做強制初始化
- 若在 `custom-skills` repo 執行，也應維持相同行為

## 2. 移除 `clone` 對 repo 維護的隱性責任

**調整前**

- `clone` 在開發目錄執行時，先整合外部來源

**調整後**

- `clone` 永遠只分發到工具目錄
- repo 整合改走 `maintain clone`

## 3. 移除 `install --sync-project` 或進入 deprecation

**調整前**

- `install` 可能因 `sync_project=True` 回寫到 repo 工作樹

**調整後**

- `install` 僅安裝與分發
- 若仍需 repo 維護，明確執行 `maintain clone`

## 4. README 與 CLI help 重新分類

README 應改成先講命令領域，再列命令：

1. Environment
2. Distribution
3. Project
4. Maintain
5. Registry
6. Utilities

這會比單純列一張扁平 command table 更容易理解。

---

## 遷移策略

### Phase 1

1. 新增 `maintain` 命令群
2. 實作 `maintain clone`
3. 實作 `maintain template`
4. 移除 `project init --force` 特例

### Phase 2

1. 讓 `clone` 不再做 repo 維護
2. 讓 `install` 不再接受 `--sync-project`
3. README / help / 測試全面同步

### Phase 3

1. 檢討 registry：是否拆 `template repo` 與 `tool repo`
2. 檢討 `project update` 是否應重新命名或下沉到 `standards/spec` 子系統
3. 檢討 `derive-tests` 的命名與職責

---

## 推薦結論

**推薦採用「命令責任重切分」方案。**

理由如下：

1. 這一輪最痛的不是功能做不到，而是命令心智模型已經混雜
2. `custom-skills` repo 維護是少數維護者需求，不應再藏在一般使用者命令中
3. `maintain clone` / `maintain template` 可以把 `custom-skills` 特例從 `project` 與 `clone` 中完整抽出
4. `project-template.manifest.yaml` 能把模板治理從隱性規則改成顯式清單，後續更容易測試與審查

---

## 後續實作順序

1. 新增 `maintain` 命令群與 `project-template.manifest.yaml`
2. 實作 `maintain template`
3. 移除 `project init --force` 特例並更新測試
4. 實作 `maintain clone`
5. 從 `clone` / `install` 移除 `sync_project` 相關責任
6. 更新 README 與命令說明


# 設計文件：ai-dev 高階命令 Phase Pipeline 與 Command Manifest

**日期：** 2026-03-13
**狀態：** 已確認
**範圍：** ai-dev CLI — `install`、`update`、`clone` 與其共用參數模型、內部抽象、command manifest

---

## 背景

[Confirmed] 目前 `ai-dev install` 同時負責前置需求檢查、工具安裝、repo clone 與 target 分發。  
[Source: Code] script/commands/install.py:75

[Confirmed] `ai-dev update` 同時負責工具升級、repo refresh、plugin marketplace 更新，以及 `auto-skill` canonical state refresh。  
[Source: Code] script/commands/update.py:165  
[Source: Code] script/commands/update.py:344

[Confirmed] `ai-dev clone` 目前語意相對單純，主要負責從 `~/.config/custom-skills` 分發到各 target，並在分發時刷新需要的 state。  
[Source: Code] script/commands/clone.py:13  
[Source: Code] script/utils/shared.py:1006

[Confirmed] 目前 `script/commands/` 與 `script/utils/` 幾乎都採平舖結構，`install.py`、`update.py`、`clone.py` 與 `shared.py`、`auto_skill_state.py`、`project_projection.py` 並列，已開始混合 CLI parsing、流程協調、狀態管理與具體操作。  
[Source: Code] script/main.py:1  
[Source: Code] script/utils/shared.py:1

這造成三個直接問題：

1. 高階命令名稱雖直觀，但背後責任不夠清楚，使用者無法僅靠命令名推測副作用。
2. `--skip-npm`、`--skip-bun`、`--skip-repos`、`--only` 等參數語彙分散，跨命令不一致。
3. 命令樹、flags、state writer 與文件目前仍缺少單一 machine-readable 契約來源。

---

## 外部參考與適用性

### Git：保留高階命令，內部再拆 porcelain / plumbing

[Confirmed] Git 官方文件明確區分 end-user oriented porcelain commands 與低階 plumbing commands。  
[Source: External] https://git-scm.com/docs/git/2.2.3.html

這點適合 `ai-dev`，因為 `ai-dev` 的主要使用情境也是「做一個高階工作流」，而不是直接操作一堆同質資源。

### uv：統一參數語彙與一致的 CLI 契約

[Confirmed] `uv` 的 CLI 參數模型相當一致，會反覆使用同一套旗標語意與目錄解析方式。  
[Source: External] https://docs.astral.sh/uv/reference/cli/

這點適合 `ai-dev` 的下一步：不是發明更多命令，而是把 phase / target / skip / only 的規則統一。

### Docker / kubectl：資源型命令樹不適合作為主模型

[Confirmed] Docker CLI 傾向以 object/resource 分組，例如 `docker image`、`docker container`。  
[Source: External] https://docs.docker.com/reference/cli/docker/

[Confirmed] `kubectl` 則是典型的 `verb + resource` 命令模型。  
[Source: External] https://kubernetes.io/docs/reference/kubectl/

這類模型對 `ai-dev` 不夠適合，因為 `ai-dev` 的主要操作不是資源 CRUD，而是環境 bootstrap / refresh / apply 這類工作流。

**[Recommended] 採用 Git 風格的高階命令模型，並輔以 uv 風格的一致參數語彙。**

---

## 目標與非目標

### 目標

1. 保留 `install`、`update`、`clone` 作為對外高階命令
2. 將其內部流程重構為一致的 phase pipeline
3. 為三個高階命令建立統一的 `--only` / `--skip` / `--target` 參數模型
4. 建立 machine-readable command manifest，作為命令契約、文件與測試的共同來源
5. 重整 `script/` 內部結構，降低 `shared.py` 類型大雜燴持續膨脹的風險

### 非目標

1. 本次不重新命名高階命令
2. 本次不全面重寫 `project`、`sync`、`mem`、`standards` 子系統
3. 本次不處理 TUI 命令模型重構
4. 本次不追求一次把所有 command help / docs 完全自動生成

---

## 方案比較

### 方案 A：保留高階命令，內部採 Phase Pipeline

- 對外保留 `install / update / clone`
- 對內固定拆成 `tools`、`repos`、`state`、`targets`
- 三個高階命令只是不同 phase 的預設組合
- `--only`、`--skip`、`--target` 全部統一

**優點**
- 對使用者心智變動最小
- 最符合 Git 式高階命令模型
- 便於建立 machine-readable command manifest

**缺點**
- 需要先清楚定義各 phase 的邊界，否則只是把混亂換名字

### 方案 B：改成資源型命令樹

- 例如 `ai-dev tools update`、`ai-dev repos refresh`、`ai-dev targets apply`

**優點**
- 責任切分最乾淨

**缺點**
- 破壞既有高階命令習慣
- 對一般使用者心智負擔更高
- 不符合本專案主要使用情境

### 方案 C：完全保留現況，只補文件與測試

**優點**
- 改動最小

**缺點**
- 無法解決參數模型分裂與抽象層混雜
- 只是在既有設計債上加文檔

**[Recommended] 採用方案 A。**

---

## 命令模型

### 高階命令保留

對外仍保留：

- `ai-dev install`
- `ai-dev update`
- `ai-dev clone`

這三者仍是使用者主要入口，不改名、不拆成資源型 command tree。

### 內部 Phase Model

新增四個一級 phase：

- `tools`
  - 安裝或更新 Claude Code、全域 NPM 套件、Bun 套件、plugin marketplace
- `repos`
  - clone / fetch / reset `~/.config/*` repos 與 custom repos
- `state`
  - 刷新 canonical state、projection metadata、其他中間狀態
- `targets`
  - 分發到 `~/.claude`、`~/.codex`、`~/.gemini`、`~/.config/opencode` 等 target

### 三個高階命令的預設 phase

| 命令 | 預設 phase | 語意 |
|------|------------|------|
| `install` | `tools,repos,state,targets` | 從零建立或補齊環境 |
| `update` | `tools,repos,state` | 刷新工具與來源，不直接套用到 targets |
| `clone` | `state,targets` | 將目前 state 套用到 targets |

---

## 統一參數模型

### 共用 flags

三個高階命令統一支援：

- `--only <phase,...>`
- `--skip <phase,...>`
- `--target <tool,...>`
- `--dry-run`

### 規則

1. `--only` 與 `--skip` 只能使用 phase 名稱，合法值由 command manifest 定義
2. `--target` 只在最終執行 plan 含 `targets` phase 時有效
3. 若命令未執行 `targets` phase 卻傳入 `--target`，應明確報錯
4. 命令專屬衝突控制 flags 仍可保留，例如 `clone --force --backup`，但不得重新定義 phase 語意

### 範例

```bash
ai-dev install
ai-dev install --skip tools
ai-dev update --only repos,state
ai-dev clone --target claude,codex
ai-dev clone --only targets --target opencode --dry-run
```

### 相容性原則

既有細碎 flags 例如：

- `install --skip-npm`
- `install --skip-bun`
- `install --skip-repos`
- `update --skip-npm`
- `update --skip-bun`
- `update --skip-repos`

在重構完成後移除，改由 phase model 與必要的 phase-internal selector 取代。

---

## Command Manifest 設計

### 設計原則

command manifest 必須是 machine-readable，但不應額外引入一份容易 drift 的手寫 YAML 當唯一真相來源。

**[Recommended] 採用 Python 內建 registry / schema 作為 source of truth，再提供可序列化輸出。**

### Manifest 至少要描述的欄位

- command path
- command kind（top-level / subgroup / leaf）
- allowed phases
- default phases
- allowed targets
- supported flags
- state writers
- dry-run support
- notes / warnings

### 範例結構

```python
CommandSpec(
    path=("install",),
    kind="top_level",
    default_phases=("tools", "repos", "state", "targets"),
    allowed_phases=("tools", "repos", "state", "targets"),
    allowed_targets=("claude", "codex", "gemini", "opencode", "antigravity"),
    flags=("only", "skip", "target", "dry_run"),
    state_writers=(
        "~/.config/custom-skills/",
        "~/.config/ai-dev/skills/auto-skill",
        "~/.config/ai-dev/projections/<target>/auto-skill",
    ),
)
```

### Manifest 的用途

1. 驗證 CLI flags 組合是否合法
2. 生成或校驗 `docs/ai-dev指令與資料流參考.md` 的命令面摘要
3. 作為未來 `doctor` / `status` 類檢查的命令契約來源

---

## 程式碼結構調整

### 現況問題

- `script/commands/` 同時承擔 CLI parsing 與流程協調
- `script/utils/shared.py` 集中過多與 environment distribution 相關的邏輯
- `auto_skill_state.py`、`shared.py`、`paths.py` 等沒有更高層的 domain 分類

### 新分層

```text
script/
  commands/
    install.py
    update.py
    clone.py
  cli/
    command_manifest.py
    phase_selection.py
    target_selection.py
  services/
    pipeline/
      install_pipeline.py
      update_pipeline.py
      clone_pipeline.py
    tools/
      install.py
      update.py
    repos/
      clone.py
      refresh.py
    state/
      auto_skill.py
      manifest_refresh.py
    targets/
      distribute.py
      conflicts.py
  models/
    command_spec.py
    execution_plan.py
```

### 分層責任

- `commands/`：Typer entry，解析 CLI 參數並建構 execution plan
- `cli/`：共用 CLI 選項解析、phase 與 target selection
- `services/pipeline/`：高階命令 orchestration
- `services/<domain>/`：具體執行各 phase
- `models/`：command spec、execution plan、phase / target schema

---

## 執行流程

### `install`

1. 解析 flags → 建立 `ExecutionPlan`
2. 執行 `tools`
3. 執行 `repos`
4. 執行 `state`
5. 執行 `targets`

### `update`

1. 解析 flags → 建立 `ExecutionPlan`
2. 執行 `tools`
3. 執行 `repos`
4. 執行 `state`
5. 不執行 `targets`

### `clone`

1. 解析 flags → 建立 `ExecutionPlan`
2. 執行必要的 `state`
3. 執行 `targets`

---

## 錯誤處理與驗證

### 錯誤處理

1. phase 不合法：CLI 解析階段直接報錯
2. `--target` 與 phase 組合不合法：plan 驗證階段報錯
3. 某 phase 執行失敗：pipeline 停止，回報 phase name 與失敗原因
4. `--dry-run`：只輸出 execution plan，不執行任何 state writer

### 測試策略

1. `command manifest` 與 CLI 註冊一致性測試
2. phase selection 單元測試
3. `install / update / clone` execution plan 測試
4. 既有 `install/update/clone` 行為回歸測試
5. `docs/ai-dev指令與資料流參考.md` 與 manifest 的摘要同步測試

---

## 遷移策略

### 第一階段

- 建立 phase model、execution plan 與 command manifest
- 先讓 `install / update / clone` 內部改走新 pipeline
- 對外命令名稱不變

### 第二階段

- 補齊 `docs/ai-dev指令與資料流參考.md` 的 top-level 命令細部語意
- 將更多子系統逐步接到 command manifest

### 第三階段

- 視需要擴展 manifest 與 doc generation 能力
- 再評估是否讓更多命令採用統一 phase/target flags

---

## 決策摘要

1. 保留 `install / update / clone` 作為對外高階命令
2. 內部統一為 `tools / repos / state / targets` phase pipeline
3. flags 統一為 `--only / --skip / --target / --dry-run`
4. command manifest 採 Python registry / schema 作為 source of truth
5. 程式碼結構從平舖轉為 `commands + cli + services + models`

---

## 參考資料

- Git Documentation: [git(1)](https://git-scm.com/docs/git/2.2.3.html)
- uv CLI Reference: [uv reference](https://docs.astral.sh/uv/reference/cli/)
- Docker CLI Reference: [docker CLI](https://docs.docker.com/reference/cli/docker/)
- kubectl Reference: [kubectl overview](https://kubernetes.io/docs/reference/kubectl/)

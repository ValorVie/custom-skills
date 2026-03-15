---
title: ai-dev 命令面優化評估
type: report/analysis
date: 2026-03-13
author: Codex
status: updated
---

# ai-dev 命令面優化評估

## 摘要

截至 2026-03-13，`ai-dev` 已有一份可對照實作的命令與資料流參考文件，且本輪補齊了 `project`、`maintain`、`standards`、`sync`、`mem`、`hooks` 六組子命令語意。其後續的 P0 落地已完成：
- `install / update / clone` 已改為共享 `tools / repos / state / targets` phase pipeline
- top-level command manifest 已落地為 machine-readable Python registry
- 參考文件已補齊 phase 契約，並新增 manifest 對文件的一致性測試

接下來的主要問題不再是「文件嚴重過時」，而是命令面本身仍存在責任邊界混雜、副作用透明度不足、預設 target 不一致、狀態檔分散且缺少更廣泛的機器驗證等設計債。這些問題尚未直接造成錯誤行為，但已經提高理解成本與後續 drift 風險。

## 分析目的

- 確認目前已盤點的命令語意是否已能作為可信參考
- 收斂 `ai-dev` 命令面在下一階段最值得調整的設計問題
- 區分「文件同步問題」與「命令/狀態模型本身需要重構」兩種議題

## 分析範圍

### 包含

- 命令面入口：`script/main.py`
- 子命令模組：
  - `script/commands/project.py`
  - `script/commands/maintain.py`
  - `script/commands/standards.py`
  - `script/commands/hooks.py`
  - `script/commands/sync.py`
  - `script/commands/mem.py`
- 參考文件：
  - `docs/ai-dev指令與資料流參考.md`
- 相關底層資料流：
  - `script/utils/shared.py`
  - `script/utils/project_projection.py`

### 排除

- 尚未逐子命令展開的 top-level 命令深度行為，例如 `install`、`update`、`clone`、`status`、`list`、`toggle`
- 非 `ai-dev` CLI 的外部工具內部實作，例如 `uds`、`openspec`、`claude-mem` server
- UI/TUI 互動細節與文本體驗優化

## 方法論

- 以 `script/main.py` 建立目前命令樹與子命令清單
- 逐一對照各子命令實作中的：
  - 前置條件
  - 主要副作用
  - 寫入狀態檔
  - 失敗與跳過條件
- 將對照結果回填到 `docs/ai-dev指令與資料流參考.md`
- 在語意已對齊的前提下，再分析命令面設計的可優化點

## 分析結果

### 發現 1：已盤點區域的文件與實作目前可視為對齊

**結論**: 目前 `project`、`maintain`、`standards`、`hooks`、`sync`、`mem` 六組子命令，文件描述已能反映實作。

**資料/證據**:

| 面向 | 現況 | 評估 |
|------|------|------|
| 子命令名稱盤點 | 已與 `script/main.py` 和各 `Typer` app 對齊 | 良好 |
| 子命令語意 | 已補齊至參考文件 | 良好 |
| 主要狀態檔 | 已列出主要 writer 與路徑 | 良好 |
| 已知語意漂移 | 本輪已修正 `project init` 同名目錄 docstring | 已處理 |

**分析**:
這表示目前最大的風險已從「看文件會做錯事」降到「需要讀很多地方才能理解整體設計」。換句話說，參考文件現在可以當作維護基線，但還不是最終的命令契約來源。

### 發現 2：命令分層雖已改善，但責任邊界仍不夠乾淨

**結論**: `ai-dev` 的命令分層已有雛形，但仍存在多個命令同時做「同步來源、刷新狀態、實際分發」的情況。

**資料/證據**:

| 面向 | 現況 | 評估 |
|------|------|------|
| 環境層命令 | `install` / `update` / `clone` 均涉及 repo、canonical state、target 分發不同組合 | 需關注 |
| repo 自維護命令 | 已拆成 `maintain clone` / `maintain template` | 良好 |
| 專案層命令 | `project init/hydrate/reconcile/exclude` 已成群，但仍共享較多隱含狀態 | 需關注 |

**分析**:
`maintain` 的拆分方向是正確的，但環境層仍偏向「歷史疊代後的功能集合」。例如使用者需要理解 `install`、`update`、`clone` 各自會不會刷新 canonical state、會不會動 target shadow、會不會碰 repo，心智成本仍偏高。

### 發現 3：副作用透明度仍不足，命令名稱不足以預測寫入範圍

**結論**: 多數命令的名稱已經能描述主動作，但不足以讓使用者預測會寫哪些狀態檔或觸發哪些附帶流程。

**資料/證據**:

| 命令 | 額外副作用 | 評估 |
|------|------------|------|
| `sync init` | 建 repo、還原本機、回寫 repo、寫 `.gitignore`、LFS、plugin manifest、直接 push | 需關注 |
| `mem pull` | worker API / SQLite fallback 匯入、更新 pulled hashes、可能自動 reindex 與 cleanup | 需關注 |
| `standards switch` | 除了更新 profile，還預設直接同步 `claude` target | 需關注 |
| `project init` | 除了複製模板，也會建立 tracking file、詢問 exclude、hydrate AI projection | 可接受但需更明確 |

**分析**:
這些行為本身不一定錯，但太多「順手做掉」的副作用會讓命令面更難預測，也讓 dry-run、審查與回滾策略變得模糊。

### 發現 4：target 與 scope 的預設規則不一致

**結論**: 不同子系統對 target/scope 的預設處理方式不同，容易讓使用者誤以為所有系統都遵循相同模型。

**資料/證據**:

| 子系統 | 預設 scope | 問題 |
|--------|------------|------|
| `standards switch` | 內建自動同步 `claude` | 與 `standards sync --target` 的多 target 模型不完全對齊 |
| `hooks` | 命令群組名稱泛用，但實作僅支援 Claude | 命名與實際 scope 不完全一致 |
| `mem auto` | 依平台直接安裝 launchd / cron | 命令本身同時承擔 config 與系統排程層責任 |

**分析**:
當 CLI 同時管理 Claude、Codex、Gemini、OpenCode 等多 target 時，scope 一致性很重要。否則使用者會把某個子系統的預設行為錯誤投射到其他子系統。

### 發現 5：狀態檔雖已盤點，machine-readable 契約已起步，但覆蓋率仍可擴大

**結論**: 現況已能人工追蹤 state owner，且 top-level command 已有 machine-readable manifest 與文件一致性測試；但仍未覆蓋到更多子命令與 state writer 細節。

**資料/證據**:

| 面向 | 現況 | 評估 |
|------|------|------|
| 命令清單來源 | `script/main.py` + 各子模組 | 良好 |
| 文件同步方式 | 以 `docs/ai-dev指令與資料流參考.md` 為人工主檔，top-level command 由 manifest test 校驗 | 改善中 |
| 漂移防護 | 已有 top-level command/phase 的 drift test，但尚未覆蓋子命令與 state writer | 需關注 |

**分析**:
這代表目前的可靠性已不再完全建立在維護紀律上，但 system constraint 還只覆蓋 top-level command。隨著命令數量與 state 增加，仍需要把這套方式擴展到更多子命令與 writer 層。

## 比較與對照

| 面向 | 現況 | 理想方向 | 建議 |
|------|------|----------|------|
| 命令語意揭露 | 文件已可人工查找 | 命令與文件可互相驗證 | 建立 machine-readable command manifest |
| 環境層責任 | `install/update/clone` 仍有重疊 | refresh / distribute / bootstrap 明確分離 | 先重整高層命令語意 |
| 子系統預設 target | 不完全一致 | scope 規則一致且顯性 | 統一 target 預設策略 |
| 副作用控制 | 命令常夾帶附加流程 | 主流程與附加流程可拆分 | 增加顯式 flags 或拆命令 |
| state 管理 | 已可追蹤但分散 | 文件 + 程式雙重約束 | 加入 drift test / doc generation |

## 結論

### 關鍵發現

1. 已盤點的子命令語意目前與實作一致，參考文件已可作為維護基線。
2. 下一階段的主要問題是命令面設計債，而不是文件完全失真。
3. 風險最高的區域是高層環境命令的責任重疊，以及缺少機器化 drift 防護。

### 建議

| 優先級 | 建議 | 理由 | 預期效果 |
|--------|------|------|----------|
| P0（已完成） | 建立 machine-readable command manifest，並用測試驗證 top-level command 與參考文件同步 | 已落地於 `script/cli/command_manifest.py` 與 `tests/test_ai_dev_command_reference.py` | 降低文件失真與命令契約不明風險 |
| P0（已完成） | 重新收斂高層命令 `install` / `update` / `clone` 的責任分界，明確區分 `tools / repos / state / targets` | 已落地為 phase pipeline 與統一 flags | 讓使用者能更直觀預測副作用與正確使用命令 |
| P1 | 統一 target/scope 預設規則，至少先處理 `standards switch` 與 `hooks` 的 scope 不一致問題 | 目前不同子系統的預設不一致 | 降低誤用與跨子系統心智切換成本 |
| P1 | 把重副作用流程拆成顯式階段或顯式 flags，例如 `sync init`、`mem pull`、`mem auto` | 目前許多命令同時做多件事 | 提高可預測性、可測試性與回滾能力 |
| P1 | 補齊 top-level 命令的細部語意表，至少涵蓋 `install/update/clone/status/list/toggle/init-from` | 目前參考文件對子系統已完整，但高層命令仍較粗略 | 讓整份參考文件真正成為單一可查來源 |
| P2 | 逐步把 state transition 收斂成更一致的 manifest/metadata 模式 | 目前各子系統 YAML/JSON/state file 風格差異大 | 降低維護成本，讓 doctor/status 更容易做全域檢查 |

## 限制與假設

- 本報告的「已對齊」結論，限於本輪已逐項核對的子命令與參考文件範圍。
- `install`、`update`、`clone` 等高層命令雖已有高階描述，但尚未做同等粒度的逐命令語意表審計。
- 本報告聚焦命令面與狀態模型，不評估 CLI 文案易讀性與互動 UX 細節。

## 附錄

- 參考文件：`docs/ai-dev指令與資料流參考.md`
- 命令入口：`script/main.py`
- 子命令模組：
  - `script/commands/project.py`
  - `script/commands/maintain.py`
  - `script/commands/standards.py`
  - `script/commands/hooks.py`
  - `script/commands/sync.py`
  - `script/commands/mem.py`

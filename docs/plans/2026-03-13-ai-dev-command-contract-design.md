---
title: ai-dev 命令契約最終狀態設計
type: plan/design
date: 2026-03-13
author: Codex
status: confirmed
---

# ai-dev 命令契約最終狀態設計

## 摘要

本文件定義 `ai-dev` 命令面在下一階段的最終狀態，不採 P1/P2 分級 rollout。目標是一次收斂三類問題：

1. 統一 target 與 scope 契約
2. 將重副作用流程改成顯式模式或顯式 flags
3. 建立可長期維護的命令分類與設計壓力參考，並補齊 top-level 命令語意表

此設計建立在已完成的 top-level phase pipeline 之上：`install / update / clone` 已共享 `tools / repos / state / targets` phase model 與 machine-readable command manifest。本輪不再調整高階命令名稱，而是把整個 CLI 的命令契約、分類模型、scope 規則與顯式副作用原則一次收斂到穩定狀態。

## 背景

截至 2026-03-13，`ai-dev` 已完成兩個前置基礎：

1. `install / update / clone` 已改為共享 `tools / repos / state / targets` phase pipeline。
2. `docs/ai-dev指令與資料流參考.md` 已可對照實作，且 top-level command 已有 manifest drift test。

但命令面仍有三個系統性問題：

- target / scope 預設不一致，同樣是會寫 target 的命令，有的要求顯式 `--target`，有的偷用預設 target。
- 部分命令把多個不同意圖或重副作用工作流塞在一起，使用者很難從命令名推測實際會做什麼。
- 雖然已有實作參考文件，但尚無一份長期維護的命令分類與設計壓力基線，無法系統化判斷哪些命令要保留、澄清、修 scope、或拆分。

## 設計目標

### 目標

1. 將所有主要命令納入同一套分類欄位與 design pressure 判定。
2. 為 target 與 scope 建立硬性契約，消除隱含預設 target。
3. 對真正混合多種意圖或隱含後處理的命令做顯式化，而不是只補文件。
4. 補齊 top-level 與重要子命令的細部語意表，讓 `docs/ai-dev指令與資料流參考.md` 持續是實作真相。
5. 新增一份長期維護的 taxonomy/reference 文件，作為命令類型與設計壓力基線。

### 非目標

1. 不重新命名 `install / update / clone`。
2. 不引入新的資源型命令樹。
3. 不在本輪把所有命令都改造成 phase pipeline。
4. 不追求本輪全面自動生成所有文件，只要求建立可驗證與可持續維護的結構。

## 文件分工

本輪完成後，相關文件分工固定如下：

### 1. `docs/ai-dev指令與資料流參考.md`

角色：**實作真相**

負責描述：

- 目前有哪些命令與子命令
- 每個命令現在實際做什麼
- 讀寫哪些 state
- 支援哪些參數與預設行為

不負責回答「這個設計好不好」。

### 2. `docs/ai-dev命令分類與設計壓力參考.md`

角色：**長期維護的命令分類基線**

負責描述：

- 命令屬於哪一類副作用
- scope 與 target mode
- 風險等級
- design pressure：`keep / clarify / needs_scope_fix / split`

這份文件在命令行為改動時也必須同步維護。

### 3. `docs/report/2026-03-13-ai-dev-command-classification-assessment.md`

角色：**本輪決策輸出**

負責總結：

- 哪些命令維持現狀
- 哪些命令要澄清
- 哪些命令要修正 scope
- 哪些命令要做顯式拆分或顯式模式

## 分類模型

所有主要命令都使用同一組欄位描述：

- `command_path`
- `intent`
- `side_effect_class`
- `scope`
- `target_mode`
- `reads_state`
- `writes_state`
- `external_operations`
- `confirmation_mode`
- `dry_run_support`
- `risk_level`
- `design_pressure`

### `side_effect_class` 定義

- `read_only`
  - 不寫 state，不做外部修改操作
- `single_write`
  - 主要只寫一類本地 state 或單一 target 狀態
- `multi_stage_pipeline`
  - 有明確的多階段工作流，且先後順序重要
- `system_level_operation`
  - 會動到全域套件、shell、排程、系統服務或其他系統層配置

### `target_mode` 定義

- `none`
- `implicit_default`
- `explicit_single`
- `explicit_multi`

### `design_pressure` 定義

- `keep`
- `clarify`
- `needs_scope_fix`
- `split`

## 已確認的命令分類結果

### `keep`

| command | 結論 | 理由 |
|---------|------|------|
| `clone` | 保留 | 雖為 `state -> targets` 雙 phase，但語意單純，已符合「套用目前 state 到 targets」的心智模型 |

### `clarify`

| command | 結論 | 理由 |
|---------|------|------|
| `install` | 保留命令，補強副作用揭露 | 命令重，但 phase 邊界已清楚，不必再拆命令 |
| `update` | 保留命令，補強副作用揭露 | 語意已穩定為 refresh，不需拆命令 |
| `status` | 保留命令，補 `--section` 類查詢能力 | 本質是聚合 read-only 檢視 |
| `toggle` | 保留命令，補 dry-run / preview / help | 寫入單一 target 狀態，但支援矩陣與預覽不足 |
| `mem auto` | 保留命令，補系統層模式揭露 | 核心問題是排程安裝副作用不夠顯性 |

### `needs_scope_fix`

| command | 結論 | 理由 |
|---------|------|------|
| `list` | 保留命令，明確定義 read-only target 默認為 all | 與寫入 target 的命令應採不同契約 |
| `standards switch` | 改為只處理 project state | 現在不該順手同步 target |
| `standards sync` | target 必須顯式指定 | 不應再偷用預設 `claude` |
| `hooks *` | 改為帶 `--target` 的顯式 scope | 目前命令名泛用，但實作其實只支援 Claude |

### `split`

| command | 結論 | 理由 |
|---------|------|------|
| `init-from` | 將「首次初始化」與「後續更新」拆成不同工作流 | 目前把 template repo 管理、互動式合併、tracking、exclude 設定混在一起 |
| `sync init` | 將 bootstrap / first-sync 模式顯式化 | 目前同時做 repo 建立、ignore、LFS、manifest、push，重副作用不夠顯性 |
| `mem pull` | 將 post-process 顯式化 | 目前 pull 後可能順手 reindex / cleanup，應改成明確模式或 flags |

## Scope / Target 契約

本輪完成後，全 CLI 採用以下硬性規則。

### 規則 1：read-only 命令可以使用隱含 scope

若命令本質是 read-only，`--target` 可以是可選，未提供時代表 `all`。

適用：

- `list`

### 規則 2：任何寫入 target 的命令都必須顯式指定 target

只要命令會改變 target 內容、target 設定或 target 對應資源，就不得使用隱含預設 target。

適用：

- `toggle`
- `standards sync`
- `hooks install`
- `hooks uninstall`
- 未來任何 target write path

### 規則 3：project state 命令預設只改 project state

若命令本質是 project 設定、profile、tracking 或本地專案配置，預設只處理 project state，不應順手寫 target。

適用：

- `standards switch`

### 規則 4：命令名稱若沒有把單一 target 寫死，就不能偷偷綁單一 target

若命令群組名稱是泛用的，scope 必須顯式表示。若目前實作只支援單一 target，也應由 CLI 約束參數，而不是靠隱含行為。

適用：

- `hooks --target claude`

### 具體收斂結果

- `list`
  - `--target` 可選
  - 未指定時列出所有 target
- `toggle`
  - 維持顯式 `--target`
- `standards sync`
  - `--target` 必填
  - 不再有預設 `claude`
- `standards switch`
  - 僅切換 `.standards` 相關狀態
  - 不再自動同步任何 target
- `hooks`
  - 新增 `--target`
  - 目前只允許 `claude`

## 顯式副作用設計

### `init-from`

`init-from` 目前同時承擔：

- template repo clone / update
- 互動式檔案合併
- tracking file 寫入
- `.git/info/exclude` 詢問與設定
- `--update` 的後續更新語意

最終狀態應拆成兩條明確工作流：

- `ai-dev init-from <template>`
  - 僅做首次初始化
- `ai-dev init-from update`
  - 僅做既有專案的更新 / 重套用

設計原則：

- 使用者不再靠 `--update` 觸發另一種意圖
- help、文件與測試各自對齊兩條工作流

### `sync init`

`sync init` 不必一定拆成新命令，但必須讓重副作用 bootstrap/first-sync 路徑變成顯式模式。

允許的最終型態：

- `sync init --mode bootstrap`
- 或等價的 `--bootstrap`

必須明確揭露：

- 會建立 repo
- 會修改 ignore 與 LFS
- 會寫回 remote
- 可能直接 push

### `mem pull`

`mem pull` 的「pull 後順手 reindex / cleanup」不能再是隱含行為。

最終狀態應改為顯式控制，例如：

- `mem pull --reindex`
- `mem pull --cleanup`
- `mem pull --post-process`

實作形式可再定，但原則是：

- 單純 pull 與 pull 後整理必須可分開
- dry-run / help / 測試必須能明確對應

## Clarify 類統一規則

### 規則 1：高風險寫入命令要有 preview 能力

適用：

- `install`
- `update`
- `toggle`
- `mem auto`

若命令會改系統狀態或大量本地 state，就應提供 `--dry-run` 或等價 preview。

### 規則 2：系統層操作必須顯示其作用層級

尤其是：

- `mem auto`
- `install`
- `update`

help 與執行輸出都要讓使用者知道會碰：

- launchd / cron
- 全域套件
- marketplace
- repo refresh

### 規則 3：read-only 聚合命令要支援分區查詢

`status` 應提供 `--section` 或等價篩選能力，至少能分開看：

- tools
- repos
- sync
- project / environment 狀態

### 規則 4：top-level 命令的語意表要細到可預測副作用

`docs/ai-dev指令與資料流參考.md` 必須補齊：

- `install`
- `update`
- `clone`
- `status`
- `list`
- `toggle`
- `init-from`

不只列命令名，還要列：

- 主要 intent
- 寫入狀態
- target 行為
- 顯式/隱含 scope

## 交付產物

本輪最終狀態需要交付以下內容：

1. `docs/ai-dev命令分類與設計壓力參考.md`
2. `docs/report/2026-03-13-ai-dev-command-classification-assessment.md`
3. 更新後的 `docs/ai-dev指令與資料流參考.md`
4. 對應 code 變更：
   - `list`
   - `standards switch`
   - `standards sync`
   - `hooks`
   - `init-from`
   - `sync init`
   - `mem pull`
   - `toggle`
   - `status`
   - `mem auto`
5. 對應測試：
   - 命令行為測試
   - 文件 drift / taxonomy 校驗

## 驗證準則

完成後需能驗證：

1. 所有會寫 target 的命令都不再有隱含預設 target。
2. `standards switch` 不再順手改 target。
3. `hooks` 的 scope 由 CLI 顯式揭露，而非靠文件猜測。
4. `init-from`、`sync init`、`mem pull` 的重副作用或二段工作流已改成顯式模式。
5. `docs/ai-dev指令與資料流參考.md` 與 `docs/ai-dev命令分類與設計壓力參考.md` 能反映實作。
6. 對應測試能防止命令契約再次 drift。

## 風險與取捨

### 風險

- `init-from` 的行為調整最可能影響既有使用者工作流。
- `standards` 與 `hooks` 的 scope 契約收斂可能需要同步修 help、README 與使用教學。
- `mem pull` / `mem auto` 涉及系統與外部服務，測試上需要更清楚的 fake/stub 邊界。

### 取捨

- 本輪選擇「最終狀態一次定義」，但不代表實作上必須單一 commit 完成。
- 不重新命名高階命令，保留既有使用者心智；重點放在命令契約一致化。
- 不全面 phase 化全部子系統，而是先把 scope 契約、顯式副作用與分類基線定下來。

## 結論

`ai-dev` 的下一階段不是再發明更多命令，而是把所有命令放回可預測的契約之下。最終狀態應同時滿足三件事：

1. 使用者能從命令名與 flags 推測 scope 與副作用。
2. 維護者能從 taxonomy/reference 文件快速判斷某個命令該保留、澄清、修 scope 還是拆分。
3. 文件、實作與測試形成基本的互相約束，避免命令面再次長成只靠口耳相傳維護的狀態。

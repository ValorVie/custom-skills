# ai-dev CLI framework architecture

> **版本**：2.0.0
> **更新日期**：2026-08-28

`ai-dev` 是多工具 AI 開發環境的 control plane。它管理 CLI tools、repositories、npx skill desired state、非 skill resources、project projection 與 migration；第一方 skill content 則由獨立的 [`ValorVie/ai-dev-skills`](https://github.com/ValorVie/ai-dev-skills) 維護。

## Repository responsibilities

| Repository | 負責內容 |
| --- | --- |
| `ValorVie/custom-skills` | ai-dev CLI、commands、agents、plugins、project-template、OpenSpec、upstream policies 與 `npx-skills.yaml` |
| `ValorVie/ai-dev-skills` | 第一方 installable skills、skill tests 與 collection validation |

`custom-skills` 不再保存或分發第一方 `skills/` content。新 skill 只有在 `upstream/npx-skills.yaml` 明確列出後，才會進入 ai-dev baseline。

## Runtime modules

```text
script/
├── main.py
├── cli/                     command manifest 與 phase selection
├── commands/                user-facing commands
├── models/                  execution plan 等資料模型
├── services/
│   ├── npx_skills/          manifest、grouped commands、migration、detach
│   ├── pipeline/            install/update/clone orchestration
│   ├── repos/               repository refresh
│   ├── targets/             retained resource distribution
│   └── tools/               CLI tool lifecycle
├── utils/
│   ├── manifest.py          clone-owned resource tracking
│   ├── shared.py            paths、source lookup、distribution、toggle helpers
│   ├── paths.py
│   └── custom_repos.py
└── tui/
```

## Command pipeline

### `ai-dev install`

```text
tools → repos → npx-skills → targets
```

- `tools`：補齊必要 CLI。
- `repos`：clone／refresh framework 與保留的 upstream repositories。
- `npx-skills`：安裝明確 manifest 中的 global skills。
- `targets`：分發 commands、agents、workflows、plugins、custom repos 與 ECC 白名單 resources。

### `ai-dev update`

```text
tools → repos → npx-skills
```

update 不執行 targets。需要重跑 clone-owned resource distribution 時，另外執行 `ai-dev clone`。

### `ai-dev clone`

clone 只處理 clone-owned resources。第一方與其他 npx-managed canonical IDs 會被排除，不進入新的 ManifestTracker entries。

分發順序：

1. framework commands、agents、workflows、plugins。
2. custom repos。
3. ECC whitelist。

## Skill desired state

`upstream/npx-skills.yaml` 是 ai-dev 的 reviewable desired state。它逐 package 列出 canonical IDs、source label 與 rationale。

global add 只指定 `claude-code`、`codex`、`gemini-cli`、`opencode`、`antigravity`。Eve 與 PromptScript 不支援 global skill installation，因此不屬於 baseline targets；需要時在各自專案內安裝。

manifest loader 會拒絕：

- 缺少 repository。
- 空 skill list。
- wildcard skill。
- 同一 canonical ID 重複或由多個來源宣告。

同 package 的 skills 以一個 command 處理。第一方 install／update 使用 guarded add；其他 packages 維持原生 add／update。部分 package 失敗時，成功項目可以保留，但 phase 仍以 exit 1 結束，且失敗項目不會 detach 舊 ownership。

## First-party base + persistent overlay

`ai-dev-first-party` 由 `FirstPartyReconciler` 管理。npx 負責 upstream base；ai-dev
只保存使用者的本機 overlay。installed skill 是 base 加 overlay 的 materialized view，
但不進入 target ManifestTracker，也不使用 copy、toggle 或 orphan cleanup。

每個檔案比較四個版本：上次接受的 upstream base、目前 upstream source、持久
overlay、目前 installed local。

| 分類 | Source | Local intent | 動作 |
| --- | --- | --- | --- |
| `clean` | 未變或單獨變更 | 無本機 override | 使用 upstream |
| `local-only` | 等於 base | 有本機 override | 自動保存或更新 overlay |
| `both-changed` | 不同於 base | 有本機 override | keep-local、use-upstream 或 abort |
| `no-base` | 無可信 base | 與 source 不同 | keep-local、use-upstream 或 abort |

missing 是明確狀態；刪除使用 tombstone，不與空檔案混淆。`.DS_Store` 不屬於
skill 內容，不參與 hash 或 root comparison。binary 仍可用 hash、size 與存在狀態
決定；skill tree 內的 symlink 或特殊檔案 fail closed。agent projection root symlink
若解析到 canonical active root，則以 real path 去重；指向其他位置時仍停止。

state 與 overlay 路徑如下：

- `~/.config/ai-dev/manifests/npx-first-party.yaml`
- `~/.config/ai-dev/overlays/npx-first-party/`
- `~/.config/ai-dev/backups/npx-first-party/`
- `~/.config/ai-dev/transactions/npx-first-party/`

所有第一方 files 先完成 planning 與 decision resolution，之後才開始 mutation。每個
skill 依序執行完整 roots backup、npx base、pure-base verification、overlay
materialization、effective verification、atomic state commit。npx non-zero、內容與
snapshot 不符、overlay／state 寫入失敗都會 rollback。未完成 journal 會在下一次執行
前先 recovery；無法證明 rollback 時停止，不開始新的 transaction。

## First-party migration

第一方 skills 從舊 copy model 遷移到 npx 時，使用以下 state：

```text
PREPARED → PUBLISHED → INSTALLED → VERIFIED → DETACHED
```

schema v1 directory guard 會用記錄的 source commit 取得舊 base tree，再展開為
schema v2 per-file state。舊 target copies 的純 base／source 副本不算不同的本機意圖；
一致的本機修改可合併成單一 canonical overlay。若不同 targets 有不同修改，該 skill
在 npx 前停止，要求使用者先選擇 canonical 版本，不建立 per-agent overlay。

`custom-simplify → simplify` 使用相同 planner 與 transaction。overlay 已保存、npx
base 與 final materialized tree 都驗證成功後，才移除舊 alias 與 ManifestTracker
ownership。

npx add 成功後還要驗證 canonical path、frontmatter name、lock source 與必要 agent path。全部通過後才移除舊 manifest entries。legacy alias 另做備份後清理。

## Clone ManifestTracker

ManifestTracker 只管理 clone-owned resources，保存 source、hash、file-level base 與 decision。用途包括：

- 3-way conflict classification。
- 使用者修改保護。
- retained source 的 orphan cleanup。
- per-source update summary。

npx-managed skill 不建立新的 clone entry。migration 尚未完成時，舊 `source=custom-skills` entry 會暫時保留，不能由一般 orphan cleanup 移除。

## List、toggle 與 standards

- `ai-dev list` 優先讀 declarative npx manifest 判斷 source；manifest 不可讀時，無法證明的項目標成 `unknown`，不執行 mutation。
- `custom-simplify` 顯示為 `ai-dev-skills (legacy: simplify)`，canonical ID 是 `simplify`。
- `ai-dev toggle` 對 npx-managed skill 採 fail closed，提示原生 npx command。
- resource-disable 不跟隨、複製或刪除 npx canonical copy／symlink。
- standards dry-run 標示 npx-managed skills；實際切換在 mutation 前停止。

## Project-level resources

project-template 內的 repo-local skills 仍隨專案版本控制，不改用 global npx installation。project init、hydrate、reconcile 與 doctor 的 ownership 不受本次 global skill migration 影響。

## Safety boundaries

- dry-run 不執行 npx、不寫 lock、不清 manifest ownership。
- modified／unknown target 不得用 `--yes` 或 force 覆蓋。
- npx 與 clone source 同名時，在寫入該 skill 前停止。
- remote repository creation、release、tag 與 push 需要目前工作流程的明確授權。
- 已安裝、已驗證與已 detach 是不同狀態，不得只用「完成」合併描述。

## Related documents

- [Resource ownership and distribution](copy-architecture.md)
- [ai-dev command and data-flow reference](../../ai-dev指令與資料流參考.md)
- [OpenSpec change: externalize-first-party-skills](../../../openspec/changes/externalize-first-party-skills/proposal.md)

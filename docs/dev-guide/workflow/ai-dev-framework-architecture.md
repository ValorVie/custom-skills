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

manifest loader 會拒絕：

- 缺少 repository。
- 空 skill list。
- wildcard skill。
- 同一 canonical ID 重複或由多個來源宣告。

同 package 的 skills 以一個 command 安裝或更新。部分 package 失敗時，成功 package 可以保留，但 phase 仍以 exit 1 結束，且失敗項目不會 detach 舊 ownership。

## First-party migration

第一方 skills 從舊 copy model 遷移到 npx 時，使用以下 state：

```text
PREPARED → PUBLISHED → INSTALLED → VERIFIED → DETACHED
```

preflight 對每個 target／skill 分類：

- `missing`：沒有舊副本，可以安裝。
- `unchanged`：target 與 stored manifest base 相同，可以安裝。
- `modified`：使用者或其他流程改過，保留並阻擋該 skill。
- `unknown`：無法證明 ownership，保留並阻擋。
- `already-migrated`：npx lock source 與 canonical install 已符合。

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

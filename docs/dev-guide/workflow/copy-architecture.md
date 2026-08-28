# ai-dev 資源 ownership 與分發架構

> **版本**：3.0.0
> **更新日期**：2026-08-28

ai-dev 將 global skill 安裝與 framework resource 分發拆成兩條管線。同一 canonical skill ID 只能有一個 writer；npx-managed skill 不得再由 clone 或 ManifestTracker 覆蓋。

## Pipeline

```text
ai-dev install
  tools → repos → npx-skills → targets

ai-dev update
  tools → repos → npx-skills

ai-dev clone
  targets
```

| Phase | 主要工作 |
| --- | --- |
| `tools` | 安裝或更新必要 CLI tools |
| `repos` | 更新 `custom-skills`、ECC 與其他保留的 repositories，並同步 `npx-skills.yaml` |
| `npx-skills` | 依明確 manifest 安裝或更新 global skills |
| `targets` | 分發 commands、agents、workflows、plugins、custom repos 與 ECC 白名單資源 |

`npx-skills` 在 `targets` 前執行。fresh install 會先建立 skills，再分發保留的 framework resources。

## Ownership matrix

| 資源 | Canonical source | Writer |
| --- | --- | --- |
| ai-dev 第一方 global skills | [`ValorVie/ai-dev-skills`](https://github.com/ValorVie/ai-dev-skills) | `npx skills` |
| manifest 中的第三方 global skills | 各公開 upstream | `npx skills` |
| ECC 白名單 skills | `~/.config/everything-claude-code/` | `ai-dev clone` + ManifestTracker |
| custom repo skills | `~/.config/ai-dev/repos.yaml` 註冊來源 | `ai-dev clone` + ManifestTracker |
| project-template repo-local skills | `project-template/` | project init/projection |
| commands、agents、workflows、plugins | `ValorVie/custom-skills` 或明確 upstream | `ai-dev clone`／原生 plugin manager |

## npx-managed skills

Repository desired state 存在 `upstream/npx-skills.yaml`。`~/.agents/.skill-lock.json` 是目前機器的 npx state，不取代 repository manifest。

規則：

- 每個 package 必須明確列出 canonical IDs；禁止 wildcard。
- global agent targets 固定列出 `claude-code`、`codex`、`gemini-cli`、`opencode`、`antigravity`，不使用 `-a '*'`。
- 同一 repository 的 skills 合併成一個 add/update command。
- manifest 缺 repo、空 skills、重複 ID 或多來源同名時，phase 在執行 npx 前失敗。
- first-party migration 使用 schema v1 source commit 取得逐檔 base。相同的舊 target modifications 可合併成單一 overlay；不同修改 fail closed，不建立 per-agent overlay。
- first-party ongoing update 讀取 `~/.config/ai-dev/manifests/npx-first-party.yaml` 與 `~/.config/ai-dev/overlays/npx-first-party/`，維持 `clean`、`local-only`、`both-changed`、`no-base` 判斷；其他 npx packages 不使用這層 reconcile。
- `local-only` 與 keep-local 保存成持久 overlay。use-upstream 清除該檔案 overlay，並在 `~/.config/ai-dev/backups/npx-first-party/` 保留被覆蓋內容。
- 每個第一方 skill 以獨立 transaction 執行 npx、pure-base verification、overlay materialization、effective verification 與 atomic state commit。全部通過後才 detach 舊 manifest ownership；失敗會 rollback。

### 一次性 legacy mapping

`custom-simplify → simplify` 會先進入同一個 per-file planner。舊 target copies 的本機內容一致時可保存成 canonical overlay；內容不同時停止。成功驗證後才清理舊 alias，transaction backup 位於 `~/.config/ai-dev/backups/npx-first-party/`。

## clone-managed resources

`ai-dev clone` 保留：

1. framework commands、agents、workflows 與 plugins。
2. `repos.yaml` 註冊的 custom repo resources。
3. `upstream/distribution.yaml` 啟用的 ECC resources。
4. clone-owned resource 的 hash、衝突與 orphan cleanup。

clone prescan 若發現 npx-managed canonical ID 也由 ECC 或 custom repo 啟用，會在寫入該 skill 前以 exit 1 停止。不要用 force 覆蓋這種 ownership conflict。

一般 clone 會暫時保留舊 manifest 中尚未完成 migration 的 npx-managed entries，避免提前 orphan-clean。完成 npx 讀回驗證後，migration 才會移除這些 entries。

## Toggle 與 standards boundary

`toggle`、resource-disable 與 standards profile 不得搬動 npx-managed skill directory 或 symlink。

- `toggle` 回傳 exit 1，並在 agent mapping 已驗證時顯示原生 `npx skills remove/add` 指令。
- `standards --dry-run` 將項目標成 `npx-managed`。
- 實際 profile switch 若要改動 npx-managed skill，會在 filesystem mutation 前停止。
- 非 npx-managed resources 維持既有 disabled-directory 行為。

目前已驗證的提示 mapping：

| ai-dev target | npx agent |
| --- | --- |
| `claude` | `claude-code` |
| `codex` | `codex` |
| `agy` | `gemini-cli` |

Antigravity 的舊 ai-dev path 與 npx path 不一致，因此維持 fail closed，不猜測 mapping。

## 主要實作檔案

| 目的 | 檔案 |
| --- | --- |
| npx manifest parsing／commands | `script/services/npx_skills/config.py`、`install.py` |
| first-party migration | `script/services/npx_skills/migration.py` |
| manifest detach／npx source lookup | `script/services/npx_skills/manifest_sync.py` |
| retained target distribution | `script/utils/shared.py`、`script/services/targets/` |
| ECC whitelist | `upstream/distribution.yaml`、`upstream/ecc-catalog.yaml` |
| desired skill inventory | `upstream/npx-skills.yaml` |

## 驗證

```bash
ai-dev install --only npx-skills --dry-run
ai-dev clone --dry-run
uv run python -m pytest tests/services/npx_skills tests/test_npx_clone_ownership.py
```

dry-run 通過不代表 npx 已安裝、migration 已 detach 或 clone 已寫入 target。實際狀態必須分開讀回。

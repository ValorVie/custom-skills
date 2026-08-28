## Context

變更動機見 `proposal.md`。目前 ai-dev 已有 YAML 驅動的 `npx-skills` phase，但每個 skill 會各跑一次 npx 指令；`copy_custom_skills_to_targets()` 同時把 `custom-skills/skills/` 分發到多個 agent 目錄，並在 ai-dev manifest 記錄 ownership。`toggle`、resource-disable 與 standards profiles 也假設 skill target 是可由 ai-dev 複製及刪除的一般目錄。

初始第一方清單有 19 個 canonical skill IDs。其中一個來源目錄名為 `custom-simplify`，frontmatter ID 則是 `simplify`。部分 skills 含有必須隨 skill 安裝的 scripts 與 evals；另有檔案包含內部範例、離開 skill 根目錄的相對連結，或指向 npx 不會安裝的 companion plugins。

進行中的 `ecc-whitelist-distribution` change 要求 ECC skills 繼續由 `ai-dev clone` 與 ManifestTracker 管理，本設計不得取代該契約。OpenSpec planning home 也只允許寫入 `custom-skills`；建立或寫入第二個 checkout 屬於外部實作階段，必須另外確認目標與交接方式。

## Goals / Non-Goals

**Goals:**

- 讓第一方 skill 內容與 ai-dev framework 分開發布。
- 以 `ValorVie/ai-dev-skills` 作為初始 19 個 skills 的公開 canonical source。
- 只用既有 npx-skills phase 安裝與更新第一方 skills。
- 從 clone、ManifestTracker、disabled directory 與 standards profile 移除第一方 skill ownership，不影響其他資源類型。
- 保留使用者修改過的安裝內容，並提供可回復的 migration。
- 讓抽離後的 repository 可獨立驗證、符合公開邊界，且支援單一 skill 安裝。

**Non-Goals:**

- 不把 ECC 或任意 custom repo skills 改由 npx 管理。
- 不把 project-template repo-local skills 改為 global installation。
- 不因 commands、agents、workflows 或 plugins 與 skill 有關，就一併搬移。
- 不重新命名既有 `custom-skills-*` canonical IDs，也不重新命名 framework repository。
- 不新增 npm package、custom registry、第二種 lock format 或自製 skill installer。
- 未在操作點取得批准前，不建立 GitHub repository，也不 push remote content。

## Decisions

### 1. 使用單一公開 collection repository

新來源 SHALL 使用以下結構：

```text
ai-dev-skills/
├── skills/
│   ├── cloud-infrastructure-security/
│   ├── custom-agent-router/
│   ├── simplify/
│   └── ...
├── tests/
├── AGENTS.md
├── README.md
├── LICENSE
└── CHANGELOG.md
```

每個 skill 維持 self-contained。根目錄測試檢查跨 skill 規則，例如 frontmatter 名稱唯一、內部連結有效及公開邊界。skill 專用的 scripts、fixtures 與 evals 留在該 skill 內，避免透過 npx 單獨安裝時漏掉 runtime inputs。

替代方案：

- 不採用每個 skill 一個 repository，因為同一維護者需要重複處理 release、license 與 CI。
- 不把 collection 留在 `custom-skills` 再安裝 GitHub subtree URL，因為 skill-only 變更仍會共用 framework history 與發布流量。

### 2. 從淨化後的 snapshot 建立新 repository

第一個 commit SHALL 包含完成淨化及 canonical name 正規化的 19 個 skill 目錄。release notes 或 commit metadata SHALL 記錄來源 framework commit，但 SHALL NOT 匯入舊 subtree history。

這項決定以新 repository 的逐檔歷史換取乾淨的公開 Git history。需要追查時，既有公開 `custom-skills` repository 仍保留先前歷史。不採用 subtree split 或 history filter，因為現有 skill history 含有不應複製到新公開 repository historical objects 的內部範例名稱。

### 3. 只使用 frontmatter `name` 作為 skill ID

新 repository 的目錄名 SHALL 與 frontmatter name 相同。初始 canonical inventory 如下：

```text
cloud-infrastructure-security
custom-agent-router
simplify
custom-skill-creator
custom-skills-dev
custom-skills-doc-updater
custom-skills-doc-writer
custom-skills-ecc-analyze
custom-skills-git-commit
custom-skills-notify
custom-skills-plan-analyze
custom-skills-threads-research
custom-skills-tool-overlap-analyzer
custom-skills-upstream-ops
discuss-multi-ai
eli5
first-principles
wiki
work-log-claude
```

`custom-simplify → simplify` 是一次性的 legacy path mapping。本次不建立通用 alias system。

### 4. ai-dev YAML 保存 desired state，npx lock 保存 machine state

`upstream/npx-skills.yaml` 繼續作為可審查的 baseline manifest。npx global lock 是工具管理的 local state，不提交到 repository，也不作為跨機器 source of truth。

manifest SHALL 明確列出每個第一方 canonical ID。不使用 wildcard installation，避免新的公開 skill 在審查前自動進入所有 ai-dev baseline。

global add 的 agent targets 也使用明確清單：`claude-code`、`codex`、`gemini-cli`、`opencode`、`antigravity`。Eve 與 PromptScript 只支援 project scope，不納入 ai-dev global phase；需要時由使用者在對應專案內手動安裝。loader 保留單一字串格式的讀取相容性，但 repository baseline 使用 YAML 清單。

executor SHALL 依 repository 分組，每個 package 建立一個 add command，並重複傳入 `--skill`。update 可一次傳入目前 CLI 支援的多個 skill IDs。config schema 維持 version 1 相容，只加強 validation，不新增檔案格式。

### 5. 第一方 target files 只由 npx 管理

migration 後，framework 不再把 `custom-skills/skills/` 當成 Stage 3 第一方來源。保留的 distribution flow 繼續管理 commands、agents、workflows、plugins、custom repos 與 ECC。

prescan 與 distribution SHALL 對每個 clone source 過濾 canonical npx-managed IDs。這可防止同名 custom repo 或 ECC skill 靜默覆蓋 npx content。同名衝突必須在寫入前停止該 skill，並列出兩個來源。

不保留 npx 與 ManifestTracker 雙 writer，因為 npx symlinks、clone overwrite、orphan cleanup 與 disabled-directory moves 無法形成可靠的共同 ownership model。

### 6. ai-dev toggle 與 standards operations 採 fail closed

第一版實作 SHALL NOT 在 `ai-dev toggle` 內包裝 `npx skills remove/add`。若 canonical ID 由 npx 管理，toggle 與 resource-disable 回傳 exit code 1，不修改 filesystem，並顯示可複製的原生 npx command。

只有已安裝 npx CLI 與 target path 一致時，才使用下列已知 mapping：

- `claude` → `claude-code`
- `codex` → `codex`
- `agy` → `gemini-cli`，因為 ai-dev agy 讀取 `~/.gemini/skills/`

Antigravity 與未來 target 必須先做 path probe，ai-dev 才能顯示具體 agent ID。等 per-agent removal、canonical cleanup 與 reinstallation semantics 都有測試後，再另案評估 native npx adapter。

這比自動 delegation 多一個人工步驟，但可避免 ai-dev 在 mapping 不完整時破壞 symlinks 或改動 npx lock state。

### 7. companion integrations 與 skill installation 分開

若 skill 引用目錄外的 plugin、hook 或 command，抽離後的 skill SHALL 連到公開的 native installation entry，並說明 npx 不會安裝 companion integration。companion resource 在本次變更中留在原 repository。

例如 notification skill 可以保留 self-contained scripts；Claude plugin 則繼續作為獨立安裝的 framework integration。文件不得宣稱 npx 會管理它不負責的 resource types。

### 8. 使用有閘門的 migration state machine

migration 使用以下 states：

```text
PREPARED → PUBLISHED → INSTALLED → VERIFIED → DETACHED
```

- `PREPARED`：sanitized candidate 已完成本機 validation，尚未要求 remote repository。
- `PUBLISHED`：使用者核准的公開 repository 與初始 revision 已可存取。
- `INSTALLED`：明確 inventory 的 npx add 已成功。
- `VERIFIED`：已讀回 canonical IDs、agent-visible paths、source metadata 與 content。
- `DETACHED`：已移除舊 manifest ownership 與未修改的 legacy copies；framework source directories 可以刪除。

任何 stage 都不自動代表下一個 stage 已完成。在 `VERIFIED` 前失敗時，舊 ownership 必須保持不變。local hash mismatch 或 unknown ownership 只停止受影響 skill，但整體 migration 不得宣稱完成。

## Risks / Trade-offs

- [Risk] 新 repository 不會保留方便查找的 per-file history。→ 記錄來源 framework commit，需要追查時使用既有 repository。
- [Risk] 第一方 skill 依賴目錄外檔案。→ 發布前檢查 escaping links 與 runtime inputs；把必要檔案移入 skill，或改成公開 integration reference。
- [Risk] npx 改變 agent IDs 或 global paths。→ 記錄驗證使用的 `skills --version`，用 list/path probes 驗證 mapping；無法證明時停止。
- [Risk] `--yes` 覆蓋使用者修改過的 target。→ add 前比較舊 manifest base 與現場內容；保留或備份修改內容，並要求明確決定。
- [Risk] `custom-simplify` 與 `simplify` 並存。→ canonical install 通過且舊路徑可證明未修改後，才套用一次性 mapping。
- [Risk] 同名 ECC 或 custom repo skill 繞過第一方 filter。→ 寫入前檢查所有來源的 canonical IDs，並加入 collision tests。
- [Risk] framework release 與 skill release 暫時不相容。→ 先發布並驗證 skill repository，再發布 framework integration；保留上一個 known-good source revision 供 rollback。
- [Trade-off] 第一方 skill toggle 改成有指引的手動 npx 操作。→ 第一版先維持清楚 ownership；等 npx lifecycle semantics 有測試後再評估自動化。

## Migration Plan

### Phase 1：準備 candidate

1. 固定來源 framework commit，並從 frontmatter 產生 canonical inventory。
2. 把 19 個 skill 目錄複製到獨立 local candidate，不匯入 Git history。
3. 將 `custom-simplify/` 改名為 `simplify/`。
4. 移除內部範例與 private paths、修正 escaping links，並記錄 companion integrations。
5. 加入 root validation，執行每個 skill 的直接測試。

若 `npx skills add <local-path> --list` 的結果與 manifest inventory 不完全相同，立即停止。

### Phase 2：發布公開來源

1. 列出準確 repository name、visibility、初始檔案與發布命令。
2. 取得建立 repository 與首次 push 的批准。
3. 建立 `ValorVie/ai-dev-skills`，發布 sanitized initial commit，建立 known-good revision 或 tag。
4. 對 remote source 重跑 discovery 與 public-boundary checks。

framework integration 前的 rollback：ai-dev 不引用 remote source，也不自動刪除公開 repository。

### Phase 3：加入 framework support

1. 將第一方 package 與明確 IDs 加入 `upstream/npx-skills.yaml`。
2. 加強 manifest validation，依 package 分組 add/update commands。
3. 加入 migration preflight、canonical legacy mapping 與 post-install readback。
4. 從 Stage 3 source configuration 與 clone ownership 移除第一方 skills。
5. 更新 list、toggle、resource-disable 與 standards boundaries。

npx phase 保持在 targets phase 之前，讓 fresh install 先取得第一方 skills，再分發保留的資源。

### Phase 4：遷移既有安裝

1. 讀取舊 target manifests，比較每個第一方 target 與 stored base。
2. 若 target 已修改或 ownership 未知，停止並保留內容。
3. 安裝明確的 npx inventory。
4. 驗證 canonical IDs 與 agent-visible locations。
5. 移除舊 manifest entries 與未修改的 legacy paths，包含 mapped `custom-simplify` path。
6. 重跑 clone，確認它不會重新取得第一方 ownership。

detach 後的 rollback：需要時還原 preserved content，回復上一個 framework release，再執行其 clone flow。rollback 不得移除 user-modified backups。

### Phase 5：移除 framework content 並更新文件

1. remote source 與 migration tests 通過後，從 `custom-skills` 移除已遷移的 `skills/` content 與 content-specific tests。
2. framework integration tests 留在 `custom-skills`；skill content tests 移到 `ai-dev-skills`。
3. 更新 README、architecture/data-flow references、skill inventory、install/update/list/toggle 文件與 CHANGELOG。
4. 驗證 ECC、custom repos 與 project-template skills 仍使用既有路徑。

## Open Questions

無。Antigravity path support 是具有 fail-closed 結果的 implementation preflight，不影響本次 ownership model。

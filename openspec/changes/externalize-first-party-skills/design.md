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
- 第一方 skills 完成 npx ownership 移交後，仍保留 `clean`、`local-only`、`both-changed`、`no-base` 衝突判斷。
- 第一方 skills 保留原本的 per-file diff、keep-local、use-upstream、abort 與 local-only restore；local 選擇要能跨 npx update 與直接原生 npx 操作持續存在。
- 讓抽離後的 repository 可獨立驗證、符合公開邊界，且支援單一 skill 安裝。

**Non-Goals:**

- 不把 ECC 或任意 custom repo skills 改由 npx 管理。
- 不把 project-template repo-local skills 改為 global installation。
- 不因 commands、agents、workflows 或 plugins 與 skill 有關，就一併搬移。
- 不重新命名既有 `custom-skills-*` canonical IDs，也不重新命名 framework repository。
- 不新增 npm package、custom registry、自製 skill installer，或為第三方 npx packages 增加 guard state。
- 不支援 per-agent overlay；同一 canonical skill 只保留一份所有 agents 共用的 local overlay。
- 未在操作點取得批准前，不建立 GitHub repository，也不 push remote content。

## Decisions

### 1. 使用單一公開 collection repository

新來源 SHALL 使用以下結構：

```text
ai-dev-skills/
├── .claude-plugin/
│   └── plugin.json
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

`.claude-plugin/plugin.json` 只負責宣告 collection 分組，並明確列出全部
`./skills/<canonical-id>`。它讓 `npx skills` 的互動 picker 提供可整組選取的
`Ai Dev Skills` group，不改變單一 skill 的安裝路徑或 ai-dev baseline 清單。
`skills@1.5.22` 由 group row 整組選取；`skills@1.5.23` 以上另有頂層
`Select All`。本次不新增 `.claude-plugin/marketplace.json`，因為 Claude Code
native marketplace 不是這個 npx picker 問題的必要條件。

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

### 5. 第一方 target 使用 base + overlay 分層 ownership

migration 後，framework 不再把 `custom-skills/skills/` 當成 Stage 3 第一方來源。保留的 distribution flow 繼續管理 commands、agents、workflows、plugins、custom repos 與 ECC。

prescan 與 distribution SHALL 對每個 clone source 過濾 canonical npx-managed IDs。這可防止同名 custom repo 或 ECC skill 靜默覆蓋 npx content。同名衝突必須在寫入前停止該 skill，並列出兩個來源。

npx 只擁有 upstream base layer。ai-dev 不以 clone、toggle、disabled directory 或 orphan cleanup 改寫該 base；ai-dev 另擁有 local overlay layer，並在 npx 完成後 materialize overlay。installed skill directory 是 base + overlay 的結果，不是任何一方單獨的真相來源。

local overlay 必須保存實際 bytes 或 deletion marker，不能只保存 hash 或 decision。這讓使用者直接執行原生 npx、暫時清掉 installed overlay 後，下一次 ai-dev reconcile 仍能恢復 local intent。

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

### 9. FirstPartyReconciler 是單一深 module

`script/services/npx_skills/install.py` 只辨識 package source，將 `ai-dev-first-party` 交給一個 reconcile interface；不得知道 base retrieval、per-file classification、prompt、overlay、backup、rollback 或 verification 的內部步驟。其他 packages 繼續走現有 npx passthrough。

```text
npx-skills phase
  ├─ third-party → NpxPassthrough
  └─ ai-dev-first-party → FirstPartyReconciler.reconcile(...)
                           ├─ SourceSnapshot
                           ├─ ThreeWayPlanner
                           ├─ DecisionResolver
                           ├─ OverlayStore
                           ├─ NpxInstaller
                           └─ Transaction + Verifier
```

共用 `manifest.py` 中的 `FileEntry`、hash、diff 與 decision primitives；不得直接重用 `_v2_classify_and_resolve()`，因為它綁定 clone target、ManifestTracker 與 copy orchestration。

### 10. 使用 overlay-aware per-file 3-way model

每個檔案使用四個版本：上次接受的 upstream base `B`、目前 upstream source `S`、已保存的 overlay `O`、目前 installed local `L`。overlay 存在時，`O` 是持久 local intent；`L` 若又偏離 `O`，則是新的 local candidate。

SourceSnapshot adapter 取得 current HEAD，並依 manifest 中的 base commit lazy fetch 舊 tree／blob。舊 commit 仍可取得時提供完整 `Ds`／`Dl`；無法取得時該 file 才降級為 `no-base`，不得用 current source 冒充 base。

```text
source unchanged + no local override → clean
source changed   + no local override → clean source-only
source unchanged + local override    → local-only
source changed   + local override    → both-changed
base unknown + source/local different → no-base
```

檔案集合取 base、source、local、overlay 的 union。missing 是明確狀態，不得當成空字串；local deletion 以 overlay tombstone 保存。`.DS_Store` 等平台 metadata 不屬於 skill 內容，不得改變 file map、directory hash 或 planner 結果。新增 upstream file、local-only new file、upstream deletion、local deletion、binary file 與 skill tree 內的 symlink／unsupported type 都必須有測試與 fail-closed 結果。

### 11. keep-local 是持久 overlay，不使用 one-revision skip memory

`local-only` 自動保存或更新 overlay，不需要 prompt。`both-changed` 與內容不同的 `no-base` 在 TTY 顯示：

```text
衝突：<path>
狀態：<上游與本機都已修改／沒有可信的共同基準>

查看差異：
  [Ds] 比較上游版本與上次共同基準
  [Dl] 比較本機版本與上次共同基準
  [Dc] 比較上游版本與本機版本

處理方式：
  [K] 保留本機內容／刪除狀態，存成持久覆寫層；後續更新仍會套用
  [O] 採用上游內容／刪除狀態；系統會先備份目前本機內容，再覆蓋
  [A] 中止本次第一方 skills 更新；目前尚未寫入任何變更
```

`no-base` 沒有可信 base，因此 `Ds`／`Dl` 必須標成不可用，prompt 只列 `Dc/K/O/A`。`K` 將 local bytes 或 deletion marker 保存為持久 overlay；`O` 移除該檔案 overlay，並採用 upstream；`A` 在任何第一方 mutation 前停止。所有 overwrite 都保留 transaction backup，不提供無備份的 force path。

non-interactive 時，`clean` 與 `local-only` 可自動處理；未解決的 `both-changed`／`no-base` 跳過整個 skill、允許其他安全 skills 繼續，phase 最後 exit 1。不得自動選擇 keep-local 或 overwrite。

### 12. Apply 使用可回復 transaction

所有第一方檔案先完成 planning 與 decision resolution，才開始 mutation。每個要交給 npx 的 skill 先保存獨立的完整 installed roots 與 transaction journal。全部 safe skills 都到達 `BACKED_UP` 後，同一 repository 只執行一次 grouped npx command，並以多個明確 `--skill <canonical-id>` 傳入 safe inventory；不得用 wildcard 取代 manifest allowlist。

```text
capture overlay candidates per skill
→ backup every safe skill
→ one grouped npx add for explicit safe IDs
→ verify pure base per skill
→ rollback only failed verification items
→ materialize overlays / tombstones for verified items
→ verify effective trees
→ atomically commit successful schema v2 state
→ detach successful legacy ownership
```

npx command 非零時，所有參與該 command 的 skills 都 rollback。npx 回傳 0 但只有部分 skill 通過 base／lock／path verification 時，只 rollback 失敗項；其餘成功項可共同提交 state。overlay apply failure、effective mismatch 或 state commit failure 都必須從對應 transaction backup 還原，保留舊 manifest／overlay，不 detach，並 exit 1。下次執行若發現未完成 journal，先恢復或明確停止，不直接開始新 transaction。

transaction state 為：

```text
PLANNED → BACKED_UP → BASE_APPLIED → OVERLAY_APPLIED → VERIFIED → COMMITTED
```

grouped state commit 前，每個 `VERIFIED` journal 先記錄預期 `SkillState` fingerprint 與 backup retention。若程序在 atomic manifest write 後、全部 journals 完成 `COMMITTED` 前中斷，下次 recovery 以 manifest 中該 skill 的 fingerprint 判斷：吻合時完成 commit cleanup，不吻合時 rollback。不得因逐 journal finalize 的 crash window 把已共同提交的 state 部分回復。

只有 `COMMITTED` 可清除暫存 transaction。使用者明確選擇 use-upstream 的舊 local content 要移入可讀的 timestamped backup；純 clean 更新成功後的 transaction backup 可以清除。

source snapshot 與 npx 下載之間無法用任意 commit SHA pin 時，以 post-install base verification 防止 TOCTOU；內容不符就 rollback。

### 13. 單一 canonical overlay 與舊 target consolidation

Codex、Gemini CLI、OpenCode、Antigravity 使用 universal `.agents/skills`；Claude Code 使用自己的 root 或 symlink。reconcile 依 real path 去重；agent projection root symlink 若解析到已知 active root，視為同一份內容。指向未知位置的 root symlink 與 skill tree 內的 symlink 仍 fail closed。overlay 套用到 canonical 與任何獨立 copy root。

新架構只允許一份 canonical overlay。舊 ai-dev target copies 完全相同時可自動合併並安全清理；若不同 targets 有不同 local modifications，migration 必須停止並要求選擇 canonical 版本或另建不同 canonical skill ID，不建立 per-agent overlay。

### 14. schema v1 自動遷移為 per-file schema v2

現有 `~/.config/ai-dev/manifests/npx-first-party.yaml` directory entries 保存 source commit，可從該 commit 取得 base tree，並展開成 per-file entries。directory hash 仍吻合時自動遷移；不吻合時以 base commit、current source、local tree 做逐檔分類。base commit 無法取得時才退回 `no-base`。

schema v2 state 仍放在 `npx-first-party.yaml`；overlay bytes 與 tombstones 放在 `~/.config/ai-dev/overlays/npx-first-party/`，transaction backups 放在 `~/.config/ai-dev/backups/npx-first-party/`。manifest 與 overlay 目錄使用 user-only permissions，不得提交或記錄內容到 log。

每個 file entry 的 `src_hash` 是本輪接受的 upstream base，`dst_hash_at_sync` 是套用 overlay 後的 expected effective hash；missing 使用固定 sentinel。overlay 存在時，即使 installed hash 等於 `dst_hash_at_sync`，planner 仍將它視為已知 local intent：source 未變是 `local-only`，source 改變是 `both-changed`。

```yaml
schema_version: 2
managed_by: ai-dev-first-party-reconcile
skills:
  example-skill:
    source: ValorVie/ai-dev-skills
    source_commit: <commit>
    files:
      SKILL.md:
        src_hash: sha256:...
        src_commit: <commit>
        src_source: ValorVie/ai-dev-skills
        dst_hash_at_sync: sha256:...
        decision: keep-local
        decided_at: <timestamp>
        overlay:
          kind: file
          hash: sha256:...
          path: example-skill/SKILL.md
```

## Risks / Trade-offs

- [Risk] 新 repository 不會保留方便查找的 per-file history。→ 記錄來源 framework commit，需要追查時使用既有 repository。
- [Risk] 第一方 skill 依賴目錄外檔案。→ 發布前檢查 escaping links 與 runtime inputs；把必要檔案移入 skill，或改成公開 integration reference。
- [Risk] npx 改變 agent IDs 或 global paths。→ 記錄驗證使用的 `skills --version`，用 list/path probes 驗證 mapping；無法證明時停止。
- [Risk] `--yes` 覆蓋使用者修改過的 target。→ add 前比較舊 manifest base 與現場內容；保留或備份修改內容，並要求明確決定。
- [Risk] npx update 不比較本機內容，且 partial agent failure 仍可能回傳 0。→ 第一方不使用原生 update；guard 先分類 local drift，add 後再驗證所有 configured paths。
- [Risk] 直接執行原生 npx 會清掉 installed overlay。→ overlay bytes 是獨立持久 truth；下一次 ai-dev reconcile 重新套用，source 同時改變時進入 `both-changed`。
- [Risk] npx whole-directory replace 使單一檔案決策難以套用。→ mutation 前保存 overlay 與完整 transaction backup；npx 寫 base 後再 materialize overlay。
- [Risk] crash 留下 base、overlay、manifest 不一致。→ transaction journal 與完整 backup 在下一次執行前恢復或阻擋。
- [Risk] 舊 target 各自有不同修改。→ 不猜測合併；阻擋並要求 canonical selection，不支援 per-agent overlay。
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
2. 加強 manifest validation，依 package 分組；第三方維持 add/update，第一方交給 reconcile。
3. 加入 per-file schema v2、persistent overlay store、decision resolver、transaction journal、migration preflight、canonical legacy mapping 與全 target post-install readback。
4. 從 Stage 3 source configuration 與 clone ownership 移除第一方 skills。
5. 更新 list、toggle、resource-disable 與 standards boundaries。

npx phase 保持在 targets phase 之前，讓 fresh install 先取得第一方 skills，再分發保留的資源。

### Phase 4：遷移既有安裝

1. 讀取舊 target manifests、v1 guard、active roots 與 overlays，比較每個第一方 target 與 stored base。
2. 取得 current source 與舊 base commit，將 v1 guard／legacy manifests 轉成 per-file plan；base 不可得的 files 才標成 no-base。
3. local-only 自動 capture overlay；both-changed／no-base 在 mutation 前完成 decision，未解決時保留並跳過該 skill。
4. 合併相同的舊 target copies；不同 target modifications 停止並要求 canonical selection。
5. 完成 local overlay capture 與所有 conflict decisions，再安裝明確的 npx inventory。
6. 驗證 pure base，套用 overlay／tombstones，再驗證 materialized view。
7. 原子寫入 schema v2 manifest 與 active overlays，再移除舊 manifest entries 與未修改的 legacy paths，包含 mapped `custom-simplify` path。
8. 重跑 clone 與 raw-npx recovery probe，確認 clone 不會取得 ownership，overlay 可重新套用。

detach 後的 rollback：需要時還原 preserved content，回復上一個 framework release，再執行其 clone flow。rollback 不得移除 user-modified backups。

### Phase 5：移除 framework content 並更新文件

1. remote source 與 migration tests 通過後，從 `custom-skills` 移除已遷移的 `skills/` content 與 content-specific tests。
2. framework integration tests 留在 `custom-skills`；skill content tests 移到 `ai-dev-skills`。
3. 更新 README、architecture/data-flow references、skill inventory、install/update/list/toggle 文件與 CHANGELOG。
4. 驗證 ECC、custom repos 與 project-template skills 仍使用既有路徑。

## Open Questions

無。Antigravity path support 是具有 fail-closed 結果的 implementation preflight，不影響本次 ownership model。

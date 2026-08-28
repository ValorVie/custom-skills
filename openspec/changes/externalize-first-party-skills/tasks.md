## 1. 固定清單與公開邊界

- [x] 1.1 記錄來源 `custom-skills` commit，從每個 `skills/*/SKILL.md` frontmatter 產生第一方清單；驗證 19 個 canonical IDs 皆唯一，且只有 `custom-simplify → simplify` 需要 legacy mapping。
- [x] 1.2 掃描所有第一方 skill 檔案中的內部品牌、repositories、hosts、accounts、project IDs、credential locations 與 private paths；將 `work-log-claude` 的內部預設值和範例改成公開安全的中性內容。
- [x] 1.3 檢查 Markdown links 與 runtime path references；把必要檔案移入各 skill，或將 escaping links 改成公開 URLs，並驗證主要流程不依賴離開 skill root 的相對連結。
- [x] 1.4 檢查 companion plugins、hooks 與 commands；更新相關 skill 文件，說明 npx 不會安裝哪些內容，並指向公開的 native installation entry。
- [x] 1.5 找出 framework 中驗證 skill content 的測試；規劃將其移到新 repository，`custom-skills` 只保留 npx integration fixtures。

## 2. 建立並驗證 ai-dev-skills candidate

- [x] 2.1 外部 checkout path 核准後，以 sanitized snapshot 建立乾淨的 `ValorVie/ai-dev-skills` candidate，不匯入舊 subtree Git history。
- [x] 2.2 建立公開 repository 結構：`skills/<canonical-id>/`、`tests/`、`AGENTS.md`、`README.md`、`LICENSE` 與 `CHANGELOG.md`；`simplify` 目錄名必須與 frontmatter ID 相同。
- [x] 2.3 加入 root validation，檢查 YAML frontmatter、ID 唯一性、目錄與名稱一致、escaping links、必要支援檔及公開邊界受限詞。
- [x] 2.4 停用 telemetry 後執行 `npx skills add <local-candidate> --list`，驗證輸出名稱與明確的第一方清單完全一致。
- [x] 2.5 執行每個已遷移 skill 的直接測試與 validator，再檢查完整 candidate diff，排除內部識別資訊與 generated files。

## 3. 發布公開來源

- [x] 3.1 列出準確的 GitHub repository name、public visibility、初始檔案清單、commands、無費用假設、rollback 與 stop conditions；取得建立 repository 和首次 push 的明確批准。
- [x] 3.2 建立 `ValorVie/ai-dev-skills`，提交 sanitized snapshot；metadata 記錄來源 framework commit，只在批准後 push，並建立 known-good initial revision 或 tag。
- [x] 3.3 驗證 remote repository 為 public，且 `npx skills add ValorVie/ai-dev-skills --list` 回傳核准的 inventory，不含內部識別資訊。

## 4. 加強 declarative npx pipeline

- [x] 4.1 將 `ValorVie/ai-dev-skills` 與 19 個 canonical IDs 加入 `upstream/npx-skills.yaml`；不得使用 wildcard installation。
- [x] 4.2 擴充 npx manifest validation，拒絕缺少 repository、空 skill 清單、重複 canonical ID，以及同一 ID 由多個來源宣告的情況。
- [x] 4.3 重構 add command generation，依 repository 分組 skills，在同一 command 重複傳入 `--skill`；明確保留 global scope、configured agents 與 non-interactive behavior。
- [x] 4.4 更新 update-command handling，使其支援 manifest inventory，並在最終摘要保留每個 package 的失敗結果。
- [x] 4.5 加入 focused tests，涵蓋 grouped commands、validation failures、dry-run no-write、部分失敗回報與缺少第一方 skill。

## 5. 實作 migration preflight 與 ownership 移交

- [x] 5.1 建立 migration inventory，將 canonical IDs 對照到舊 target manifest entries，並加入一次性的 `custom-simplify → simplify` path mapping。
- [x] 5.2 在 npx add 前比較每個舊 target 與 stored manifest base；preview 只分類 unchanged、locally modified、unknown ownership 或 missing，不執行 mutation。
- [x] 5.3 若 target 已修改或 ownership 未知，停止並保留內容；列出衝突檔案與 backup/manual-decision 入口，不使用 force。
- [x] 5.4 npx add 後讀回 canonical IDs、source information 與 agent-visible paths；所有必要驗證通過前，不得 detach 舊 ownership。
- [x] 5.5 只從 ai-dev target manifests 移除已驗證且未修改的第一方 entries，並清理不再使用的 legacy paths；`simplify` 通過後才能移除 `custom-simplify`。
- [x] 5.6 加入 migration tests，涵蓋全新安裝、unchanged legacy copy、modified legacy copy、unknown ownership、missing npx source、部分 add 失敗、完成後重跑及 legacy-name cleanup。

## 6. 移除第一方 clone ownership

- [x] 6.1 從第一方 Stage 3 platform resources 移除 `custom-skills/skills/`，保留 commands、agents、workflows 與 plugins。
- [x] 6.2 從 custom repo 與 ECC prescan/distribution 過濾 npx-managed canonical IDs；若另一個 enabled source 使用同一 ID，必須在寫入前停止。
- [x] 6.3 防止一般 clone orphan cleanup 在 gated migration 前刪除 legacy first-party entries。
- [x] 6.4 更新 ManifestTracker 與 clone tests，證明新 manifests 不含第一方 npx skills，而 ECC 與 custom repo skills 仍被追蹤。
- [x] 6.5 執行 clone dry-run 與 isolated target tests，驗證保留資源的順序，並確認 clone 無法重新取得第一方 ownership。

## 7. 更新 list、toggle 與 standards 邊界

- [x] 7.1 更新 skill source identification，讀取 declarative npx manifest，將第一方 entries 顯示為 `ai-dev-skills`，並包含 legacy-name migration view。
- [x] 7.2 npx manifest 缺少或無效時，list 仍維持 read-only；無法證明來源的項目標示為 `unknown`，不得 mutation 或猜測。
- [x] 7.3 `toggle` 與 resource-disable 必須在 filesystem mutation 前拒絕 npx-managed canonical IDs，回傳 exit code 1；只有 target mapping 已驗證時，才顯示可複製的原生 npx command。
- [x] 7.4 以 focused tests 固定 `claude → claude-code`、`codex → codex` 與 `agy → gemini-cli` mapping；探測 Antigravity 實際讀取路徑，不符合已安裝 npx CLI 時採 fail closed。
- [x] 7.5 standards dry-run 標記 npx-managed entries；實際 profile switch 若要改動 npx-managed skill，必須在 mutation 前停止。
- [x] 7.6 加入 regression tests，證明非 npx-managed resources 保留既有 toggle、disabled-directory 與 profile behavior。

## 8. 移除 framework skill content 並更新文件

- [x] 8.1 remote 與 migration validation 通過後，從 `custom-skills` 移除已遷移的 `skills/` directories 與 content-specific tests；project-template repo-local skills 維持不變。
- [x] 8.2 更新 README、skill inventory、install/update/list/toggle references、`docs/dev-guide/workflow/ai-dev-framework-architecture.md`、copy architecture 與 command/data-flow 文件。
- [x] 8.3 更新 `custom-skills-dev`、`custom-skills-doc-updater`、ECC analysis 與 notification references，使新安裝位置和 companion integration boundaries 正確。
- [x] 8.4 在 CHANGELOG 記錄 breaking ownership changes、首次安裝、local-conflict stops、`custom-simplify → simplify`、rollback 與未變更的 ECC boundary。
- [x] 8.5 從目前 checkout 執行 project-template maintenance，驗證 managed prompt blocks 與 repo-local project skills 沒有無關 drift。

## 9. 最終驗證與交接

- [x] 9.1 執行 focused npx、manifest、clone、list、toggle、resource-disable、standards 與 migration tests，再執行完整 repository test suite、Ruff、Black check 及 `git diff --check`。
- [x] 9.2 執行 `openspec validate externalize-first-party-skills --strict`，確認每個 delta requirement 都有有效的 `#### Scenario`。
- [x] 9.3 使用已批准的本機 ASD-STE100 checker 檢查最終 OpenSpec Markdown artifacts；逐項判斷適用的 findings，不宣稱認證或完整符合。
- [x] 9.4 對所有 changed public files 與 staged diffs 執行不分大小寫掃描，檢查內部 identifiers、private paths、hosts、accounts、credentials 與 organization-specific examples。
- [x] 9.5 分別提交兩個 repositories 的 scoped changes，回報兩個 commit hashes 與驗證結果；未批准的 remote changes 不得 push。
- [x] 9.6 分開確認最終狀態：public source 已發布、npx install 已驗證、framework ownership 已 detach、舊未修改副本已清理、local conflicts 已保留、ECC 未變更，且未進行 production、service 或 credential mutation。

## 10. 限縮 global agent targets

- [x] 10.1 將 `defaults.agents` 擴充為向後相容的字串或清單輸入，add command 以多個 agent arguments 展開。
- [x] 10.2 將 repository baseline 改為 `claude-code`、`codex`、`gemini-cli`、`opencode`、`antigravity`，並加入不包含 Eve／PromptScript 的回歸測試。
- [x] 10.3 更新現行文件與 CHANGELOG，執行 focused／完整測試、OpenSpec strict validation、public-boundary scan 與 diff check，完成後另行提交且不推送。

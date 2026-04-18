# npx skills 遷移與 ai-dev 整合計畫

**日期**：2026-04-18
**狀態**：進行中
**依據報告**：[2026-04-18-npx-skills-coverage-audit.md](../report/2026-04-18-npx-skills-coverage-audit.md)

## 目標

1. 將 12 個有官方/權威 npx 版本的 skill 改用 `npx skills` 維護
2. 將 24 個 UDS 上游鏡像 skill 移到 `skills/uds/` 子目錄以區分來源
3. 在 ai-dev CLI 加入 `npx skills` 安裝能力，由 YAML 檔驅動
4. 保留所有本地客製與無替代版本的 skill

---

## 遷移清單

### ➡️ 改用 npx skills（共 12 個）

**A 組 — anthropics/skills 官方**：
- `claude-api`
- `skill-creator`

**A 組 — kepano/obsidian-skills 官方**：
- `defuddle`
- `obsidian-markdown`
- `obsidian-cli`
- `obsidian-bases`
- `json-canvas`

**B 組 — affaan-m/everything-claude-code（本地無實質客製，僅差 `origin: ECC` 欄位）**：
- `codebase-onboarding`
- `context-budget`
- `mcp-server-patterns`（本地缺一段 docs 連結但無關鍵功能差異）
- `safety-guard`
- `security-scan`

### 🗂 移到 `skills/uds/` 子目錄（24 個）

```
ai-collaboration-standards        ai-friendly-architecture
ai-instruction-standards          atdd-assistant
bdd-assistant                     changelog-guide
checkin-assistant                 code-review-assistant
commit-standards                  docs-generator
documentation-guide               error-code-guide
forward-derivation                git-workflow-guide
logging-guide                     methodology-system
project-structure-guide           refactoring-assistant
release-standards                 requirement-assistant
reverse-engineer                  spec-driven-dev
test-coverage-assistant           testing-guide
```

### 🔒 維持原樣（17 個）

- `custom-*` 12 個（本專案客製）
- `auto-skill`、`cloud-infrastructure-security`、`discuss-multi-ai`、`wiki`、`work-log-claude`

---

## ai-dev 行為異動

### 舊邏輯

| Phase | 來源 | 去向 |
|-------|------|------|
| `tools` | `npx skills update`（已有，但無安裝邏輯） | npm global |
| `repos` | 硬編碼 `REPOS` dict | `~/.config/*/` |
| `state` | auto-skill canonical | `~/.config/ai-dev/skills/auto-skill/` |
| `targets` | `~/.config/custom-skills/skills/` | `~/.claude/skills/` 等 |

**缺口**：`skills-lock.json` 只由 npx skills 自行管理，ai-dev 不讀、不觸發安裝。

### 新邏輯

新增 `upstream/npx-skills.yaml` 作為 ai-dev 驅動的 npx 安裝清單：

```yaml
# 由 ai-dev 觸發的 npx skills 安裝列表
# 執行：ai-dev install-npx-skills  或  ai-dev update --only npx-skills
version: 1

skills:
  - package: anthropics/skills
    source: anthropic-official
    skills:
      - claude-api
      - skill-creator

  - package: kepano/obsidian-skills
    source: kepano-obsidian
    skills:
      - defuddle
      - json-canvas
      - obsidian-bases
      - obsidian-cli
      - obsidian-markdown

  - package: affaan-m/everything-claude-code
    source: everything-claude-code
    skills:
      - codebase-onboarding
      - context-budget
      - mcp-server-patterns
      - safety-guard
      - security-scan
```

**新增 phase：`npx-skills`**
- 讀取 `upstream/npx-skills.yaml`
- 對每個 skill 執行 `npx skills add -g <package>@<skill> --yes`
- 加入 command_manifest.py 的 phase 定義
- 整合到 `update` 預設流程（`tools, repos, state, npx-skills`）

**新增 CLI 入口**：
- `ai-dev install-npx-skills`：等同 `ai-dev update --only npx-skills`

### COPY_TARGETS / get_source_skills 調整

- `get_source_skills()` 需支援巢狀目錄（偵測 `skills/uds/<name>`）
- `copy_custom_skills_to_targets()` 對 UDS 子目錄扁平化展開，目標端仍為 `~/.claude/skills/<name>/`（不帶 uds/ 前綴，以維持工具相容性）

---

## 執行步驟

### Phase 1：文件與設定（本計畫）
- [x] 盤點報告
- [x] 本計畫
- [ ] 建立 `upstream/npx-skills.yaml`

### Phase 2：ai-dev 程式修改
- [ ] `script/cli/command_manifest.py`：新增 `npx-skills` phase
- [ ] `script/services/npx_skills/install.py`：新模組，讀 YAML + 執行 npx
- [ ] `script/services/pipeline/update_pipeline.py`：註冊新 phase
- [ ] `script/main.py`：新增 `install-npx-skills` 命令（或納入 update）
- [ ] `script/utils/shared.py:get_source_skills()`：支援巢狀掃描
- [ ] `script/services/targets/distribute.py`：UDS 子目錄扁平化複製

### Phase 3：UDS 子目錄遷移
- [ ] `mkdir skills/uds/`
- [ ] `git mv skills/<uds-skill> skills/uds/<uds-skill>`（24 個）
- [ ] 同步更新 `~/.config/custom-skills/skills/`（若有）

### Phase 4：npx 安裝 + 本地移除
- [ ] `ai-dev install-npx-skills` 或手動 `npx skills add -g ...`
- [ ] 驗證 `~/.claude/skills/` 出現 npx 版
- [ ] `git rm -r skills/<12 個遷移 skill>`

### Phase 5：驗證與文件
- [ ] `ai-dev clone --dry-run` 確認不會誤刪或重複複製
- [ ] 更新 `docs/ai-dev指令與資料流參考.md`
- [ ] 更新 `docs/report/2026-04-18-npx-skills-coverage-audit.md` 標記完成
- [ ] CHANGELOG 記錄

### Phase 6：Commits
- [ ] commit 1：新增 `npx-skills.yaml` + 本計畫
- [ ] commit 2：ai-dev 程式支援 npx-skills phase
- [ ] commit 3：UDS 子目錄遷移
- [ ] commit 4：移除改用 npx 的 12 個本地 skill
- [ ] commit 5：文件更新

---

## 風險與回滾

| 風險 | 緩解 |
|------|------|
| `npx skills add -g` 與 `ai-dev clone` 覆蓋衝突 | 先 dry-run；若衝突，改安裝到 `skills-lock.json` project-level，由 ai-dev 統一分發 |
| UDS 子目錄破壞工具發現（Claude Code 期望 flat） | `copy_custom_skills_to_targets()` 扁平化；本地 `skills/uds/` 僅作為組織用 |
| 移除本地版後某工具找不到 skill | 先確認 `~/.claude/skills/<name>/` 存在再 `git rm` |
| SKILL.md 有本地客製被誤刪 | B 組已確認僅差 `origin: ECC`，無客製；A 組官方版為主 |

## 相容性承諾

- 既有 `ai-dev clone`、`ai-dev update` 命令行為不變
- `update --only npx-skills` 為新選項；`update` 預設包含它（可用 `--skip npx-skills` 跳過）
- `skills-lock.json` 繼續由 npx skills 管理，ai-dev 不直接修改

# npx skills 整合與 UDS 子目錄化設計

**日期**：2026-04-18
**狀態**：待使用者審核
**取代**：`2026-04-18-npx-skills-migration-plan.md`（該文件為初版草稿，以本設計為準）

---

## 設計目標

1. 讓 ai-dev 以 YAML 驅動的方式自動安裝／更新 `npx skills` 官方 skill
2. 把 24 個 UDS 鏡像 skill 從 `skills/` 根目錄移到 `skills/uds/` 子目錄以明確來源
3. 移除 12 個改由 npx 維護的本地鏡像，避免新舊版併存
4. 保證 Claude + Codex（含 Gemini、Antigravity、Copilot）皆自動安裝

---

## 已確定設計決策

| # | 項目 | 決策 |
|---|------|------|
| Q1 | YAML 真實來源 | 專案 `upstream/npx-skills.yaml` 是權威，`ai-dev update` 覆蓋到 `~/.config/ai-dev/npx-skills.yaml`。個人 skill 走 `npx skills` 手動安裝，不受 ai-dev 管 |
| Q2 | install vs update 語意 | `install` = `npx skills add`（idempotent，補齊缺的）；`update` = `npx skills update`（刷新已裝） |
| Q3 | agents 範圍 | 一律 `-a '*'`（all agents）。YAML 的 `defaults.agents: "*"` 即產生此參數 |
| Q4 | UDS 子目錄 | `skills/uds/<name>/`，`get_source_skills()` 遞迴掃描，target 分發時扁平化 |
| Q5 | pipeline phase 位置 | 新 phase 名 `npx-skills`，接在 `state` 後、`targets` 前。install/update 預設啟用，保留 `--skip npx-skills` 逃生閥 |
| Q6 | 本地 12 skill 處理 | 同一次變更 `git rm`，不保留 `_deprecated/` 過渡區 |

---

## 架構

### 1. 設定檔結構

**專案層（權威來源）** — `upstream/npx-skills.yaml`
```yaml
version: 1

defaults:
  agents: "*"           # 一律所有 agent（產生 -a '*'）
  scope: global         # -g（user-level 安裝）
  yes: true             # --yes（跳過互動）

packages:
  - repo: anthropics/skills
    source: anthropic-official
    rationale: Anthropic 官方維護
    skills: [claude-api, skill-creator]

  - repo: kepano/obsidian-skills
    source: kepano-obsidian
    rationale: Obsidian 官方作者維護
    skills: [defuddle, json-canvas, obsidian-bases, obsidian-cli, obsidian-markdown]

  - repo: affaan-m/everything-claude-code
    source: everything-claude-code
    rationale: 本地比對後無實質客製
    skills: [codebase-onboarding, context-budget, mcp-server-patterns, safety-guard, security-scan]
```

**User 層（由 ai-dev 自動同步）** — `~/.config/ai-dev/npx-skills.yaml`

- 由 `ai-dev update` 的 `repos` phase 從專案複製過來（與其他 state 同步機制一致）
- 使用者**不應手動改**這份（改了下次 update 會被覆蓋）
- 使用者想裝個人 skill：直接 `npx skills add <pkg>@<skill> -g -a '*' --yes`，不透過 ai-dev

### 2. ai-dev pipeline 變動

**新 phase：`npx-skills`**

```
install pipeline:
  tools → repos → state → npx-skills → targets
                            ↑ 新
update pipeline:
  tools → repos → state → npx-skills
                            ↑ 新
```

**phase 行為**：

| 命令 | npx-skills phase 動作 |
|------|---------------------|
| `ai-dev install` | 對每個 yaml 中的 `<repo>@<skill>` 執行 `npx skills add <repo>@<skill> -g -a '*' --yes`（idempotent：已裝則 skip） |
| `ai-dev update` | 對每個 yaml 中的 `<skill>` 執行 `npx skills update <skill> -y`（只更新已裝的） |
| `ai-dev update --skip npx-skills` | 跳過此 phase |
| `ai-dev install-npx-skills`（新命令） | 等同 `ai-dev install --only npx-skills` 的捷徑 |

**為何 install 使用 add 而非 update**：
- 新工作站首次 `ai-dev install` 時，npx skill 尚未安裝；`update` 找不到已裝 skill 會失敗
- `add` 天然 idempotent：若已裝同名同版本，npx skills 會 no-op 或只做輕量重新連結

### 3. UDS 子目錄結構

```
skills/
├── uds/                              # 24 個 UDS 鏡像（新）
│   ├── ai-collaboration-standards/
│   ├── ai-friendly-architecture/
│   └── ...（共 24 個）
├── auto-skill/                       # 其他 skill 原位
├── custom-simplify/
├── custom-skills-*/                  # 本專案客製
├── cloud-infrastructure-security/
├── discuss-multi-ai/
├── wiki/
└── work-log-claude/
```

**掃描與分發**：

```python
def get_source_skills(root: Path) -> list[SkillEntry]:
    """遞迴掃描子目錄，任何含 SKILL.md 的目錄都算 skill。"""
    for skill_md in root.rglob("SKILL.md"):
        yield SkillEntry(
            source_dir=skill_md.parent,
            name=skill_md.parent.name,          # 扁平化：目錄名即 skill 名
            # subdir 資訊僅供 log／report，不影響分發路徑
        )

def copy_to_target(entry: SkillEntry, target_root: Path):
    dest = target_root / entry.name           # 永遠扁平：~/.claude/skills/<name>/
    shutil.copytree(entry.source_dir, dest, dirs_exist_ok=True)
```

**關鍵不變式**：target 端永遠是扁平 `<target>/skills/<name>/`，不出現 `uds/` 前綴。

### 4. 模組與檔案新增／變動

| 檔案 | 動作 | 內容 |
|------|------|------|
| `upstream/npx-skills.yaml` | **已建立** | 專案權威 yaml（已存在，需驗證欄位對齊本設計） |
| `script/services/npx_skills/install.py` | **新增** | 解析 yaml、執行 `npx skills add`／`update` |
| `script/services/npx_skills/__init__.py` | **新增** | 匯出 `run_npx_skills_phase` |
| `script/cli/command_manifest.py` | **修改** | `PIPELINE_PHASES` 加 `"npx-skills"`；install/update 的 `default_phases` / `allowed_phases` 納入 |
| `script/services/pipeline/install_pipeline.py` | **修改**（若存在；否則在 `clone_pipeline.py` 或對應檔） | 加 `elif phase == "npx-skills": run_npx_skills_phase(plan, mode="add")` |
| `script/services/pipeline/update_pipeline.py` | **修改** | 加 `elif phase == "npx-skills": run_npx_skills_phase(plan, mode="update")` |
| `script/main.py` | **修改** | 新增 `install-npx-skills` 命令（薄 wrapper） |
| `script/utils/shared.py` | **修改** | `get_source_skills()` 改用 `rglob("SKILL.md")`；`copy_custom_skills_to_targets()` 用 `entry.name` 扁平化 |
| `script/services/repos/refresh.py` | **修改** | 加一步：把 `upstream/npx-skills.yaml` 複製到 `~/.config/ai-dev/npx-skills.yaml` |
| `skills/uds/` | **新增目錄** | 24 個 UDS skill 用 `git mv` 搬入 |
| `skills/<12 個>` | **刪除** | `git rm -r` |

### 5. 資料流：`ai-dev install` 完整流程

```
$ ai-dev install
├─ tools       : npm/bun/uds/npx-skills CLI 本身升級
├─ repos       : git fetch/reset 所有 upstream repo
│                 並複製 upstream/npx-skills.yaml → ~/.config/ai-dev/npx-skills.yaml
├─ state       : refresh auto-skill canonical
├─ npx-skills  : 讀 ~/.config/ai-dev/npx-skills.yaml
│                 for each package.repo:
│                   for each skill:
│                     npx skills add <repo>@<skill> -g -a '*' --yes
└─ targets     : 複製 ~/.config/custom-skills/skills/**/SKILL.md 到各 agent
                 （遞迴掃描，包含 skills/uds/）
```

### 6. 驗證與回滾

**驗證步驟**：
1. `ai-dev install --dry-run` 顯示 phase 清單含 `npx-skills`
2. `ai-dev install-npx-skills` 後：
   - `ls ~/.claude/skills/claude-api/` 存在且為 anthropic 版
   - `ls ~/.codex/skills/claude-api/`、`~/.config/gemini/skills/claude-api/` 同樣存在
3. `ai-dev clone --dry-run` 確認不會把已刪除的本地 12 skill 目錄複製
4. UDS 子目錄：`get_source_skills()` 回傳 24 個 UDS skill 的 `name` 為純 skill 名（無 `uds/` 前綴）

**回滾**：
- yaml 有問題：`ai-dev update --skip npx-skills` 臨時跳過
- 本地 12 skill 誤刪：`git revert` 還原該 commit
- UDS 子目錄不相容：`git mv skills/uds/* skills/` 還原平坦結構

---

## 相容性承諾

- `ai-dev install`、`ai-dev update`、`ai-dev clone` CLI 介面**不變**
- `--only`、`--skip`、`--target` 新增支援 `npx-skills` phase 名稱
- 既有 phases（`tools/repos/state/targets`）行為不變
- `skills-lock.json` 由 npx skills 自行管理，ai-dev 不讀寫

---

## 遷移設計（舊使用者升級路徑）

**策略**：半自動（install/update 偵測殘留舊鏡像並自動覆蓋），最小化使用者手動步驟。

### 風險對照與遷移處理

| # | 風險 | 對策 | 實作位置 |
|---|------|------|---------|
| M1 | 升級後 `~/<target>/skills/<name>/` 殘留舊本地鏡像版，但使用者未跑 `install-npx-skills` | `npx-skills` phase 對每個 yaml skill 執行時，無論 target 端是否已有，都跑 `npx skills add`（idempotent，新版覆蓋舊版） | `script/services/npx_skills/install.py` |
| M2 | `skills/uds/` 子目錄化後，舊版 ai-dev 的 `get_source_skills()` 是平坦掃描，找不到 UDS skill | 先升級 ai-dev 本體（M4 處理），再 pull 新 repo。額外保險：`skills/uds/` 與 `skills/` 根目錄**同時**共存一個版本期（git mv 後保留），由 `get_source_skills()` 去重；下個版本再清根目錄 — **否決**（增加複雜度）。採 M4 解法即可 | — |
| M3 | `~/.config/ai-dev/npx-skills.yaml` 首次不存在 | `npx-skills` phase 入口 `ensure_user_yaml()`：若 user 檔不存在則從 `~/.config/custom-skills/upstream/npx-skills.yaml` 複製（`repos` phase 已拉過） | `install.py` 入口 |
| M4 | `tools` phase 升級 ai-dev 本體後，當次執行仍用舊 Python 模組 | `tools` phase 偵測 ai-dev 套件版本是否改變；若變動，顯示「ai-dev 本體已升級，請重新執行」並 `sys.exit(0)`（正常退出，不跑後續 phase） | `script/services/tools/update.py` |
| M5 | 本地 `skills/<name>/` 被 `git rm` 後，target 端舊檔殘留 | 不自動清 target 端（避免誤刪）。由 M1 的 `npx skills add` 覆蓋相同名稱檔案，實際效果等同更新 | — |

### 遷移流程（使用者視角）

**情境：舊使用者（ai-dev 舊版，本地 `skills/claude-api/` 存在）升級到本次變更後**

```
1. git pull（或 ai-dev update --only repos 拉最新 custom-skills）
   → ~/.config/custom-skills/ 已含新 upstream/npx-skills.yaml
   → skills/ 結構已變（uds/ 子目錄 + 刪除 12 skill）

2. ai-dev update
   ├─ tools: 偵測 ai-dev 本體若升級 → 提示「請重新執行 ai-dev update」退出
   │          (若沒升級則繼續)
   ├─ repos: git reset upstream repos
   ├─ state: auto-skill
   ├─ npx-skills: ensure_user_yaml() → 首次建立 ~/.config/ai-dev/npx-skills.yaml
   │              對每個 yaml skill 執行 `npx skills update <name> -y`
   │              （首次此步會 no-op 或 warn，因為 skills 尚未安裝）
   │              → 提示「尚未安裝，請執行 ai-dev install-npx-skills」
   └─（update 無 targets phase）

3. ai-dev install-npx-skills
   └─ 對每個 yaml skill 執行 `npx skills add <repo>@<name> -g -a '*' --yes`
      → 覆蓋舊本地鏡像版，target 端變成 npx 版

4. ai-dev clone
   └─ 從 ~/.config/custom-skills/skills/**/SKILL.md 分發
      （skills/uds/*／skills/其他 都能被遞迴掃描）
```

### 遷移提示訊息設計

`npx-skills` phase 執行時需輸出明確訊息：

```
[npx-skills] 讀取 ~/.config/ai-dev/npx-skills.yaml (12 個 skill, 3 個 package)

[1/12] anthropics/skills@claude-api
  ✓ 已安裝（版本 X.Y.Z），跳過

[2/12] anthropics/skills@skill-creator
  偵測到本地舊鏡像殘留於 ~/.claude/skills/skill-creator/，將以 npx 版覆蓋
  執行 npx skills add anthropics/skills@skill-creator -g -a '*' --yes
  ✓ 已安裝至 claude, codex, gemini, antigravity, copilot

...

總結：12 skill 中 8 個已安裝跳過、4 個新裝/覆蓋。
```

### 首次遷移完成偵測

為判斷「遷移已完成」，加入一次性偵測：

- 若 `~/.config/ai-dev/.npx-migration-v1-done` 存在 → 視為已遷移，不再顯示「偵測到舊鏡像」警告
- 首次 `install-npx-skills` 成功結束後寫入此 marker
- 使用者想重跑強制遷移：`rm ~/.config/ai-dev/.npx-migration-v1-done` 後重跑

---

## YAGNI 排除

**不做**的事：
- 雙層 yaml 合併（user 疊加 project）— 選項 C，已否決
- 本地 `_deprecated/` 過渡區 — 直接刪
- 自訂 npx registry mirror — 直接用 skills.sh 預設
- `ai-dev install-npx-skills` 以外的專屬子命令（例如 `list-npx-skills`、`remove-npx-skill`）— 由使用者直接用 `npx skills list`／`remove`

---

## 遷移執行順序（供後續 plan 使用）

1. 本設計核准
2. 產生 implementation plan（用 writing-plans skill）
3. 依 plan 執行：
   - Commit 1：修改 `upstream/npx-skills.yaml` 格式對齊本設計
   - Commit 2：新增 `script/services/npx_skills/`、修改 command_manifest 與 pipelines
   - Commit 3：修改 `shared.py` 的 `get_source_skills()` 支援遞迴
   - Commit 4：`git mv` 24 個 UDS skill 到 `skills/uds/`
   - Commit 5：`ai-dev install-npx-skills` 安裝 12 個 + `git rm` 本地 12 個
   - Commit 6：更新 `docs/ai-dev指令與資料流參考.md`（MUST 規則）與 CHANGELOG

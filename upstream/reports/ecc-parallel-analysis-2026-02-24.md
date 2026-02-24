# ECC 並行使用可行性分析報告

> **日期：** 2026-02-24
> **目的：** 評估 custom-skills 移除 ECC 整合部分，改由使用者另行安裝 ECC 框架並行使用的可行性
> **結論：** 可行，已建立 OpenSpec change `ecc-selective-distribution`
> **Change 路徑：** `openspec/changes/ecc-selective-distribution/`

---

## 1. ECC 上游現狀

| 指標 | 數據 |
|------|------|
| Repository | [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) |
| Stars | 50,385 |
| 版本 | 1.4.1 |
| 最後更新 | 2026-02-23 |
| Agents | 13 個 |
| Skills | 44 個 |
| Commands | 32 個 |
| 安裝方式 | Plugin Marketplace / npm (`ecc-universal`) / Shell / Manual |
| custom-skills 同步日期 | 2026-02-08（落後 ~2 週） |

---

## 2. custom-skills 從 ECC 整合的部分

| 分類 | 數量 | 具體項目 | 改動程度 |
|------|------|----------|----------|
| Hooks | 全套 | memory-persistence, strategic-compact, code quality | **重度** — Node.js → Python 重寫，新增 PHP/Python 支援 |
| Skills | 6 | continuous-learning, strategic-compact, eval-harness, security-review, tdd-workflow, coding-standards | 中度 |
| Agents | 4 | build-error-resolver, e2e-runner, doc-updater, security-reviewer | 輕度 |
| Commands | 6 | checkpoint, build-fix, e2e, learn, test-coverage, eval | 輕度 |

---

## 3. Hooks 功能完整比對

### 3.1 一覽表

| Event | 功能 | ECC 原版 | custom-skills 魔改版 |
|-------|------|:--------:|:-------------------:|
| **PreToolUse** | 封鎖非 tmux 環境跑 dev server | ✅ | ✅ |
| | 提醒長時間指令用 tmux | ✅ | ✅ |
| | git push 前提醒 | ✅ | ✅ |
| | 封鎖隨意建立 .md 檔 | ✅ | ❌ |
| | 建議手動 compaction | ✅ | ✅ |
| **PostToolUse** | 記錄 PR URL | ✅ | ✅ |
| | 非同步 build 分析 | ✅ | ❌ |
| | JS/TS Prettier 格式化 | ✅ | ✅ |
| | TypeScript 型別檢查 | ✅ | ✅ |
| | console.log 警告 | ✅ | ✅ |
| | PHP Pint/CS-Fixer 格式化 | ❌ | ✅ |
| | PHPStan 靜態分析 | ❌ | ✅ |
| | PHP debug 程式碼警告 | ❌ | ✅ |
| | Python Ruff/Black 格式化 | ❌ | ✅ |
| | mypy 型別檢查 | ❌ | ✅ |
| | Python debug 程式碼警告 | ❌ | ✅ |
| **SessionStart** | 載入前次 session context | ✅ | ✅ (+10KB 截斷 + 中文標記) |
| **SessionEnd** | 持久化 session 狀態 | ✅ (解析 transcript) | ✅ (查 git 狀態) |
| | 評估 session 可提取模式 | ✅ | ✅ |
| **PreCompact** | 壓縮前儲存狀態 | ✅ (簡單 timestamp) | ✅ (含 git diff stats) |
| **Stop** | 檢查 debug 程式碼 | ✅ (僅 JS/TS) | ✅ (JS/TS + PHP + Python) |

### 3.2 架構差異

| 面向 | ECC 原版 | custom-skills 魔改版 |
|------|----------|---------------------|
| Runtime | 純 Node.js | Python + Node.js 混合 |
| Matcher 機制 | 簡單字串 (`"Edit"`)，腳本內部過濾 | CEL 表達式 (`tool == "Edit" && file_path matches ...`)，框架層過濾 |
| SessionEnd 資料來源 | 解析 Claude transcript（使用者問題、工具使用） | 查 git 狀態（repo 實際變更） |
| 在地化 | 英文 | 繁體中文 |
| 程式碼組織 | 扁平 `scripts/hooks/` | 依功能分類 `code-quality/`, `memory-persistence/`, `strategic-compact/` |

### 3.3 缺少的兩個 Hook 詳細分析

#### Hook 1: 封鎖隨意建立 .md 檔（PreToolUse Write）

**價值：中高**

- 攔截 `Write` 工具建立 `.md` / `.txt` 檔案
- 允許例外：`README.md`、`CLAUDE.md`、`AGENTS.md`、`CONTRIBUTING.md`、`.claude/plans/` 路徑下
- 使用 `process.exit(2)` 完全阻擋工具呼叫
- **解決問題：** Claude 傾向自發建立 `ARCHITECTURE.md`、`DESIGN.md`、`NOTES.md` 等文件

**與 custom-skills 的衝突：**

此 hook 會封鎖 auto-skill 知識庫寫入（`skills/auto-skill/**/*.md`）。若要採用，須新增例外：
- `/skills\//` — 技能檔案
- `/\.standards\//` — 標準檔案
- `/openspec\//` — OpenSpec 變更
- `/docs\//` — 文件目錄

#### Hook 2: 非同步 build 分析（PostToolUse Bash, async）

**價值：低（純範例）**

- 偵測 `npm run build`、`pnpm build`、`yarn build`
- **僅印出一行 log，無實際分析邏輯**
- ECC 自己標記為 "Example: async hook"
- 缺少 `bun build`、`cargo build`、`make`、`tsc`、`vite build` 等偵測
- 不值得採用

---

## 4. 名稱衝突盤點

### 4.1 完全衝突（同名）

| 類別 | 衝突項目 | 處理建議 |
|------|----------|----------|
| Skills | `coding-standards` | 移除 custom-skills 版本，使用 ECC 版 |
| Skills | `continuous-learning` | 移除 custom-skills 版本，使用 ECC 版 |
| Skills | `eval-harness` | 移除 custom-skills 版本，使用 ECC 版 |
| Commands | `tdd` | 重命名或移除 custom-skills 版本 |

### 4.2 近似衝突（功能重疊但名稱不同）

| custom-skills | ECC | 說明 |
|---------------|-----|------|
| `code-review-assistant` (skill) | `code-review` (command) + `code-reviewer` (agent) | 功能重疊但名稱不同，可共存 |
| `security-review` (skill) | `security-reviewer` (agent) | skill vs agent，可共存 |
| `strategic-compact` (skill) | `strategic-compact` (skill) | 完全同名，需移除一方 |

### 4.3 Agents 衝突

**無完全衝突。** custom-skills 的 agents（code-architect, doc-writer, reviewer 等）與 ECC 的 agents 名稱完全不同。

---

## 5. ECC 選擇性安裝分析

### 5.1 安裝方式能力矩陣

| 安裝方式 | Skills | Agents | Commands | Hooks | Rules | 可選擇性? |
|----------|:------:|:------:|:--------:|:-----:|:-----:|:---------:|
| Plugin Marketplace | ✅ | ✅ | ✅ | ✅ (自動載入) | ❌ | ❌ 全有或全無 |
| npm (`ecc-universal`) | ❌ | ❌ | ❌ | ❌ | ✅ | 僅安裝 rules |
| `install.sh` | ❌ | ❌ | ❌ | ❌ | ✅ | 僅安裝 rules |
| Manual Clone | ✅ | ✅ | ✅ | 可控制 | ✅ | ✅ 完全可控 |

### 5.2 關鍵限制

- **Plugin Marketplace 無法關閉 hooks** — Claude Code v2.1+ 自動從 `hooks/hooks.json` 載入，無 per-component 開關
- **`claude plugin disable`** 只能停用整個 plugin
- **無 `--disable-hooks` 旗標**

### 5.3 推薦方案：Clone + 清空 hooks

```bash
# 一次性設置
git clone https://github.com/affaan-m/everything-claude-code.git ~/.claude/plugins/ecc-no-hooks
echo '{"hooks":{}}' > ~/.claude/plugins/ecc-no-hooks/hooks/hooks.json

# 安裝為本地 plugin
# Claude Code 內: /plugin install from ~/.claude/plugins/ecc-no-hooks
# 或 per-session: claude --plugin-dir ~/.claude/plugins/ecc-no-hooks
```

**優點：**
- 獲得全部 13 agents、44 skills、32 commands
- 空的 hooks.json 阻止自動載入，無警告
- 更新方式：`git pull && echo '{"hooks":{}}' > hooks/hooks.json`

**缺點：**
- 需要手動更新（不像 marketplace 自動更新）
- 每次 `git pull` 後要重新清空 hooks.json

### 5.4 替代方案比較

| 方案 | 說明 | 優點 | 缺點 |
|------|------|------|------|
| **A. Clone + 清空 hooks** (推薦) | Clone repo，清空 hooks.json | 獲得全部 skills/agents/commands，hooks 完全不載入 | 手動更新，pull 後需重新清空 |
| **B. Marketplace + 忍受雙重 hooks** | 直接用 marketplace 安裝 | 自動更新 | hooks 重複執行，SessionStart/End 衝突 |
| **C. Cherry-pick 到 custom-skills** | 只複製需要的檔案 | 完全可控 | 回到目前的手動同步模式 |
| **D. Fork ECC + 移除 hooks** | 維護一個去 hooks 的 fork | 可用 marketplace 安裝 | 需維護 fork，增加負擔 |

---

## 6. 並行架構建議

### 6.1 移除清單（從 custom-skills）

```
plugins/ecc-hooks/           ← 保留（你的魔改版有 PHP/Python 支援）
plugins/ecc-hooks-old/       ← 刪除
plugins/ecc-hooks-opencode/  ← 刪除
sources/ecc/                 ← 刪除（不再需要本地副本）
upstream/ecc/                ← 刪除或標記為 deprecated

skills/coding-standards/     ← 刪除（ECC 衝突）
skills/continuous-learning/  ← 刪除（ECC 衝突）
skills/eval-harness/         ← 刪除（ECC 衝突）

.claude/commands/tdd.md      ← 重命名或刪除（ECC 衝突）
```

### 6.2 保留清單（custom-skills 獨有）

```
skills/ 其他 47 個            ← ECC 沒有
.standards/                   ← ECC 沒有
plugins/auto-skill-hooks/     ← 獨立，不衝突
plugins/ecc-hooks/            ← 你的魔改版（PHP/Python 支援）
.claude/commands/ 其他        ← 不衝突
openspec/                     ← ECC 沒有
```

### 6.3 使用者安裝流程（並行模式）

```bash
# Step 1: 安裝 custom-skills（你的框架）
ai-dev install

# Step 2: 安裝 ECC（無 hooks 版）
git clone https://github.com/affaan-m/everything-claude-code.git ~/.claude/plugins/ecc-no-hooks
echo '{"hooks":{}}' > ~/.claude/plugins/ecc-no-hooks/hooks/hooks.json
# 在 Claude Code 中: /plugin install from ~/.claude/plugins/ecc-no-hooks

# Step 3: 驗證
# - custom-skills 的 hooks 正常運作
# - ECC 的 skills/agents/commands 可用
# - 無名稱衝突警告
```

---

## 7. 結論

| 問題 | 答案 |
|------|------|
| 並行可行嗎？ | **可行**，衝突數量少且可解決 |
| 推薦安裝方式？ | Clone + 清空 hooks.json |
| 需要移除什麼？ | 3 skills + 1 command + sources/ecc/ + 舊 plugin |
| Hooks 怎麼辦？ | 保留 custom-skills 魔改版，ECC hooks 不啟用 |
| 風險？ | 低 — 主要是名稱衝突（已盤點），hooks 重複執行可避免 |
| 維護成本？ | 中 — ECC 需手動 `git pull` 更新，但不需要再做逐檔同步 |

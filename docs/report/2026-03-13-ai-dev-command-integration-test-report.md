---
title: ai-dev 命令整合測試報告
type: report/analysis
date: 2026-03-13
author: ValorVie
status: draft
---

# ai-dev 命令整合測試報告

## 摘要

本次針對 `ai-dev` 目前命令面做了三層驗證：`--help` 命令樹 smoke、command-level pytest 套件，以及隔離 `HOME` 的真人 CLI smoke。結果是 `54/54` 個入口 help smoke 通過、`76/76` 個命令契約測試通過，且大多數可本地驗證的主命令/子命令都能在 sandbox 中得到符合預期的效果。後續補修已完成 `mem` 無設定 guard、`standards` 初始化判定一致化、以及 `coverage --source` 的語意收斂；目前剩下的主要缺口集中在外部依賴與互動式驗證。

## 目前仍阻塞或未完成的測試項目

建議先看這一段，其餘章節再回頭查證據。

| 類別 | 項目 | 狀態 | 原因 | 建議後續動作 |
|------|------|------|------|--------------|
| 外部認證阻塞 | `ai-dev add-custom-repo ValorVie/qdm-ai-base` 完整 live smoke | BLOCKED | GitHub HTTPS clone 在目前 sandbox 需要 non-interactive auth | 在有 GitHub 認證的環境重跑，或為測試提供本地 mirror / fixture repo |
| 外部服務阻塞 | `mem register / push / full pull` 端到端 round-trip | BLOCKED | 需要真實 sync server 與可用 `claude-mem.db` | 準備測試用 sync server 與最小 DB fixture，再補一套 E2E smoke |
| 互動式 UI | `tui` 終端互動流程 | SKIP | 本輪只驗了 help wiring，未做視覺/操作 smoke | 另外建立人工 smoke checklist 或自動化終端互動腳本 |
| live happy path 缺口 | `update-custom-repo` 真正 fetch/update 路徑 | 未完成 | 本輪只驗到 empty-config guard | 以本地假 repo 或 fixture repo 補一條完整更新 smoke |
| live happy path 缺口 | `hooks install` 成功安裝路徑 | 未完成 | 本輪主要驗 guard path，未在 source 完整就緒的 sandbox 做安裝 smoke | 準備完整 source 後補一條 install/status/uninstall smoke |

## 本輪已修正項目

| 項目 | 狀態 | 備註 |
|------|------|------|
| `mem status/pull/auto --dry-run` 無設定時直接 traceback | 已修正 | 改成 CLI guard；`mem auto --dry-run --on/--off` 可用預設 10 分鐘預覽 |
| `standards status/list` 初始化狀態判定不一致 | 已修正 | `project init` 產出的 `.standards/profiles/` scaffold 即視為已初始化 |
| `coverage --source <single-file>` 會產生 warning | 已修正 | 單一 `.py` 檔會自動收斂到父目錄，help/docs 已同步改成「模組名稱或目錄」 |

## 分析目的

- 建立一套可重跑的 `ai-dev` CLI 整合測試指令
- 確認每個主命令、子命令至少有一層可驗證證據
- 區分真正的命令問題、前置條件不足、以及外部依賴阻塞
- 產出後續可持續維護的測試報告

## 分析範圍

### 包含

- top-level 命令：
  `install`、`update`、`clone`、`status`、`list`、`toggle`、`add-repo`、`add-custom-repo`、`update-custom-repo`、`init-from`、`test`、`coverage`、`derive-tests`、`tui`
- 子命令群組：
  `project *`、`standards *`、`hooks *`、`maintain *`、`sync *`、`mem *`
- 命令解析、help wiring、guard path、dry-run 路徑、sandbox 中可驗證的實際副作用

### 排除

- 真正連線到外部 `mem` sync server 的完整端到端同步
- 需要互動式 TUI 操作的視覺驗證
- 依賴 GitHub 認證或上游私有限制的穩定性驗證

## 方法論

### 驗證層次

1. **Command tree help smoke**
   - 對整棵 CLI 樹的 `54` 個入口逐一執行 `--help`
   - 目的：確認 parser、註冊與 help wiring 沒有斷裂
2. **Command-level pytest suite**
   - 執行既有 command tests 與 reference drift test
   - 目的：確認命令契約、guard path 與文件對齊
3. **Live sandbox smoke**
   - 以臨時 `HOME` 建立隔離環境
   - 使用真實 `python -m script.main` 執行 CLI
   - 對可本地驗證的命令做 smoke / guard / dry-run 測試

### 測試環境

| 項目 | 值 |
|------|----|
| 測試分支 worktree | `maintain-command-surface` |
| 測試 commit | `6d72e36` |
| 執行時間 | 2026-03-13 |
| Python 入口 | `.venv/bin/python -m script.main` |
| 隔離策略 | 臨時 `HOME` + 臨時 bare repo + 臨時 project 目錄 |

## 可重跑指令

### 1. 命令樹 help smoke

```bash
python3 - <<'PY'
import subprocess, json
from pathlib import Path

workdir = Path("/Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills/.worktrees/maintain-command-surface")
commands = [
    ["--help"],
    ["install", "--help"],
    ["update", "--help"],
    ["clone", "--help"],
    ["status", "--help"],
    ["list", "--help"],
    ["toggle", "--help"],
    ["add-repo", "--help"],
    ["add-custom-repo", "--help"],
    ["update-custom-repo", "--help"],
    ["init-from", "--help"],
    ["test", "--help"],
    ["coverage", "--help"],
    ["derive-tests", "--help"],
    ["tui", "--help"],
    ["project", "--help"],
    ["project", "init", "--help"],
    ["project", "hydrate", "--help"],
    ["project", "reconcile", "--help"],
    ["project", "doctor", "--help"],
    ["project", "update", "--help"],
    ["project", "exclude", "--help"],
    ["standards", "--help"],
    ["standards", "status", "--help"],
    ["standards", "list", "--help"],
    ["standards", "switch", "--help"],
    ["standards", "show", "--help"],
    ["standards", "overlaps", "--help"],
    ["standards", "sync", "--help"],
    ["hooks", "--help"],
    ["hooks", "install", "--help"],
    ["hooks", "uninstall", "--help"],
    ["hooks", "status", "--help"],
    ["maintain", "--help"],
    ["maintain", "template", "--help"],
    ["maintain", "clone", "--help"],
    ["sync", "--help"],
    ["sync", "init", "--help"],
    ["sync", "push", "--help"],
    ["sync", "pull", "--help"],
    ["sync", "status", "--help"],
    ["sync", "add", "--help"],
    ["sync", "remove", "--help"],
    ["mem", "--help"],
    ["mem", "register", "--help"],
    ["mem", "push", "--help"],
    ["mem", "pull", "--help"],
    ["mem", "status", "--help"],
    ["mem", "cleanup", "--help"],
    ["mem", "reindex", "--help"],
    ["mem", "auto", "--help"],
]

failed = []
for args in commands:
    proc = subprocess.run(
        ["uv", "run", "python", "-m", "script.main", *args],
        cwd=workdir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if proc.returncode != 0:
        failed.append((" ".join(args), proc.stdout))

print(json.dumps({"total": len(commands), "failed": failed}, ensure_ascii=False, indent=2))
PY
```

### 2. Command-level pytest 套件

```bash
uv run pytest \
  tests/test_install_command.py \
  tests/test_update_command.py \
  tests/test_clone_command.py \
  tests/test_status_command.py \
  tests/test_list_command.py \
  tests/test_toggle_command.py \
  tests/test_init_from.py \
  tests/test_project_command.py \
  tests/test_standards_command.py \
  tests/test_hooks_command.py \
  tests/test_maintain_command.py \
  tests/test_sync_command.py \
  tests/test_mem_command.py \
  tests/test_ai_dev_command_reference.py \
  -q
```

### 3. Live sandbox smoke

建議拆成三批：

- 核心命令：`install / update / clone / status / list / toggle / test / coverage`
- project/standards/hooks/sync/maintain/add-repo
- mem guard 與 dry-run

本次實際執行的是臨時 `HOME` sandbox 腳本；若要重跑，可直接依本報告的「分析結果」表格挑選對應命令。

## 分析結果

### 指標總覽

| 指標 | 結果 | 評估 |
|------|------|------|
| Help smoke | `54 / 54` 通過 | 良好 |
| Command-level pytest | `76 / 76` 通過 | 良好 |
| Live sandbox smoke | 多數關鍵命令可驗證 | 良好 |
| 已確認問題 | 4 項 | 需關注 |
| 外部依賴阻塞 | 3 類 | 已記錄 |

### 命令群組結果

| 命令群組 | 自動化契約 | Live smoke | 結論 |
|----------|------------|------------|------|
| `install / update / clone` | PASS | PASS (`--dry-run`) | 符合目前 phase pipeline 語意 |
| `status / list / toggle` | PASS | PASS | 基本命令行為正常 |
| `project *` | PASS | PASS | 主要流程正常，`hydrate/reconcile` 對 managed block 產生衝突提示屬預期 |
| `standards *` | PASS | PASS | 初始化判定已與 scaffold 語意對齊 |
| `hooks *` | PASS | PASS / GUARD PASS | 未安裝或缺少 source 時 guard 清楚 |
| `maintain *` | PASS | PASS | `template --check`、`clone` 均可驗證 |
| `sync *` | PASS | PASS | 本地 bare repo 模式可完整驗證 init/add/push/pull/remove |
| `mem *` | PASS（mock） | PASS | 無設定 guard path 已修正為友善提示 |
| `add-repo` | 無專屬 pytest | PASS (`--skip-clone`) | 可本地驗證 sources.yaml 寫入 |
| `add-custom-repo` | 無專屬 pytest | BLOCKED | 受 GitHub clone 認證/互動限制 |
| `update-custom-repo` | 無專屬 pytest | PASS（empty-config guard） | guard path 正常，完整更新未驗證 |
| `test / coverage / derive-tests` | `coverage` 已補專屬 pytest | PASS | 基本 wrapper 正常，`coverage --source` 單檔案已自動正規化 |
| `tui` | `test_tui_app.py` 未納入本輪 | SKIP | 互動式 UI，需另做終端視覺驗證 |

### 發現 1：`mem` 無設定時的 guard path 仍是 traceback 風格

> 後續修補狀態：已修正。

**結論**: `mem status`、`mem pull`，以及未建立設定檔時的 `mem auto --dry-run`，目前都會直接拋出 `FileNotFoundError`，對使用者來說屬於不夠友善的失敗模式。

**證據**:

| 命令 | 結果 | 評估 |
|------|------|------|
| `ai-dev mem status` | exit `1`，直接顯示 traceback 與 `FileNotFoundError` | 需修正 |
| `ai-dev mem pull` | exit `1`，直接顯示 traceback 與 `FileNotFoundError` | 需修正 |
| `ai-dev mem auto --dry-run --on`（無設定） | exit `1`，直接顯示 traceback | 需修正 |
| `ai-dev mem auto --dry-run --on`（有最小設定） | exit `0`，正確顯示 scheduler preview | 正常 |

**分析**:

這不是命令不可用，而是 guard path 沒有在 CLI 邊界被接住。對比 `sync status` 或 `hooks install` 的前置條件提示，`mem` 目前的 UX 顯著較差。

### 發現 2：`standards` 初始化狀態判定存在不一致

> 後續修補狀態：已修正。

**結論**: `project init` 後，`standards show uds` 與 `standards switch uds` 都能執行，但 `standards status` / `standards list` 仍回報「專案尚未初始化標準體系」。

**證據**:

| 命令 | 結果 | 評估 |
|------|------|------|
| `ai-dev project init <project>` | PASS | 正常建立 `.standards/` scaffold |
| `ai-dev standards show uds` | PASS | 可讀取 profile 與 overlaps |
| `ai-dev standards switch uds --dry-run` | PASS | 可預覽切換 |
| `ai-dev standards switch uds` | exit `0`，顯示「已經在使用 'uds' profile」 | 可執行 |
| `ai-dev standards status` | exit `0`，但顯示「尚未初始化標準體系」 | 不一致 |
| `ai-dev standards list` | exit `0`，但顯示「尚未初始化標準體系」 | 不一致 |

**分析**:

這代表 `standards` 各子命令使用的初始化判定條件並不一致。`show/switch` 可運作，但 `status/list` 視為未初始化，對使用者心智模型有混淆風險。

### 發現 3：`coverage --source` 的文件/用法仍有歧義

> 後續修補狀態：已修正。

**結論**: `ai-dev coverage` 命令本身可正常執行，但 `--source` 若帶「單一檔案路徑」會產生 `CoverageWarning`；改成「模組或目錄」較符合實際行為。

**證據**:

| 命令 | 結果 | 評估 |
|------|------|------|
| `ai-dev coverage tests/test_install_command.py --source script/commands/install.py` | exit `0`，但出現 `module-not-imported` / `no-data-collected` warning | 需澄清 |
| `ai-dev coverage tests/test_install_command.py --source script/commands` | exit `0`，可正常產出 coverage report | 正常 |

**分析**:

CLI help 目前寫的是「原始碼路徑」，但單檔案路徑在實際 pytest-cov 流程中不理想。建議之後把說明收斂成「模組或目錄」。

### 發現 4：`add-custom-repo` 在非互動 sandbox 仍受 GitHub clone 認證限制

**結論**: `add-custom-repo` 的完整 live smoke 無法在本次 sandbox 穩定完成，因為 GitHub HTTPS clone 在此環境下要求互動式認證。

**證據**:

| 命令 | 結果 | 評估 |
|------|------|------|
| `ai-dev add-custom-repo ValorVie/qdm-ai-base` | exit `1`，`fatal: could not read Username for 'https://github.com'` | BLOCKED |

**分析**:

這屬於外部依賴/認證條件阻塞，不等同於命令邏輯錯誤。若要完整驗證，需在具備 GitHub non-interactive auth 的環境重跑。

## 關鍵命令實測摘要

| 命令 | 實測結果 |
|------|----------|
| `ai-dev install --dry-run --only repos,state,targets --target claude` | PASS，顯示 phase plan |
| `ai-dev update --dry-run --only tools,repos,state` | PASS，顯示 phase plan |
| `ai-dev clone --dry-run --only state,targets --target claude` | PASS，顯示 phase plan |
| `ai-dev status --section tools` | PASS，正確輸出工具狀態 |
| `ai-dev list --target claude --type skills` | PASS，正確列出 sandbox skill |
| `ai-dev toggle --target claude --type skills --name demo --disable --dry-run` | PASS，正確輸出 dry-run |
| `ai-dev project init <plain-project>` | PASS，建立 scaffold 與 AI 檔，並在無 `.git` 時顯示正確提示 |
| `ai-dev project doctor <plain-project>` | PASS，回報 `OK` |
| `ai-dev project hydrate <plain-project>` | PASS，回報 managed block 衝突 4 項 |
| `ai-dev project reconcile <plain-project>` | PASS，回報 managed block 衝突 4 項 |
| `ai-dev project exclude --list` | PASS，可列出或回報未設定 |
| `ai-dev standards sync --target claude` | PASS，sandbox 內可正常同步 |
| `ai-dev hooks status --target claude` | PASS，未安裝時顯示明確狀態 |
| `ai-dev hooks install --target claude` | GUARD PASS，缺 source 時明確提示先執行 `install/update` |
| `ai-dev hooks uninstall --target claude` | PASS，未安裝時正常退出 |
| `ai-dev maintain template --check` | PASS |
| `ai-dev maintain clone` | PASS |
| `ai-dev sync status`（未 init） | PASS，顯示初始化指引 |
| `ai-dev sync init --remote <bare-repo> --mode bootstrap` | PASS |
| `ai-dev sync add <dir>` / `push` / `pull --force` / `remove <dir>` | PASS |
| `ai-dev add-repo demo-owner/demo-upstream --skip-clone` | PASS |
| `ai-dev update-custom-repo`（empty config） | PASS，顯示尚未設定任何 repo |
| `ai-dev test tests/test_install_command.py` | PASS |
| `ai-dev coverage tests/test_install_command.py --source script/commands` | PASS |
| `ai-dev derive-tests <spec.md>` | PASS |
| `ai-dev mem cleanup`（無 DB） | PASS，顯示無重複 observations |
| `ai-dev mem reindex`（無 DB） | GUARD PASS，明確指出資料庫不存在 |

## 問題與阻塞

| 問題/阻塞 | 影響 | 狀態 | 備註 |
|-----------|------|------|------|
| `mem status/pull/auto --dry-run` 無設定時直接 traceback | 中 | 已修正 | 已改成 CLI guard message，且 `mem auto --dry-run` 可做預覽 |
| `standards status/list` 初始化狀態判定不一致 | 中 | 已修正 | 已與 `show/switch` 對齊 |
| `coverage --source <single-file>` 會產生 warning | 低 | 已修正 | CLI 會自動改用父目錄，help/doc 已同步 |
| `add-custom-repo` 需要非互動 GitHub auth | 中 | BLOCKED | 非命令內部邏輯錯誤 |
| `mem register/push/full pull` 需 sync server + 真實 DB | 中 | BLOCKED | 本輪只測 guard path |
| `tui` 需互動式終端 UI 驗證 | 低 | SKIP | 建議另做人工 smoke |

## 結論

### 關鍵發現

1. `ai-dev` 目前命令樹的 parser/help wiring 是完整的，`54/54` 入口 smoke 通過。
2. 現有 command-level pytest 套件足以作為穩定的自動化契約基線，`76/76` 通過。
3. 大多數關鍵命令在隔離 sandbox 的實際 CLI 執行中都能得到符合預期的效果。
4. 真正需要優先處理的不是大面積命令失效，而是少數 guard path 與狀態判定不一致。

### 建議

| 優先級 | 建議 | 理由 | 預期效果 |
|--------|------|------|----------|
| 已完成 | 修正 `mem status`、`mem pull`、`mem auto --dry-run` 的無設定 guard path | 原本直接 traceback，CLI 體驗不一致 | 已降低首次使用失敗成本 |
| 已完成 | 對齊 `standards status/list/show/switch` 的初始化判定 | 原本會看到互相矛盾的訊息 | 已收斂 `standards` 子命令語意 |
| 已完成 | 澄清 `coverage --source` 的 help 與文件建議值 | 原本容易誤用單一檔案路徑 | 已降低 warning 與誤判 |
| 待處理 | 為 `add-custom-repo` 建立可在 CI / sandbox 使用的 non-interactive 測試策略 | 目前受 GitHub clone auth 影響 | 補齊 repo 管理命令的 live verification |
| 待處理 | 為 `tui` 補一份人工 smoke checklist | 目前只有 help smoke，沒有互動驗證 | 補齊最後一塊命令面證據 |

## 限制與假設

- 本報告中的 live smoke 以隔離 `HOME` sandbox 執行，不會代表真實使用者環境的所有外部整合行為。
- `add-custom-repo` 的完整驗證受 GitHub non-interactive auth 限制。
- `mem` 系列僅驗證 guard path、dry-run 與本地無 DB 行為，未連線真實 sync server。
- `tui` 本輪僅涵蓋入口 help，不涵蓋互動式操作流程。

## 附錄

- command tree help smoke：`54 / 54` 通過
- command-level pytest：`76 / 76` 通過
- 測試工作樹：`/Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills/.worktrees/maintain-command-surface`
- 測試 commit：`6d72e36`

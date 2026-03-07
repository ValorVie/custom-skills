# Claude Code StatusLine 設定指南

> 自訂 Claude Code 底部狀態列，顯示 Git 分支、模型、Context 用量進度條與時間。

---

## 概覽

StatusLine 是 Claude Code 底部的可自訂列，透過執行 shell 腳本產生內容。腳本從 stdin 接收 JSON session 資料，輸出到 stdout 即顯示在狀態列。

**預設排版效果：**
```
~/ai-home - main* | Claude Sonnet | [████░░░░░░] 42% | 03-07 14:32
```

---

## 檔案結構

```
~/.claude/
├── settings.json              # 啟用 statusLine 的設定
├── statusline-command.sh      # Mac / Linux 腳本
└── statusline-command.ps1     # Windows PowerShell 腳本
```

範本檔案位於本指南同目錄下：

```
statusline-config/
├── statusline-command.sh      # Mac / Linux 範本
└── statusline-command.ps1     # Windows PowerShell 範本
```

---

## settings.json 設定

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline-command.sh"
  }
}
```

> **重要**：`~` 會自動展開為家目錄，跨機器可攜。
> 不要使用硬編碼的絕對路徑（如 `/Users/username/...`）。

### Windows 設定

```json
{
  "statusLine": {
    "type": "command",
    "command": "powershell -NoProfile -File ~/.claude/statusline-command.ps1"
  }
}
```

---

## Mac / Linux 腳本

檔案：`~/.claude/statusline-command.sh`

```bash
#!/usr/bin/env bash
# Claude Code status line
# Format: ~/dir - main* | Claude Sonnet | [████░░░░░░] 42% | 03-07 14:32

input=$(cat)

cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')
model=$(echo "$input" | jq -r '.model.display_name // ""')
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')

grey='\033[38;5;242m'
cyan='\033[38;5;117m'
reset='\033[0m'
sep="${grey} | ${reset}"

# Directory (home → ~)
dir="${cwd/#$HOME/~}"

# Git branch + dirty indicator
git_info="(no git)"
if git_branch=$(git -C "$cwd" symbolic-ref --short HEAD 2>/dev/null \
                || git -C "$cwd" rev-parse --short HEAD 2>/dev/null); then
  dirty=""
  if ! git -C "$cwd" diff --quiet 2>/dev/null \
     || ! git -C "$cwd" diff --cached --quiet 2>/dev/null; then
    dirty="*"
  elif git -C "$cwd" ls-files --others --exclude-standard --error-unmatch . \
       >/dev/null 2>&1; then
    dirty="*"
  fi
  git_info="${git_branch}${dirty}"
fi

# Context progress bar
ctx_bar="[░░░░░░░░░░] --%"
if [ -n "$used_pct" ]; then
  used_int=${used_pct%.*}
  bar_width=10
  filled=$(( used_int * bar_width / 100 ))
  empty=$(( bar_width - filled ))
  bar=""
  for (( i=0; i<filled; i++ )); do bar="${bar}█"; done
  for (( i=0; i<empty;  i++ )); do bar="${bar}░"; done
  ctx_bar="[${bar}] ${used_int}%"
fi

datetime_str=$(date +"%m-%d %H:%M")

printf "${grey}%s - %s${sep}%s${sep}${cyan}%s${reset}${sep}${grey}%s${reset}\n" \
  "$dir" "$git_info" "$model" "$ctx_bar" "$datetime_str"
```

**安裝：**
```bash
chmod +x ~/.claude/statusline-command.sh
```

**相依：** `jq`（`brew install jq` / `apt install jq`）

---

## Windows 腳本

檔案：`~/.claude/statusline-command.ps1`

```powershell
# Claude Code status line - PowerShell (Windows)
$input_json = $input | Out-String | ConvertFrom-Json

$cwd   = $input_json.workspace.current_dir
$model = $input_json.model.display_name
$pct   = if ($null -ne $input_json.context_window.used_percentage) {
             [int]$input_json.context_window.used_percentage
         } else { 0 }

$home_path = $env:USERPROFILE
$dir = if ($cwd -and $cwd.StartsWith($home_path)) {
    "~" + $cwd.Substring($home_path.Length).Replace('\', '/')
} else { $cwd }

$git_info = "(no git)"
try {
    $branch = git -C $cwd symbolic-ref --short HEAD 2>$null
    if (-not $branch) { $branch = git -C $cwd rev-parse --short HEAD 2>$null }
    if ($branch) {
        $dirty = if (git -C $cwd status --porcelain 2>$null) { "*" } else { "" }
        $git_info = "$branch$dirty"
    }
} catch {}

$bar_width = 10
$filled = [math]::Floor($pct * $bar_width / 100)
$bar = ("█" * $filled) + ("░" * ($bar_width - $filled))
$ctx_bar = "[$bar] $pct%"

$datetime_str = Get-Date -Format "MM-dd HH:mm"
Write-Host "$dir - $git_info | $model | $ctx_bar | $datetime_str"
```

---

## 可用的 JSON 資料欄位

Claude Code 透過 stdin 傳入以下資料：

| 欄位 | 說明 |
|------|------|
| `model.display_name` | 模型顯示名稱（如 `Claude Sonnet`） |
| `model.id` | 模型 ID（如 `claude-sonnet-4-6`） |
| `workspace.current_dir` | 當前工作目錄（推薦，優於 `cwd`） |
| `workspace.project_dir` | Claude Code 啟動時的目錄 |
| `context_window.used_percentage` | Context 使用百分比（session 初期可能為 null） |
| `context_window.remaining_percentage` | Context 剩餘百分比 |
| `context_window.context_window_size` | 最大 context 大小（預設 200000） |
| `context_window.total_input_tokens` | Session 累積輸入 token |
| `context_window.total_output_tokens` | Session 累積輸出 token |
| `cost.total_cost_usd` | Session 累積費用（美元） |
| `cost.total_duration_ms` | Session 總時長（毫秒） |
| `session_id` | 唯一 session ID |
| `vim.mode` | Vim 模式（`NORMAL` / `INSERT`，僅啟用時存在） |
| `agent.name` | 當前 agent 名稱（使用 `--agent` 時存在） |

> **注意**：`context_window.used_percentage` 在 session 開始前幾個訊息可能為 null，腳本需要提供 fallback 值（如 `// 0` 或 `// empty`）。

---

## 跨平台移植

### 匯出

只需複製兩個檔案：

```bash
cp ~/.claude/statusline-command.sh ~/dotfiles/claude/
cp ~/.claude/statusline-command.ps1 ~/dotfiles/claude/   # Windows 用
```

`settings.json` 中的 `statusLine` 區塊直接複製即可（使用 `~` 路徑，無需修改）。

### 匯入（新機器）

```bash
# Mac / Linux
cp statusline-command.sh ~/.claude/
chmod +x ~/.claude/statusline-command.sh
```

在 `~/.claude/settings.json` 加入：
```json
"statusLine": {
  "type": "command",
  "command": "~/.claude/statusline-command.sh"
}
```

### dotfiles 整合

```bash
# 建立 symlink
ln -sf ~/dotfiles/claude/statusline-command.sh ~/.claude/statusline-command.sh
```

---

## 測試方式

```bash
# 模擬 Claude Code 傳入的 JSON
echo '{
  "model": {"display_name": "Claude Sonnet"},
  "workspace": {"current_dir": "/Users/you/project"},
  "context_window": {"used_percentage": 42}
}' | ~/.claude/statusline-command.sh
```

---

## 常見問題

| 問題 | 解法 |
|------|------|
| 狀態列不顯示 | 確認腳本有 `chmod +x`，且輸出到 stdout |
| 顯示 `--` | session 初期 `used_percentage` 為 null，屬正常現象 |
| Windows 不生效 | 確認 settings.json 使用 PowerShell 版本的 command |
| 路徑在其他機器失效 | 確認使用 `~` 而非 `/Users/username/` 絕對路徑 |
| 顏色不顯示 | Windows 基本 PowerShell 不支援 ANSI，需額外設定 |

---

## 參考

- [官方文件](https://code.claude.com/docs/zh-TW/statusline)
- 社群專案：[ccstatusline](https://github.com/sirmalloc/ccstatusline)、[starship-claude](https://github.com/martinemde/starship-claude)

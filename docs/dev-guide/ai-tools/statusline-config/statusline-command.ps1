# Claude Code status line - PowerShell version (Windows)
# Format: ~/dir - main* | Claude Sonnet | [████░░░░░░] 42% | 03-07 14:32

$input_json = $input | Out-String | ConvertFrom-Json

$cwd   = $input_json.workspace.current_dir
$model = $input_json.model.display_name
$pct   = if ($null -ne $input_json.context_window.used_percentage) {
             [int]$input_json.context_window.used_percentage
         } else { 0 }

# --- Directory (replace home with ~) ---
$home_path = $env:USERPROFILE
$dir = if ($cwd -and $cwd.StartsWith($home_path)) {
    "~" + $cwd.Substring($home_path.Length).Replace('\', '/')
} else { $cwd }

# --- Git branch + dirty indicator ---
$git_info = "(no git)"
try {
    $branch = git -C $cwd symbolic-ref --short HEAD 2>$null
    if (-not $branch) { $branch = git -C $cwd rev-parse --short HEAD 2>$null }
    if ($branch) {
        $dirty = ""
        $has_changes = git -C $cwd status --porcelain 2>$null
        if ($has_changes) { $dirty = "*" }
        $git_info = "$branch$dirty"
    }
} catch {}

# --- Context window progress bar [████░░░░░░] 42% ---
$bar_width = 10
$filled = [math]::Floor($pct * $bar_width / 100)
$empty  = $bar_width - $filled
$bar = ("█" * $filled) + ("░" * $empty)
$ctx_bar = "[$bar] $pct%"

# --- Date and time ---
$datetime_str = Get-Date -Format "MM-dd HH:mm"

# Output (no ANSI on basic PowerShell; use Write-Host for color if needed)
Write-Host "$dir - $git_info | $model | $ctx_bar | $datetime_str"

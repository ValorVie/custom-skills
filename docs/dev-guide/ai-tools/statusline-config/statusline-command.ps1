# Claude Code status line - PowerShell version (Windows)
# Line 1: ~/dir - main*
# Line 2: Opus | [████░░░░░░] 42% | 03-07 14:32

$input_json = $input | Out-String | ConvertFrom-Json

$cwd   = $input_json.workspace.current_dir
$model = $input_json.model.display_name
$pct   = if ($null -ne $input_json.context_window.used_percentage) {
             [int]$input_json.context_window.used_percentage
         } else { 0 }

# --- Directory (replace home with ~, truncate if too long) ---
$home_path = $env:USERPROFILE
$dir = if ($cwd -and $cwd.StartsWith($home_path)) {
    "~" + $cwd.Substring($home_path.Length).Replace('\', '/')
} else { $cwd }
if ($dir.Length -gt 40) {
    $parts = $dir.TrimStart('/').Split('/')
    $last3 = $parts[-3..-1] -join '/'
    $dir = "~/…/$last3"
}

# --- Git branch + dirty indicator ---
$git_info = "(no git)"
try {
    $branch = git -C $cwd symbolic-ref --short HEAD 2>$null
    if (-not $branch) { $branch = git -C $cwd rev-parse --short HEAD 2>$null }
    if ($branch) {
        $dirty = if (git -C $cwd status --porcelain 2>$null) { "*" } else { "" }
        $git_info = "$branch$dirty"
    }
} catch {}

# --- Context window progress bar [████░░░░░░] 42% ---
$bar_width = 10
$filled = [math]::Floor($pct * $bar_width / 100)
$bar = ([string]::new([char]0x2588, $filled)) + ([string]::new([char]0x2591, $bar_width - $filled))
$ctx_bar = "[$bar] $pct%"

# --- Bar color based on usage ---
$e = [char]0x1B
if ($pct -ge 95) { $bar_color = "$e[38;5;196m" }      # red
elseif ($pct -ge 80) { $bar_color = "$e[38;5;208m" }   # orange
elseif ($pct -ge 50) { $bar_color = "$e[38;5;220m" }   # yellow
else { $bar_color = "$e[38;5;242m" }                     # grey (same as model)

$blue  = "$e[38;5;117m"
$grey  = "$e[38;5;242m"
$reset = "$e[0m"
$sep   = "$grey | $reset"

# --- Date and time ---
$datetime_str = Get-Date -Format "MM-dd HH:mm"

# Line 1: dir - branch
Write-Host "${blue}$dir - $git_info${reset}"
# Line 2: model | progress bar | datetime
Write-Host "${grey}${model}${sep}${bar_color}${ctx_bar}${reset}${sep}${grey}${datetime_str}${reset}"

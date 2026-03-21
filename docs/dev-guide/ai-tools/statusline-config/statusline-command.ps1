# Claude Code status line - PowerShell version (Windows)
# Line 1: ~/dir - main*
# Line 2: Opus 4.6 (1M context) | ctx 42% | 5h: 40% | 7d: 15% | 03-21 13:19

$input_json = $input | Out-String | ConvertFrom-Json

$cwd   = $input_json.workspace.current_dir
$model = $input_json.model.display_name
$pct   = if ($null -ne $input_json.context_window.used_percentage) {
             [int]$input_json.context_window.used_percentage
         } else { $null }
$rate_5h = if ($null -ne $input_json.rate_limits.five_hour.used_percentage) {
               [int]$input_json.rate_limits.five_hour.used_percentage
           } else { $null }
$rate_7d = if ($null -ne $input_json.rate_limits.seven_day.used_percentage) {
               [int]$input_json.rate_limits.seven_day.used_percentage
           } else { $null }

$e = [char]0x1B
$blue   = "$e[38;5;117m"
$grey   = "$e[38;5;242m"
$green  = "$e[38;5;114m"
$yellow = "$e[38;5;220m"
$orange = "$e[38;5;208m"
$red    = "$e[38;5;196m"
$reset  = "$e[0m"
$sep    = "$grey | $reset"

# --- Color picker by percentage ---
function Get-PctColor($val) {
    if ($null -eq $val) { return $grey }
    if ($val -ge 95) { return $red }
    if ($val -ge 80) { return $orange }
    if ($val -ge 50) { return $yellow }
    return $grey
}

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

# --- Context, rate limits ---
$ctx_str = if ($null -ne $pct) { "ctx $pct%" } else { "ctx --%" }
$r5h_str = if ($null -ne $rate_5h) { "5h: $rate_5h%" } else { "5h: --%" }
$r7d_str = if ($null -ne $rate_7d) { "7d: $rate_7d%" } else { "7d: --%" }

$ctx_color = Get-PctColor $pct
$r5h_color = Get-PctColor $rate_5h
$r7d_color = Get-PctColor $rate_7d

# --- Date and time ---
$datetime_str = Get-Date -Format "MM-dd HH:mm"

# Line 1: dir - branch
Write-Host "${blue}$dir - $git_info${reset}"
# Line 2: model | ctx XX% | 5h: XX% | 7d: XX% | datetime
Write-Host "${grey}${model}${sep}${ctx_color}${ctx_str}${reset}${sep}${r5h_color}${r5h_str}${reset}${sep}${r7d_color}${r7d_str}${reset}${sep}${grey}${datetime_str}${reset}"

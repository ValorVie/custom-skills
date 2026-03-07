#!/usr/bin/env bash
# Claude Code status line - Pure/p10k style
# Format: ~/dir - main* | Claude Sonnet | [████░░░░░░] 42% | 03-07 14:32

input=$(cat)

cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')
model=$(echo "$input" | jq -r '.model.display_name // ""')
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')

# Colors (ANSI, will render dimmed in status line)
blue='\033[38;5;117m'
grey='\033[38;5;242m'
cyan='\033[38;5;117m'
reset='\033[0m'
sep="${grey} | ${reset}"

# --- Directory ---
dir="${cwd/#$HOME/~}"

# --- Git branch + dirty indicator ---
git_info="(no git)"
if git_branch=$(git -C "$cwd" symbolic-ref --short HEAD 2>/dev/null || git -C "$cwd" rev-parse --short HEAD 2>/dev/null); then
  dirty=""
  if ! git -C "$cwd" diff --quiet 2>/dev/null || ! git -C "$cwd" diff --cached --quiet 2>/dev/null; then
    dirty="*"
  elif git -C "$cwd" ls-files --others --exclude-standard --error-unmatch . >/dev/null 2>&1; then
    dirty="*"
  fi
  git_info="${git_branch}${dirty}"
fi

# --- dir - branch ---
dir_branch="${dir} - ${git_info}"

# --- Context window progress bar ---
# Format: [████░░░░░░] 42%
ctx_bar=""
if [ -n "$used_pct" ]; then
  used_int=${used_pct%.*}
  bar_width=10
  filled=$(( used_int * bar_width / 100 ))
  empty=$(( bar_width - filled ))
  bar=""
  for (( i=0; i<filled; i++ )); do bar="${bar}█"; done
  for (( i=0; i<empty;  i++ )); do bar="${bar}░"; done
  ctx_bar="[${bar}] ${used_int}%"
else
  ctx_bar="[░░░░░░░░░░] --%"
fi

# --- Date and time ---
datetime_str=$(date +"%m-%d %H:%M")

printf "${blue}%s${reset}${sep}${grey}%s${sep}${cyan}%s${reset}${sep}${grey}%s${reset}\n" \
  "$dir_branch" \
  "$model" \
  "$ctx_bar" \
  "$datetime_str"

#!/usr/bin/env bash
# Claude Code status line - Pure/p10k style
# Line 1: ~/dir - main*
# Line 2: Opus 4.6 (1M context) | ctx 42% | 5h: 40% | 7d: 15% | 03-21 13:19

input=$(cat)

cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')
model=$(echo "$input" | jq -r '.model.display_name // ""')
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
rate_5h=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
rate_7d=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')

# Colors (ANSI)
blue='\033[38;5;117m'
grey='\033[38;5;242m'
green='\033[38;5;114m'
yellow='\033[38;5;220m'
orange='\033[38;5;208m'
red='\033[38;5;196m'
reset='\033[0m'
sep="${grey} | ${reset}"

# --- Color picker by percentage ---
pct_color() {
  local val="$1"
  if [ -z "$val" ]; then echo "$grey"; return; fi
  if [ "$val" -ge 95 ]; then echo "$red"
  elif [ "$val" -ge 80 ]; then echo "$orange"
  elif [ "$val" -ge 50 ]; then echo "$yellow"
  else echo "$grey"
  fi
}

# --- Directory (truncate if too long) ---
dir="${cwd/#$HOME/~}"
max_dir_len=40
if [ ${#dir} -gt $max_dir_len ]; then
  last3=$(echo "$dir" | awk -F'/' '{print $(NF-2)"/"$(NF-1)"/"$NF}')
  dir="~/…/${last3}"
fi

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

# --- Context usage ---
if [ -n "$used_pct" ]; then
  ctx_int=${used_pct%.*}
  ctx_str="ctx ${ctx_int}%"
else
  ctx_str="ctx --%"
  ctx_int=""
fi

# --- Rate limits ---
if [ -n "$rate_5h" ]; then
  r5h_int=${rate_5h%.*}
  r5h_str="5h: ${r5h_int}%"
else
  r5h_str="5h: --%"
  r5h_int=""
fi

if [ -n "$rate_7d" ]; then
  r7d_int=${rate_7d%.*}
  r7d_str="7d: ${r7d_int}%"
else
  r7d_str="7d: --%"
  r7d_int=""
fi

# --- Date and time ---
datetime_str=$(date +"%m-%d %H:%M")

# --- Output ---
# Line 1: dir - branch
printf "${blue}%s - %s${reset}\n" "$dir" "$git_info"

# Line 2: model | ctx XX% | 5h: XX% | 7d: XX% | datetime
ctx_color=$(pct_color "$ctx_int")
r5h_color=$(pct_color "$r5h_int")
r7d_color=$(pct_color "$r7d_int")

printf "${grey}%s${sep}${ctx_color}%s${reset}${sep}${r5h_color}%s${reset}${sep}${r7d_color}%s${reset}${sep}${grey}%s${reset}\n" \
  "$model" \
  "$ctx_str" \
  "$r5h_str" \
  "$r7d_str" \
  "$datetime_str"

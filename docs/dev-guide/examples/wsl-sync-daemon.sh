#!/usr/bin/env bash
# ============================================
# wsl-sync-daemon.sh — WSL → Windows 即時檔案同步
# ============================================
# 依賴: inotifywait (inotify-tools), rsync
#
# 用法:
#   wsl-sync-daemon.sh <src> <dst> [exclude-file]
#
# 範例:
#   wsl-sync-daemon.sh ~/Code/project /mnt/f/Code/project
#   wsl-sync-daemon.sh ~/Code/project /mnt/f/Code/project ~/.config/sync-exclude.txt
#
# 停止:
#   pkill -f wsl-sync-daemon
#
# 安裝依賴:
#   sudo apt install inotify-tools rsync

set -euo pipefail

SRC="${1:?用法: wsl-sync-daemon.sh <src> <dst> [exclude-file]}"
DST="${2:?用法: wsl-sync-daemon.sh <src> <dst> [exclude-file]}"
EXCLUDE_FILE="${3:-$HOME/.config/sync-exclude.txt}"

SRC="${SRC%/}"
DST="${DST%/}"

# 載入排除規則
INOTIFY_EXCLUDE_PARTS=()
EXCLUDE_PATTERNS=()
RSYNC_EXCLUDE_ARGS=()
if [ -f "$EXCLUDE_FILE" ]; then
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    line="${line%/}"
    EXCLUDE_PATTERNS+=("$line")
    RSYNC_EXCLUDE_ARGS+=(--exclude "$line")
    escaped="${line//./\\.}"
    escaped="${escaped//\*/.*}"
    INOTIFY_EXCLUDE_PARTS+=("/${escaped}(/|$)")
  done < "$EXCLUDE_FILE"
  echo "[sync] 排除規則: $EXCLUDE_FILE (${#EXCLUDE_PATTERNS[@]} 條)"
else
  echo "[sync] 警告: 排除檔案不存在: $EXCLUDE_FILE"
fi

# 判斷路徑是否應被排除
should_exclude() {
  local path="$1"
  for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    case "$path" in
      ${pattern}/*|${pattern}|*/${pattern}/*|*/${pattern}) return 0 ;;
    esac
  done
  return 1
}

# 組合 inotifywait 排除正則
INOTIFY_EXCLUDE=""
if [ ${#INOTIFY_EXCLUDE_PARTS[@]} -gt 0 ]; then
  INOTIFY_EXCLUDE=$(IFS='|'; echo "${INOTIFY_EXCLUDE_PARTS[*]}")
fi

mkdir -p "$DST"

echo "[sync] $SRC → $DST"
echo "[sync] 初始同步中 (rsync 差量)..."

rsync -a --delete "${RSYNC_EXCLUDE_ARGS[@]}" "$SRC/" "$DST/"
echo "[sync] 初始同步完成"
echo "[sync] 監聽中... (Ctrl+C 停止)"

# inotifywait 監聽變更，逐檔同步
INOTIFY_ARGS=(-r -m -q --format '%w%f' -e modify -e create -e delete -e move "$SRC")
if [ -n "$INOTIFY_EXCLUDE" ]; then
  INOTIFY_ARGS=(--exclude "$INOTIFY_EXCLUDE" "${INOTIFY_ARGS[@]}")
fi

inotifywait "${INOTIFY_ARGS[@]}" | while IFS= read -r changed_path; do
  rel="${changed_path#$SRC/}"

  if should_exclude "$rel"; then
    continue
  fi

  src_file="$SRC/$rel"
  dst_file="$DST/$rel"

  if [ -f "$src_file" ]; then
    mkdir -p "$(dirname "$dst_file")"
    cp "$src_file" "$dst_file"
    echo "[sync] → $rel"
  elif [ -d "$src_file" ]; then
    mkdir -p "$dst_file"
  elif [ ! -e "$src_file" ]; then
    rm -rf "$dst_file"
    echo "[sync] ✗ $rel (deleted)"
  fi
done

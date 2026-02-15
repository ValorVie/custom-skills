#!/usr/bin/env bash
# ============================================
# wsl-sync-manager.sh — 多專案統一同步管理
# ============================================
# 依賴: wsl-sync-daemon.sh, inotify-tools, rsync
#
# 用法:
#   wsl-sync-manager.sh [config-file]
#
# 預設設定檔: ~/.config/sync-projects.txt
#
# 設定檔格式:
#   # 註解
#   <WSL路徑>  <Windows路徑>  [排除規則檔]
#
# 停止:
#   pkill -f wsl-sync-manager

set -euo pipefail

CONFIG="${1:-$HOME/.config/sync-projects.txt}"
DEFAULT_EXCLUDE="$HOME/.config/sync-exclude.txt"
DAEMON="$HOME/.local/bin/wsl-sync-daemon.sh"

if [ ! -f "$CONFIG" ]; then
  echo "[manager] 錯誤: 設定檔不存在: $CONFIG"
  echo "[manager] 請建立設定檔，格式:"
  echo "  ~/Code/project  /mnt/f/Code/project"
  exit 1
fi

if [ ! -x "$DAEMON" ]; then
  echo "[manager] 錯誤: 同步腳本不存在或無執行權限: $DAEMON"
  exit 1
fi

# 收集子程序 PID（daemon PID + sed PID）
CHILD_PIDS=()

cleanup() {
  echo ""
  echo "[manager] 正在停止所有同步..."
  for pid in "${CHILD_PIDS[@]}"; do
    kill -- -"$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null
  echo "[manager] 已停止"
  exit 0
}

trap cleanup SIGINT SIGTERM

# 讀取設定，啟動每個專案
PROJECT_COUNT=0
while IFS= read -r line; do
  # 跳過註解和空行
  [[ -z "$line" || "$line" == \#* ]] && continue

  # 解析欄位: src  dst  [exclude]
  read -r src dst exclude <<< "$line"

  # 展開 ~
  src="${src/#\~/$HOME}"
  dst="${dst/#\~/$HOME}"

  if [ -z "$src" ] || [ -z "$dst" ]; then
    echo "[manager] 警告: 格式錯誤，跳過: $line"
    continue
  fi

  if [ ! -d "$src" ]; then
    echo "[manager] 警告: 來源目錄不存在，跳過: $src"
    continue
  fi

  # 排除規則：行內指定 > 預設
  exclude="${exclude:-$DEFAULT_EXCLUDE}"
  exclude="${exclude/#\~/$HOME}"

  project_name="$(basename "$src")"
  echo "[manager] 啟動同步: $project_name"

  # 在背景啟動 daemon，日誌加前綴（sed -u 避免緩衝）
  "$DAEMON" "$src" "$dst" "$exclude" 2>&1 | sed -u "s/^\[sync\]/[$project_name]/" &
  CHILD_PIDS+=($!)
  PROJECT_COUNT=$((PROJECT_COUNT + 1))
done < "$CONFIG"

if [ "$PROJECT_COUNT" -eq 0 ]; then
  echo "[manager] 設定檔中無有效專案: $CONFIG"
  exit 1
fi

echo "[manager] 共 $PROJECT_COUNT 個專案同步中 (Ctrl+C 停止全部)"
echo "---"

# 等待所有子程序
wait

# claude-mem 除錯指南

本指南涵蓋 claude-mem 插件的常見問題診斷、日誌分析與修復命令。

---

## 架構概覽

```
Claude Code Session
  |-- Hook (worker-service.cjs)      --> 與 Worker 通訊
  |-- MCP Server (mcp-server.cjs)    --> 提供搜尋工具
  +-- Worker Daemon (worker-wrapper.cjs -> worker-service.cjs)
        +-- HTTP Server @ 127.0.0.1:37777
```

| 元件 | 說明 |
|------|------|
| **Worker Daemon** | 常駐 HTTP 服務，處理觀察紀錄、搜尋、session 管理 |
| **Hook Scripts** | 在 Claude Code 事件觸發時與 Worker 通訊 |
| **MCP Server** | 提供 search、timeline、get_observations 等工具 |

---

## 1. 檢查：確認系統狀態

### 1.1 檢查 Worker 是否存活

```bash
# Linux/WSL
ss -tlnp | grep 37777

# macOS（macOS 沒有 ss，使用 lsof）
lsof -iTCP:37777 -sTCP:LISTEN

# Windows (PowerShell)
Get-NetTCPConnection -LocalPort 37777 -ErrorAction SilentlyContinue

# Windows (cmd)
netstat -ano | findstr "37777"
```

### 1.2 檢查 bun 是否安裝

```bash
# Linux/WSL/macOS
which bun && bun --version

# macOS 安裝 bun（如果未安裝）
brew install oven-sh/bun/bun
# 或
curl -fsSL https://bun.sh/install | bash
```

若未安裝，參考 https://bun.sh 安裝。

### 1.3 確認插件路徑

```bash
# Linux/WSL/macOS：插件快取路徑（版本號可能不同）
PLUGIN_DIR="$HOME/.claude/plugins/cache/thedotmack/claude-mem"
ls "$PLUGIN_DIR"/

# Windows 路徑
# %USERPROFILE%\.claude\plugins\cache\thedotmack\claude-mem\<version>
```

### 1.4 檢查設定檔

```bash
# Linux/WSL/macOS
cat ~/.claude-mem/settings.json

# macOS 也可以用 open 快速編輯
open ~/.claude-mem/settings.json
```

關鍵欄位：

| 設定 | 預設值 | 說明 |
|------|--------|------|
| `CLAUDE_MEM_WORKER_PORT` | `37777` | Worker HTTP 服務端口 |
| `CLAUDE_MEM_WORKER_HOST` | `127.0.0.1` | Worker 綁定地址 |
| `CLAUDE_MEM_DATA_DIR` | `~/.claude-mem` | 資料與日誌目錄 |
| `CLAUDE_MEM_LOG_LEVEL` | `INFO` | 日誌等級 (DEBUG/INFO/WARN/ERROR) |
| `CLAUDE_MEM_PROVIDER` | `claude` | AI 提供商 (claude/gemini/openrouter) |

### 1.5 Health Check

```bash
curl -s http://127.0.0.1:37777/health | jq .
```

成功回應表示 Worker 正常運行。無回應表示 Worker 未啟動。

---

## 2. 分析：查看日誌

### 2.1 日誌位置

```bash
ls ~/.claude-mem/logs/
# 格式: claude-mem-YYYY-MM-DD.log
```

### 2.2 查看今日日誌

```bash
cat ~/.claude-mem/logs/claude-mem-$(date +%Y-%m-%d).log
```

### 2.3 即時追蹤日誌

```bash
tail -f ~/.claude-mem/logs/claude-mem-$(date +%Y-%m-%d).log
```

### 2.4 只看錯誤

```bash
grep '\[ERROR\]' ~/.claude-mem/logs/claude-mem-$(date +%Y-%m-%d).log
```

### 2.5 macOS Console.app 查看日誌

```bash
# 用 macOS 內建的 Console.app 開啟日誌（方便 GUI 篩選）
open -a Console ~/.claude-mem/logs/claude-mem-$(date +%Y-%m-%d).log
```

### 2.6 常見日誌模式解讀

| 日誌訊息 | 含義 | 處理方式 |
|----------|------|----------|
| `Worker available` | Worker 正常運行 | 無需處理 |
| `Worker already running and healthy` | Worker 健康檢查通過 | 無需處理 |
| `Worker not available` | Worker 未啟動或已崩潰 | 見 3.1 |
| `Failed to start server. Is port 37777 in use?` | 端口被佔用 | 見 3.2 |
| `Worker failed to start (health check timeout)` | 啟動後 health check 超時 | 見 3.3 |
| `Worker did not become ready within 15 seconds` | Hook 等待 Worker 回應超時 | 見 3.4 |
| `INIT_COMPLETE` | Session 初始化成功 | 無需處理 |

---

## 3. 執行：修復命令

### 3.1 手動啟動 Worker

```bash
# 找到最新版本的插件目錄（Linux/WSL）
PLUGIN_DIR=$(ls -d ~/.claude/plugins/cache/thedotmack/claude-mem/*/ | sort -V | tail -1)

# macOS 的 sort 不支援 -V，使用替代方案：
PLUGIN_DIR=$(ls -d ~/.claude/plugins/cache/thedotmack/claude-mem/*/ | sort -t. -k1,1n -k2,2n -k3,3n | tail -1)

# 啟動 Worker（前台模式，用於除錯）
cd "$PLUGIN_DIR/scripts"
bun worker-service.cjs start

# 啟動 Worker（透過 wrapper，正式模式）
bun worker-wrapper.cjs
```

### 3.2 端口被佔用：殺掉舊進程

Linux/WSL:

```bash
# 找到佔用 37777 的進程
ss -tlnp | grep 37777

# 殺掉佔用端口的進程
kill $(lsof -t -i :37777)

# 確認端口已釋放（應該無輸出）
ss -tlnp | grep 37777
```

macOS:

```bash
# 找到佔用 37777 的進程
lsof -iTCP:37777 -sTCP:LISTEN

# 殺掉佔用端口的進程
kill $(lsof -t -iTCP:37777)

# 確認端口已釋放（應該無輸出）
lsof -iTCP:37777 -sTCP:LISTEN
```

Windows PowerShell:

```powershell
$pid = (Get-NetTCPConnection -LocalPort 37777 -ErrorAction SilentlyContinue).OwningProcess
if ($pid) { Stop-Process -Id $pid -Force }
```

重新啟動 Worker:

```bash
PLUGIN_DIR=$(ls -d ~/.claude/plugins/cache/thedotmack/claude-mem/*/ | sort -V | tail -1)
cd "$PLUGIN_DIR/scripts" && bun worker-service.cjs start
```

### 3.3 Health Check 超時：完整重啟流程

```bash
# 1. 殺掉所有相關進程
pkill -f "worker-service.cjs" 2>/dev/null
pkill -f "worker-wrapper.cjs" 2>/dev/null

# macOS 如果 pkill 不可用：
# kill $(pgrep -f "worker-service.cjs") 2>/dev/null
# kill $(pgrep -f "worker-wrapper.cjs") 2>/dev/null

# 2. 等待端口釋放
sleep 3

# 3. 確認端口已釋放
# Linux/WSL
ss -tlnp | grep 37777
# macOS
lsof -iTCP:37777 -sTCP:LISTEN

# 4. 重新啟動
PLUGIN_DIR=$(ls -d ~/.claude/plugins/cache/thedotmack/claude-mem/*/ | sort -V | tail -1)
cd "$PLUGIN_DIR/scripts" && bun worker-wrapper.cjs &

# 5. 驗證
sleep 5
curl -s http://127.0.0.1:37777/health
```

### 3.4 Hook 15 秒超時：最簡修復

這通常發生在 Claude Code 啟動時 Worker 尚未就緒。

```bash
# 最簡單的方法：完全退出 Claude Code，等待端口釋放，再重啟
# Hook 會自動啟動 Worker

# 如果反覆發生，手動預啟動 Worker：
PLUGIN_DIR=$(ls -d ~/.claude/plugins/cache/thedotmack/claude-mem/*/ | sort -V | tail -1)
cd "$PLUGIN_DIR/scripts" && bun worker-wrapper.cjs &
sleep 5
# 然後再啟動 Claude Code
```

### 3.5 變更 Worker 端口

如果 37777 經常被其他程式佔用：

```bash
# 編輯設定檔
vi ~/.claude-mem/settings.json
# 將 CLAUDE_MEM_WORKER_PORT 改為其他端口，例如 "38888"

# macOS 也可以用 open 編輯
open ~/.claude-mem/settings.json

# 重啟 Worker 使其生效
pkill -f "worker-service.cjs" 2>/dev/null
sleep 2
# 下次啟動 Claude Code 時會自動用新端口
```

### 3.6 完全重置（保留資料）

```bash
# 1. 殺掉所有 Worker 進程
pkill -f "worker-service.cjs" 2>/dev/null
pkill -f "worker-wrapper.cjs" 2>/dev/null

# 2. 清除日誌（保留設定和資料）
rm -f ~/.claude-mem/logs/*.log

# 3. 重新啟動 Claude Code（Hook 會自動啟動 Worker）
```

---

## 4. macOS 專用注意事項

### macOS 防火牆提示

首次啟動 Worker 時，macOS 可能彈出「是否允許連入連線」的防火牆提示。由於 Worker 只綁定 `127.0.0.1`（本機），可以選擇「拒絕」而不影響功能。選「允許」也沒有安全風險。

### macOS 的 lsof 用法差異

macOS 的 `lsof` 語法與 Linux 略有不同：

```bash
# macOS 查端口
lsof -iTCP:37777 -sTCP:LISTEN

# macOS 殺掉佔用端口的進程
kill $(lsof -t -iTCP:37777)

# Linux 查端口（對比）
ss -tlnp | grep 37777
```

### macOS sort -V 不可用

macOS 內建的 `sort` 不支援 `-V`（版本排序），尋找插件目錄時使用替代方案：

```bash
# 替代 sort -V
PLUGIN_DIR=$(ls -d ~/.claude/plugins/cache/thedotmack/claude-mem/*/ | sort -t. -k1,1n -k2,2n -k3,3n | tail -1)
```

### Homebrew 安裝 bun

```bash
brew install oven-sh/bun/bun
```

### macOS 開機自動啟動 Worker（可選）

如果希望 Worker 隨系統啟動，可建立 LaunchAgent：

```xml
<!-- ~/Library/LaunchAgents/com.claude-mem.worker.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claude-mem.worker</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_USERNAME/.bun/bin/bun</string>
        <string>worker-wrapper.cjs</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/YOUR_USERNAME/.claude/plugins/cache/thedotmack/claude-mem/CURRENT_VERSION/scripts</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/claude-mem-worker.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/claude-mem-worker.err</string>
</dict>
</plist>
```

管理指令：

```bash
# 載入（需自行替換 YOUR_USERNAME 和 CURRENT_VERSION）
launchctl load ~/Library/LaunchAgents/com.claude-mem.worker.plist

# 卸載
launchctl unload ~/Library/LaunchAgents/com.claude-mem.worker.plist

# 查看狀態
launchctl list | grep claude-mem
```

> **注意**：插件更新版本後需修改 plist 中的路徑。

---

## 5. Windows 專用注意事項

### 路徑對照

| 項目 | Linux/macOS | Windows |
|------|------------|---------|
| 設定檔 | `~/.claude-mem/settings.json` | `%USERPROFILE%\.claude-mem\settings.json` |
| 日誌 | `~/.claude-mem/logs/` | `%USERPROFILE%\.claude-mem\logs\` |
| 插件 | `~/.claude/plugins/cache/` | `%USERPROFILE%\.claude\plugins\cache\` |

### npm run worker:restart 無法使用

`npm run worker:restart` 是插件開發者的指令，需要在插件**原始碼**目錄執行，而非插件快取目錄或使用者的專案目錄。使用者應直接用 bun 命令：

```cmd
cd %USERPROFILE%\.claude\plugins\cache\thedotmack\claude-mem\<version>\scripts
bun worker-service.cjs start
```

### Windows 殺進程

```powershell
# 找到並殺掉佔用端口的進程
$pid = (Get-NetTCPConnection -LocalPort 37777 -ErrorAction SilentlyContinue).OwningProcess
if ($pid) { Stop-Process -Id $pid -Force }

# 或殺掉所有 bun 進程
Get-Process -Name bun -ErrorAction SilentlyContinue | Stop-Process -Force
```

---

## 6. 快速診斷流程

```
錯誤發生
  |
  +-- "Worker did not become ready within 15 seconds"
  |     --> 退出 Claude Code -> 等 5 秒 -> 重啟
  |
  +-- "Failed to start server. Is port 37777 in use?"
  |     --> 殺掉佔用端口的進程 -> 重啟 Worker (3.2)
  |
  +-- "Worker not available"
  |     --> 手動啟動 Worker (3.1)
  |
  +-- "Worker failed to start (health check timeout)"
  |     --> 完全重啟流程 (3.3)
  |
  +-- 其他錯誤
        --> 查看日誌 (2.4) -> 回報 issue
            https://github.com/thedotmack/claude-mem/issues
```

---

## 7. 跨平台命令速查表

| 操作 | Linux/WSL | macOS | Windows |
|------|-----------|-------|---------|
| 查端口 | `ss -tlnp \| grep 37777` | `lsof -iTCP:37777 -sTCP:LISTEN` | `netstat -ano \| findstr "37777"` |
| 殺端口進程 | `kill $(lsof -t -i :37777)` | `kill $(lsof -t -iTCP:37777)` | `Stop-Process -Id (Get-NetTCPConnection -LocalPort 37777).OwningProcess` |
| 殺所有 Worker | `pkill -f "worker-service.cjs"` | `pkill -f "worker-service.cjs"` | `Get-Process -Name bun \| Stop-Process` |
| 找插件目錄 | `ls -d ~/.claude/plugins/cache/thedotmack/claude-mem/*/` | 同 Linux | `dir %USERPROFILE%\.claude\plugins\cache\thedotmack\claude-mem\` |
| 查日誌 | `cat ~/.claude-mem/logs/claude-mem-$(date +%Y-%m-%d).log` | 同 Linux | `type %USERPROFILE%\.claude-mem\logs\claude-mem-YYYY-MM-DD.log` |
| Health Check | `curl -s http://127.0.0.1:37777/health` | 同 Linux | `curl -s http://127.0.0.1:37777/health` |

# WSL ↔ Windows 檔案同步指南

在 WSL 中開發、Windows 環境執行（例如需要開啟瀏覽器的 Puppeteer 專案）時的檔案同步方案。

---

## 依賴安裝

```bash
sudo apt install -y inotify-tools rsync
```

| 工具 | 用途 |
|------|------|
| `inotify-tools` | 提供 `inotifywait`，監聽檔案系統事件（WSL 原生支援） |
| `rsync` | 差量同步，僅傳輸變更的檔案（初始同步與手動同步） |

---

## 方案總覽

| 方案 | 延遲 | CPU 占用 | 適合場景 |
|------|------|----------|----------|
| [A. 共用檔案系統](#a-共用檔案系統直接在-mnt-開發) | 零 | 無 | 小專案、不在意 I/O 效能 |
| [B. rsync 手動同步](#b-rsync-手動同步) | 手動觸發 | 僅同步時 | 偶爾同步、簡單場景 |
| [C. inotifywait + rsync 自動同步](#c-inotifywait--rsync-自動同步推薦) | <0.5 秒 | 極低 | 持續開發、頻繁修改 |

---

## A. 共用檔案系統（直接在 /mnt/ 開發）

最簡單的方案——專案放在 Windows 檔案系統上，WSL 透過 `/mnt/` 存取。

```bash
# 專案位置（Windows 端）
F:\Code\project-name

# WSL 存取
/mnt/f/Code/project-name

# Windows 執行
cd F:\Code\project-name && npm start
```

**優點：** 零設定、零同步成本
**缺點：** WSL 下 I/O 較慢（`/mnt/` 走 9P 協定），git 操作和 npm install 明顯變慢

---

## B. rsync 手動同步

專案保留在 WSL 原生檔案系統（效能好），需要時手動差量同步到 Windows。

### 基本用法

```bash
# WSL → Windows（差量同步，僅傳輸變更檔案）
rsync -av --delete \
  --exclude-from="$HOME/.config/sync-exclude.txt" \
  /home/user/Code/project/ \
  /mnt/f/Code/project/

# Windows → WSL
rsync -av --delete \
  --exclude-from="$HOME/.config/sync-exclude.txt" \
  /mnt/f/Code/project/ \
  /home/user/Code/project/
```

### 設定 alias

```bash
# ~/.zshrc 或 ~/.bashrc
alias psync='rsync -av --delete --exclude-from="$HOME/.config/sync-exclude.txt" /home/user/Code/project/ /mnt/f/Code/project/'
alias psync-back='rsync -av --delete --exclude-from="$HOME/.config/sync-exclude.txt" /mnt/f/Code/project/ /home/user/Code/project/'
```

### 排除檔案設定

見 [排除規則設定](#排除規則設定) 章節。

---

## C. inotifywait + rsync 自動同步（推薦）

使用 `inotifywait` 監聽檔案變更，即時同步到 Windows。啟動時以 `rsync` 做差量初始同步，之後逐檔即時同步。

### 架構

```
┌─────────────────────────────────────────────┐
│ WSL (開發端)                                 │
│                                             │
│  inotifywait 監聽 ──→ 變更事件 ──→ cp 單檔   │
│                                             │
│  rsync (啟動時) ──→ 差量初始同步              │
│                                             │
│  排除規則 ←── ~/.config/sync-exclude.txt     │
└──────────────────────┬──────────────────────┘
                       │ /mnt/
                       ▼
┌─────────────────────────────────────────────┐
│ Windows (執行端)                             │
│  npm start / puppeteer / 瀏覽器              │
└─────────────────────────────────────────────┘
```

### 安裝同步腳本

```bash
# 從範例複製
cp docs/dev-guide/examples/wsl-sync-daemon.sh ~/.local/bin/
chmod +x ~/.local/bin/wsl-sync-daemon.sh

# 複製排除規則
cp docs/dev-guide/examples/sync-exclude.example.txt ~/.config/sync-exclude.txt
```

或手動建立，見 [examples/wsl-sync-daemon.sh](../examples/wsl-sync-daemon.sh)。

### 啟動方式

```bash
# 前景執行（可看即時日誌）
wsl-sync-daemon.sh ~/Code/project /mnt/f/Code/project

# 自訂排除規則檔案
wsl-sync-daemon.sh ~/Code/project /mnt/f/Code/project ~/.config/my-exclude.txt

# 背景執行
nohup wsl-sync-daemon.sh ~/Code/project /mnt/f/Code/project \
  > /tmp/project-sync.log 2>&1 &

# 查看日誌
tail -f /tmp/project-sync.log

# 停止
pkill -f wsl-sync-daemon
```

### 輸出範例

```
[sync] 排除規則: /home/user/.config/sync-exclude.txt (20 條)
[sync] /home/user/Code/project → /mnt/f/Code/project
[sync] 初始同步中 (rsync 差量)...
[sync] 初始同步完成
[sync] 監聽中... (Ctrl+C 停止)
[sync] → src/index.js
[sync] → src/utils/helper.js
[sync] ✗ src/old-file.js (deleted)
```

### 搭配 systemd（開機自啟）

```bash
# 複製 service 範例
mkdir -p ~/.config/systemd/user
cp docs/dev-guide/examples/wsl-sync-golem.service ~/.config/systemd/user/

# 修改 service 檔中的路徑後啟用
systemctl --user daemon-reload
systemctl --user enable --now wsl-sync-golem.service

# 管理
systemctl --user status wsl-sync-golem.service    # 查看狀態
systemctl --user restart wsl-sync-golem.service    # 重啟
journalctl --user -u wsl-sync-golem.service -f     # 查看日誌
```

見 [examples/wsl-sync-golem.service](../examples/wsl-sync-golem.service)。

---

## 排除規則設定

所有方案共用同一份排除檔案 `~/.config/sync-exclude.txt`。

### 格式說明

```
# 這是註解（# 開頭的行會被忽略）
# 空行也會被忽略
# 每行一個規則

# 目錄名稱（會排除所有同名目錄）
node_modules
.venv

# 特定檔案
.env

# 萬用字元
*.log
```

### 範例檔案

見 [sync-exclude.example.txt](../examples/sync-exclude.example.txt)，包含常見的排除規則。

安裝：

```bash
cp docs/dev-guide/examples/sync-exclude.example.txt ~/.config/sync-exclude.txt
# 依需求編輯
vim ~/.config/sync-exclude.txt
```

### 常用排除清單

| 類別 | 排除項目 | 說明 |
|------|----------|------|
| **套件管理** | `node_modules`, `.venv`, `venv`, `vendor`, `__pycache__` | 兩端各自安裝 |
| **環境設定** | `.env`, `.env.local` | 兩端環境可能不同 |
| **建置產物** | `dist`, `build`, `.next`, `.nuxt` | 兩端各自建置 |
| **快取** | `.cache`, `.turbo`, `.parcel-cache` | 暫存檔無需同步 |
| **IDE** | `.idea`, `.vscode` | 個人設定 |
| **版本控制** | `.git` | 兩端各自管理（或只用單邊 git） |
| **日誌** | `*.log`, `logs/` | 執行時產生 |
| **系統檔案** | `.DS_Store`, `Thumbs.db`, `desktop.ini` | OS 暫存 |

---

## 注意事項

### node_modules 處理

排除 `node_modules` 後，Windows 端需要獨立安裝：

```powershell
# Windows PowerShell
cd F:\Code\project-golem
npm install
```

兩端的 `node_modules` 是獨立的，不會互相干擾。

### .git 同步策略

- **建議排除 `.git`：** 兩端各自管理 git，避免跨平台 lock file 衝突
- **如果需要同步 `.git`：** 只在一端操作 git，另一端視為唯讀

### 檔案權限

WSL 和 Windows 的權限模型不同。同步後 Windows 端可能出現權限問題：

```bash
# 如果 Windows 端腳本無法執行，手動修正
chmod +x /mnt/f/Code/project-golem/*.sh
```

### 效能考量

- `inotifywait` 在 WSL2 上原生支援，記憶體占用極低
- rsync 初始同步使用差量比對，重啟 daemon 時只傳輸變更檔案
- `/mnt/` 路徑的寫入速度約為 WSL 原生的 1/3~1/5
- 大量小檔案同步（如 `npm install` 後的 node_modules）會很慢——務必排除

### 疑難排解

```bash
# inotifywait 監聽數量不夠
# 如果檔案很多，可能需要調高 inotify watch 上限
echo 'fs.inotify.max_user_watches=524288' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# 確認 daemon 是否在跑
ps aux | grep wsl-sync-daemon

# 確認排除規則是否正確
cat ~/.config/sync-exclude.txt
```

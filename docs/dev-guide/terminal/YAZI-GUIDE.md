# Yazi 終端檔案管理器完整指南

## 目錄

- [簡介與定位](#簡介與定位)
- [安裝方式（多平台）](#安裝方式多平台)
- [必要與選配依賴](#必要與選配依賴)
- [設定檔路徑與初始化](#設定檔路徑與初始化)
- [快速開始](#快速開始)
- [常用操作](#常用操作)
- [實用整合](#實用整合)
- [遠端檔案傳輸（SFTP/SSH）](#遠端檔案傳輸sftpssh)
- [常見問題](#常見問題)
- [參考資料](#參考資料)

---

## 簡介與定位

Yazi 是以 Rust 實作的終端檔案管理器，重點在高效瀏覽、預覽與鍵盤操作。

在開發工作流中，Yazi 適合負責：

- 快速瀏覽專案目錄與檔案
- 搭配預覽器快速確認內容
- 在終端內完成移動、複製、重命名等檔案操作

---

## 安裝方式（多平台）

### macOS

```bash
brew install yazi ffmpeg sevenzip jq poppler fd ripgrep fzf zoxide resvg imagemagick
```

### Windows

```powershell
# WinGet
winget install sxyazi.yazi

# Scoop
scoop install yazi
```

### Linux

```bash
# Arch
sudo pacman -S yazi ffmpeg 7zip jq poppler fd ripgrep fzf zoxide resvg imagemagick

# Debian / Ubuntu（依官方說明，部分版本建議使用官方 binaries 或自行編譯）
sudo apt install ffmpeg 7zip jq poppler-utils fd-find ripgrep fzf zoxide imagemagick

# Fedora（COPR）
sudo dnf copr enable lihaohong/yazi
sudo dnf install yazi
```

### 手動下載官方 binary（一條龍指令，適合 apt 套件過舊）

Linux / macOS（自動抓最新版 + 自動判斷架構）：

系統級安裝（需要 `sudo`，安裝到 `/usr/local/bin`）：

```bash
YAZI_TAG="$(curl -fsSL https://api.github.com/repos/sxyazi/yazi/releases/latest | sed -n 's/.*"tag_name": "\([^"]*\)".*/\1/p')" && case "$(uname -s)-$(uname -m)" in Linux-x86_64) ASSET="yazi-x86_64-unknown-linux-gnu.zip";; Linux-aarch64|Linux-arm64) ASSET="yazi-aarch64-unknown-linux-gnu.zip";; Darwin-x86_64) ASSET="yazi-x86_64-apple-darwin.zip";; Darwin-arm64|Darwin-aarch64) ASSET="yazi-aarch64-apple-darwin.zip";; *) echo "Unsupported platform: $(uname -s)-$(uname -m)"; exit 1;; esac && TMP_DIR="$(mktemp -d)" && curl -fL -o "$TMP_DIR/yazi.zip" "https://github.com/sxyazi/yazi/releases/download/${YAZI_TAG}/${ASSET}" && unzip -oq "$TMP_DIR/yazi.zip" -d "$TMP_DIR" && YAZI_BIN="$(find "$TMP_DIR" -type f -name yazi -print -quit)" && YA_BIN="$(find "$TMP_DIR" -type f -name ya -print -quit)" && [ -n "$YAZI_BIN" ] && [ -n "$YA_BIN" ] && sudo install "$YAZI_BIN" "$YA_BIN" -t /usr/local/bin && yazi --version && rm -rf "$TMP_DIR"
```

使用者層安裝（無 `sudo`，推薦給一般使用者，安裝到 `~/.local/bin`）：

```bash
YAZI_TAG="$(curl -fsSL https://api.github.com/repos/sxyazi/yazi/releases/latest | sed -n 's/.*"tag_name": "\([^"]*\)".*/\1/p')" && case "$(uname -s)-$(uname -m)" in Linux-x86_64) ASSET="yazi-x86_64-unknown-linux-gnu.zip";; Linux-aarch64|Linux-arm64) ASSET="yazi-aarch64-unknown-linux-gnu.zip";; Darwin-x86_64) ASSET="yazi-x86_64-apple-darwin.zip";; Darwin-arm64|Darwin-aarch64) ASSET="yazi-aarch64-apple-darwin.zip";; *) echo "Unsupported platform: $(uname -s)-$(uname -m)"; exit 1;; esac && TMP_DIR="$(mktemp -d)" && curl -fL -o "$TMP_DIR/yazi.zip" "https://github.com/sxyazi/yazi/releases/download/${YAZI_TAG}/${ASSET}" && unzip -oq "$TMP_DIR/yazi.zip" -d "$TMP_DIR" && YAZI_BIN="$(find "$TMP_DIR" -type f -name yazi -print -quit)" && YA_BIN="$(find "$TMP_DIR" -type f -name ya -print -quit)" && [ -n "$YAZI_BIN" ] && [ -n "$YA_BIN" ] && mkdir -p "$HOME/.local/bin" && install "$YAZI_BIN" "$YA_BIN" -t "$HOME/.local/bin" && "$HOME/.local/bin/yazi" --version && rm -rf "$TMP_DIR"
```

若你的 shell 還沒把 `~/.local/bin` 放進 PATH，可加入：

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
# zsh 使用者改寫到 ~/.zshrc
```

這兩版都會自動在解壓後目錄遞迴找 `yazi` 與 `ya`，可避免 zip 內含子目錄時安裝失敗。

Windows（PowerShell，一條龍）：

```powershell
$tag=(Invoke-RestMethod https://api.github.com/repos/sxyazi/yazi/releases/latest).tag_name; $asset=if($env:PROCESSOR_ARCHITECTURE -eq 'ARM64'){'yazi-aarch64-pc-windows-msvc.zip'}else{'yazi-x86_64-pc-windows-msvc.zip'}; $zip="$env:TEMP\$asset"; $dst="$env:TEMP\yazi-bin"; Remove-Item $dst -Recurse -Force -ErrorAction SilentlyContinue; Invoke-WebRequest -Uri "https://github.com/sxyazi/yazi/releases/download/$tag/$asset" -OutFile $zip; Expand-Archive $zip $dst -Force; New-Item -ItemType Directory -Force "$env:ProgramFiles\yazi" | Out-Null; Copy-Item (Get-ChildItem -Path $dst -Recurse -Filter yazi.exe | Select-Object -First 1).FullName "$env:ProgramFiles\yazi\yazi.exe" -Force; Copy-Item (Get-ChildItem -Path $dst -Recurse -Filter ya.exe | Select-Object -First 1).FullName "$env:ProgramFiles\yazi\ya.exe" -Force; & "$env:ProgramFiles\yazi\yazi.exe" --version
```

執行後若 `yazi` 指令仍找不到，請把安裝目錄加入 PATH：

- Linux / macOS：`/usr/local/bin`
- Windows：`%ProgramFiles%\yazi`

---

## 必要與選配依賴

必要依賴：

- `file`（用於檔案類型判斷）

常用選配：

- `ffmpeg`（影片縮圖）
- `7zip`（壓縮檔處理）
- `jq`（JSON 預覽）
- `poppler`（PDF 預覽）
- `fd` / `ripgrep`（搜尋）
- `fzf` / `zoxide`（快速跳轉）

Windows 額外注意：

- 建議安裝 Git for Windows，並設定 `YAZI_FILE_ONE` 指向 `file.exe`。

---

## 設定檔路徑與初始化

Yazi 主要設定檔：

- `yazi.toml`（一般設定）
- `keymap.toml`（按鍵設定）
- `theme.toml`（主題設定）

預設路徑：

| 平台 | 路徑 |
|------|------|
| Linux / macOS | `~/.config/yazi/` |
| Windows | `%AppData%\yazi\config\` |

可用環境變數覆寫設定目錄：

```bash
YAZI_CONFIG_HOME=~/.config/yazi-alt yazi
```

---

## 快速開始

### 1) 啟動

```bash
yazi
```

### 2) 建議使用 shell wrapper（離開後同步 cwd）

以 Bash/Zsh 為例：

```bash
function y() {
  local tmp="$(mktemp -t "yazi-cwd.XXXXXX")" cwd
  yazi "$@" --cwd-file="$tmp"
  IFS= read -r -d '' cwd < "$tmp"
  [ -n "$cwd" ] && [ "$cwd" != "$PWD" ] && [ -d "$cwd" ] && cd -- "$cwd"
  rm -f -- "$tmp"
}
```

之後可用 `y` 取代 `yazi`。

---

## 常用操作

- `q`: 離開
- `h` `j` `k` `l`: 方向移動（Vim 風格）
- `Space`: 選取/取消選取
- `Enter`: 開啟檔案或進入目錄
- `y` / `x` / `p`: 複製 / 剪下 / 貼上
- `a`: 建立檔案或目錄
- `r`: 重命名
- `.`: 顯示或隱藏檔案
- `/`、`?`: 搜尋
- `s` / `S`: 使用 `fd` 或 `ripgrep` 搜尋

---

## 實用整合

### 與 zellij

- 建議固定一個 pane/tab 跑 Yazi，作為檔案入口。
- 另一個 pane 放 Claude Code / OpenCode，方便快速切換「找檔 → 編輯 → 測試」。

### 與編輯器

- 可將 Yazi 當作「檔案導覽層」，在終端中定位檔案後交給 VS Code 或 CLI 編輯工具。

### 套件管理（ya）

```bash
ya pkg add yazi-rs/plugins:git
ya pkg list
ya pkg upgrade
```

---

## 遠端檔案傳輸（SFTP/SSH）

如果你平常就是走 SSH，Yazi 可用外掛補上遠端檔案工作流。

### 方案 A：`sshfs.yazi`（SFTP/SSH 優先推薦）

適用情境：

- 你已經有 `~/.ssh/config`
- 想把遠端目錄掛載後，像本地檔案一樣操作

安裝需求：

- Linux/macOS
- 系統需有 `sshfs`

安裝與設定：

```bash
ya pkg add uhs-robert/sshfs
```

`~/.config/yazi/init.lua`：

```lua
require("sshfs"):setup()
```

`~/.config/yazi/keymap.toml`（建議最小鍵位）：

```toml
[mgr]
prepend_keymap = [
  { on = ["M", "s"], run = "plugin sshfs -- menu", desc = "Open SSHFS menu" },
]
```

使用方式：

- `M s` 開啟 SSHFS 功能選單
- 常用動作：mount + jump、unmount、jump to mount、add/remove host

### 方案 B：`gvfs.yazi`（Linux 多協定掛載，含 SFTP）

適用情境：

- Linux 桌面環境，想要同時處理 SFTP/SMB/NFS/FTP 等協定

安裝需求（Linux）：

- `gvfs` + `glib`，且有 DBus Session
- 依需求安裝協定 backend（例如 `gvfs-backends`）

安裝與設定：

```bash
ya pkg add boydaihungst/gvfs
```

`~/.config/yazi/init.lua`：

```lua
require("gvfs"):setup()
```

`~/.config/yazi/keymap.toml`（建議最小鍵位）：

```toml
[mgr]
prepend_keymap = [
  { on = ["M", "m"], run = "plugin gvfs -- select-then-mount --jump", desc = "Mount and jump" },
  { on = ["M", "u"], run = "plugin gvfs -- select-then-unmount", desc = "Unmount" },
  { on = ["M", "a"], run = "plugin gvfs -- add-mount", desc = "Add SFTP/SMB/FTP URI" },
  { on = ["g", "m"], run = "plugin gvfs -- jump-to-device", desc = "Jump to mounted device" },
]
```

使用方式（以 SFTP 為例）：

1. `M a` 新增 mount URI（例如 `sftp://user@host/home/user`）
2. `M m` 選擇並掛載，掛載後自動跳轉
3. 完成後 `M u` 卸載

選型建議：

- 日常 SSH/SFTP：優先 `sshfs.yazi`
- 多協定整合：使用 `gvfs.yazi`

---

## 常見問題

### 預覽異常或功能缺失

- 先檢查依賴版本是否過舊（`ffmpeg`, `ripgrep`, `fd` 等）。

### Windows 無法正確判斷類型

- 檢查 `YAZI_FILE_ONE` 是否正確指向 Git for Windows 的 `file.exe`。

### 設定沒有生效

- 確認實際使用的設定目錄（是否設定了 `YAZI_CONFIG_HOME`）。

---

## 參考資料

- 官方文件（Installation）：https://yazi-rs.github.io/docs/installation
- 官方文件（Quick Start）：https://yazi-rs.github.io/docs/quick-start
- 官方文件（Configuration）：https://yazi-rs.github.io/docs/configuration/overview
- 官方文件（Resources/Plugins）：https://yazi-rs.github.io/docs/resources
- sshfs.yazi README：https://github.com/uhs-robert/sshfs.yazi
- gvfs.yazi README：https://github.com/boydaihungst/gvfs.yazi
- GitHub Releases：https://github.com/sxyazi/yazi/releases

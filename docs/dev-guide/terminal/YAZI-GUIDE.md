# Yazi 終端檔案管理器完整指南

## 目錄

- [簡介與定位](#簡介與定位)
- [安裝方式（多平台）](#安裝方式多平台)
- [必要與選配依賴](#必要與選配依賴)
- [設定檔路徑與初始化](#設定檔路徑與初始化)
- [快速開始](#快速開始)
- [常用操作](#常用操作)
- [實用整合](#實用整合)
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
- GitHub Releases：https://github.com/sxyazi/yazi/releases

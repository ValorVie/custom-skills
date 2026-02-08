## 1. 安裝流程實作

- [x] 1.1 在 ai-dev install 增加 OpenCode superpowers 路徑初始化（mkdir、git clone/pull）。
- [x] 1.2 在 ai-dev update 增加 OpenCode superpowers 更新邏輯（git pull fallback clone）。

## 2. Symlink 與驗證

- [x] 2.1 建立/刷新 plugin 與 skills symlink（含清理既有檔案/目錄）並確保父目錄存在。
- [x] 2.2 在指令輸出中加入驗證提示（ls -l 路徑）。

## 3. 相容與文檔

- [x] 3.1 保留 `~/.config/superpowers` 追蹤流程，避免安裝程式觸碰該路徑。
- [x] 3.2 視需要更新 docs/ 或命令說明，描述 OpenCode 安裝流程與限制。

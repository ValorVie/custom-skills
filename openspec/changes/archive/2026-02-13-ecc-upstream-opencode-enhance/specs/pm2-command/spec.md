# pm2-command Specification

## ADDED Requirements

### Requirement: pm2 命令存在

系統 SHALL 在 `commands/claude/pm2.md` 和 `commands/opencode/pm2.md` 提供 PM2 服務管理命令。

#### Scenario: 命令檔案存在
- **WHEN** 檢查命令目錄
- **THEN** `commands/claude/pm2.md` SHALL 存在
- **THEN** `commands/opencode/pm2.md` SHALL 存在

### Requirement: 專案結構自動偵測

pm2 命令 SHALL 自動分析專案結構，偵測可啟動的服務。

#### Scenario: 偵測 Node.js 服務
- **WHEN** 專案包含 `package.json` 且定義了 `scripts.dev` 或 `scripts.start`
- **THEN** 系統 SHALL 識別該服務並偵測框架類型（Vite / Next.js / Express 等）
- **THEN** 系統 SHALL 從 config 或 `.env` 中偵測埠號

#### Scenario: 偵測 Python 服務
- **WHEN** 專案包含 `manage.py`（Django）或 `main.py`（FastAPI）
- **THEN** 系統 SHALL 識別該服務並偵測框架類型
- **THEN** 系統 SHALL 生成對應的啟動命令

#### Scenario: 偵測 monorepo 結構
- **WHEN** 專案包含多個子目錄各有獨立的 `package.json`
- **THEN** 系統 SHALL 識別所有可啟動的服務
- **THEN** 系統 SHALL 為每個服務生成獨立的 PM2 配置

### Requirement: PM2 配置生成

pm2 命令 SHALL 生成 `ecosystem.config.cjs` 檔案。

#### Scenario: 配置檔案內容
- **WHEN** 系統完成服務偵測
- **THEN** 系統 SHALL 生成 `ecosystem.config.cjs` 包含所有服務的配置
- **THEN** 每個服務配置 SHALL 包含：name、script、cwd、env（含 PORT）
- **THEN** 配置 SHALL 可直接被 `pm2 start ecosystem.config.cjs` 使用

### Requirement: 個別服務命令生成

pm2 命令 SHALL 為每個偵測到的服務生成獨立的啟動/停止命令。

#### Scenario: 服務命令輸出
- **WHEN** 系統完成配置生成
- **THEN** 系統 SHALL 輸出每個服務的 pm2 start / stop / restart / logs 命令
- **THEN** 系統 SHALL 輸出全體服務的 pm2 start-all / stop-all 命令

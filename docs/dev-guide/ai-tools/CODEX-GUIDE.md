# Codex 官方安裝／設定／使用指南（終端版）

> 根據 OpenAI 官方說明整合的 Codex CLI 快速上手指引。

---

## 安裝與更新

- 全域安裝：  
  ```bash
  npm install -g @openai/codex
  ```  
  官方文件主張以單行安裝即可上手。
- 升級到最新版本：  
  ```bash
  codex --upgrade
  ```
- 平台支援：macOS、Linux 正式支援；Windows 為實驗性（建議透過 WSL）。

---

## 登入與驗證

- **建議流程（無須手動複製 API Key）**  
  ```bash
  codex --login
  ```  
  選擇「Sign in with ChatGPT」即可完成登入並在本機儲存憑證。
- **API Key 模式（備用）**  
  ```bash
  export OPENAI_API_KEY="你的金鑰"
  codex
  ```  
  仍支援以 API 金鑰驅動的舊有環境。

---

## 核心操作模式

Codex 以「核准層級」控制自動化幅度：

| 模式 | 自動權限 | 適用情境 |
|------|----------|----------|
| Suggest（預設） | 讀檔，提出修補與指令但需你確認 | 安全探索、審閱 |
| Auto Edit | 讀寫檔案；指令仍需確認 | 重複性或大批量編修 |
| Full Auto | 讀寫檔案並可執行指令；在本機沙盒內 | 長流程修復／原型製作 |

切換方式：啟動時加旗標（如 `codex --auto-edit`、`codex --full-auto`），或在會話中輸入 `/mode`。

---

## 權限與沙箱（重要）

- `--sandbox <mode>`：控制檔案系統與網路沙箱，常用值：
  - `read-only`：僅讀取；任何寫入都會被阻擋。
  - `workspace-write`：允許在目前工作目錄與暫存路徑寫入（預設用於 `--full-auto`）。
  - `danger-full-access`：解除限制，可寫入全系統（請謹慎使用）。
- `--full-auto`：等同 `--sandbox workspace-write` 並將核准策略調整為低干預；仍保留基本安全提示。
- `--dangerously-bypass-approvals-and-sandbox` / `--yolo`：直接關閉核准與沙箱，全權放行（不可與 `--full-auto` 並用）。
- `--add-dir <DIR>`：在讀寫受限模式下，額外開放可寫目錄（可重複）。用法：  
  ```bash
  codex --sandbox read-only --add-dir ./src --add-dir ./tests
  ```  
  只允許 `src/`、`tests/` 寫入，其他路徑保持唯讀。

> 強制拒絕／允許路徑建議  
> - **最嚴模式**：`--sandbox read-only`，只在必要路徑加上 `--add-dir`。  
> - **完全放行**：僅在一次性、安全的隔離環境（容器、VM）內使用 `--yolo`。  
> - Codex 尚未提供逐檔案的內建黑名單；若需更細粒度限制，請利用 OS 權限、容器掛載或 read-only bind mount。

---

## 設定檔控制（像 OpenCode 的安全檔）

- 位置：`~/.config/codex/config.toml`（若不存在可自行建立）。citeturn0search6
- 你可以在此預設核准與沙箱模式，啟動時會自動套用：citeturn0search0
  ```toml
  # 預設模型（可選）
  [model]
  default = "gpt-5.2-codex"

  # 核准與沙箱預設
  approval_policy = "on-request"   # 其他值：never, untrusted, always
  sandbox_mode    = "workspace-write"  # 其他值：read-only, danger-full-access

  # 在 workspace-write 模式下是否允許網路
  [sandbox_workspace_write]
  network_access = false

  # 自訂 Profile 範例
  [profiles.readonly_strict]
  approval_policy = "never"
  sandbox_mode    = "read-only"
  ```
- 允許／拒絕路徑：目前 **沒有** 像 OpenCode 那樣的 config 允許清單／封鎖清單欄位；僅能：
  1) 用 `--add-dir` 旗標在唯讀模式下開白名單寫入目錄；  
  2) 改用 OS 層級權限或容器 bind-mount 封鎖路徑；  
  3) 在 `sandbox_mode = read-only` 下保守運行，必要時用 `--add-dir` 增量開放。citeturn0search1
- `.git`、`.codex` 等敏感目錄在 sandbox 中預設唯讀，無法透過 config 放寬；若需修改請改於容器或以 `--yolo` 在隔離環境中操作。citeturn0search1

---

## 基本使用範例

```bash
# 啟動並請 Codex 說明目前專案
codex "Explain this repo"

# 以 Auto Edit 模式進行重構
codex --auto-edit "Refactor the logging module for clarity"

# 切換模型（可選）
codex -m gpt-5.1-codex-max "Add integration tests for auth flow"
```

---

## 更新與故障排除

- 更新版本：`codex --upgrade`。
- 若登入狀態異常，可重跑 `codex --login` 重新綁定帳號。
- 若命令卡住，可用 `Ctrl+C` 中斷並重新下指令；確保網路穩定。

---

## 常見問答（官方摘要）

- **使用的模型**：預設採 GPT‑5 系列，可用 `-m` 指定其他 Responses API 模型。  
- **程式碼是否上傳？** 讀寫與指令執行皆在本機，只有提示等高階上下文會送至模型。  
- **支援哪些 IDE／介面？** 除 CLI 外，官方亦提供 IDE 延伸與 Web／App 介面，可共用同一帳號與授權。

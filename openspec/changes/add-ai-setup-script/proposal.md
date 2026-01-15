# 提案：新增 AI 環境設定腳本

## 摘要
新增一個基於 Python 的設定與維護腳本 (`script/main.py`)，以自動化 `docs/AI開發環境設定指南.md` 中描述的 AI 開發環境設定流程。

## 動機
目前的設定流程需要手動執行許多 Shell 指令，且在 macOS/Linux 與 Windows 之間有所不同。統一的 Python 腳本將可：
- 減少手動操作錯誤。
- 提供跨平台的一致介面。
- 簡化維護工作（每日更新）。
- 確保所有開發者擁有正確的工具與配置。

## 預計變更
- 使用 Python 實作 `script/main.py`。
- 使用 `uv` 進行依賴管理。
- 支援 `install` 子指令進行首次設定。
- 支援 `maintain` 子指令進行每日更新。
- 更新 `script/README.md`，包含使用 `uv` 的操作說明。

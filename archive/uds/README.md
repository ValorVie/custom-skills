# UDS 退役封存

- 退役日期：2026-10-11
- 狀態：僅供歷史查閱，ai-dev 不再安裝、更新或呼叫 UDS
- 原功能：
  - 把 `AsiaOstrich/universal-dev-standards` clone 到 `~/.config/universal-dev-standards`。
  - 以 npm 安裝 `uds` CLI。
  - 在 `ai-dev update`、`project init`／`update` 代理執行 `uds init`／`uds update`。
  - 用 `ai-dev standards` 切換 `.standards/profiles` 的 profile。

## 為什麼移除

本 repo 的 `.standards/`、`skills/uds/` 與 UDS agents 已先後移除，第一方 skills 也改由 `ai-dev-skills` 以 npx 管理。剩下的整合，只是在每次 install／update 時拉取一個沒有地方使用的 repo，並替專案執行一個 ai-dev 不再維護的工具。

## 既有專案

- ai-dev 不刪除、也不修改任何專案的 `.standards/`，專案規則檔引用的檔案仍然存在。
- 專案留有 `.standards/` 時，`ai-dev update` 與 `project update` 只顯示一段說明。只靠 UDS 的專案，`project update` 仍以 0 結束。
- 需要更新 `.standards/` 時，可直接執行已安裝的 `uds update`；不再使用時，手動刪除 `.standards/`，並移除規則檔中的引用。
- 曾用 `ai-dev standards` 停用的資源，可用 `ai-dev toggle` 重新啟用。
- `~/.config/universal-dev-standards` 與全域 npm 套件 `universal-dev-standards` 不會自動移除。

## 封存內容

| 路徑 | 內容 |
| --- | --- |
| `specs/openspec/standards-profiles/` | profile 切換規格 |
| `specs/openspec/standards-sync/` | `.standards/` 與上游同步規格 |
| `specs/openspec/tui-standards-profile/` | TUI profile 區塊規格 |

原本 `upstream/uds/` 的 UDS 備份（`.standards/` 與 skills 鏡像）已刪除，需要時從 git 歷史取回。

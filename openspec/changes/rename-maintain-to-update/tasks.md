# Tasks: rename-maintain-to-update

## 階段 1：程式碼重構

- [ ] 將 `script/commands/maintain.py` 重新命名為 `script/commands/update.py` <!-- id: 1 -->
- [ ] 在 `update.py` 中將函式名稱 `maintain()` 改為 `update()` <!-- id: 2, depends: 1 -->
- [ ] 更新 `script/main.py` 的 import 與 command 註冊 <!-- id: 3, depends: 2 -->
- [ ] 更新 `script/tui/app.py` 的按鈕標籤與 command 呼叫 <!-- id: 4, depends: 3 -->

## 階段 2：規格文件更新

- [ ] 更新 `openspec/specs/setup-script/spec.md` <!-- id: 5 -->
- [ ] 更新 `openspec/specs/cli-distribution/spec.md` <!-- id: 6 -->
- [ ] 更新 `openspec/specs/skill-npm-integration/spec.md` <!-- id: 7 -->
- [ ] 更新 `openspec/specs/documentation/spec.md` <!-- id: 8 -->

## 階段 3：文檔更新

- [ ] 更新 `README.md` <!-- id: 9 -->
- [ ] 更新 `docs/AI開發環境設定指南.md` <!-- id: 10 -->
- [ ] 更新 `CHANGELOG.md` 新增變更記錄 <!-- id: 11 -->

## 階段 4：驗證

- [ ] 執行 `ai-dev update --help` 確認指令正常 <!-- id: 12, depends: 1,2,3 -->
- [ ] 執行 `ai-dev tui` 確認 TUI 介面正常 <!-- id: 13, depends: 4 -->
- [ ] 使用 `rg maintain` 搜尋確認無遺漏 <!-- id: 14 -->
- [ ] 執行 `openspec validate rename-maintain-to-update --strict --no-interactive` 確認規格有效 <!-- id: 15 -->

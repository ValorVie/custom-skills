# Tasks: 三階段分發流程重構

## 1. 核心邏輯修改

- [x] 1.1 修改 `copy_skills()` 移除 Stage 2 呼叫
  - 檔案：`script/utils/shared.py`
  - 移除 `copy_sources_to_custom_skills()` 的呼叫
  - 保留函式本身供開發者模式使用

- [x] 1.2 新增開發者整合函式 `integrate_to_dev_project()`
  - 檔案：`script/utils/shared.py`
  - 整合外部來源到開發目錄
  - 使用現有的 `copy_sources_to_custom_skills()` 邏輯但目標改為開發目錄

## 2. Clone 指令修改

- [x] 2.1 修改 `clone` 指令邏輯
  - 檔案：`script/commands/clone.py`
  - 當 `--sync-project` 且在開發目錄時，呼叫整合函式
  - 分發仍從 `~/.config/custom-skills` 執行

- [x] 2.2 新增提示訊息
  - 當偵測到開發目錄但未使用 `--sync-project` 時提示
  - 顯示整合完成後的摘要

## 3. 程式碼清理

- [x] 3.1 更新 docstring 與註解
  - 修改 `copy_skills()` 的文件說明
  - 更新三階段流程的註解

- [x] 3.2 確認測試覆蓋
  - 驗證修改後的流程
  - 確認開發者與使用者場景皆正常

## 4. Spec 更新

- [ ] 4.1 Archive 完成後更新 `setup-script` spec
- [ ] 4.2 Archive 完成後更新 `clone-command` spec

# ai-dev 命令分類與設計壓力參考

本文件是 `ai-dev` 命令面的長期維護基線，用來描述每個命令的副作用類型、scope、target 模式與設計壓力。它不取代 [ai-dev指令與資料流參考.md](/Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills/.worktrees/maintain-command-surface/docs/ai-dev指令與資料流參考.md)；後者描述目前實作真相，本文件描述命令類型與應維持的設計判斷。

## 分類維度

- `side_effect_class`
  - `read_only`
  - `single_write`
  - `multi_stage_pipeline`
  - `system_level_operation`
- `scope`
  - `global_env`
  - `repo`
  - `project`
  - `target`
  - `external_service`
- `target_mode`
  - `none`
  - `implicit_default`
  - `explicit_single`
  - `explicit_multi`
- `design_pressure`
  - `keep`
  - `clarify`
  - `needs_scope_fix`
  - `split`

## 命令分類總表

| command_path | side_effect_class | scope | target_mode | design_pressure |
|--------------|-------------------|-------|-------------|-----------------|
| `install` | `multi_stage_pipeline + system_level_operation` | `global_env, repo, target` | `explicit_multi` | `clarify` |
| `update` | `multi_stage_pipeline + system_level_operation` | `global_env, repo` | `none` | `clarify` |
| `clone` | `multi_stage_pipeline` | `target` | `explicit_multi` | `keep` |
| `status` | `read_only` | `global_env, repo, project` | `none` | `clarify` |
| `list` | `read_only` | `target` | `implicit_default` | `needs_scope_fix` |
| `toggle` | `single_write` | `target` | `explicit_single` | `clarify` |
| `init-from` | `multi_stage_pipeline` | `repo, project` | `none` | `split` |
| `standards switch` | `single_write` | `project` | `none` | `needs_scope_fix` |
| `standards sync` | `single_write` | `target` | `explicit_single` | `needs_scope_fix` |
| `hooks install` | `single_write` | `target` | `explicit_single` | `needs_scope_fix` |
| `hooks uninstall` | `single_write` | `target` | `explicit_single` | `needs_scope_fix` |
| `hooks status` | `read_only` | `target` | `explicit_single` | `needs_scope_fix` |
| `sync init` | `multi_stage_pipeline + system_level_operation` | `repo, external_service` | `none` | `split` |
| `mem pull` | `multi_stage_pipeline` | `external_service, project` | `none` | `split` |
| `mem auto` | `system_level_operation` | `global_env` | `none` | `clarify` |

## Design Pressure 分組

### `keep`

- `clone`
  - 維持 `state -> targets` 的預設組合即可，不需再拆命令。

### `clarify`

- `install`
- `update`
- `status`
- `toggle`
- `mem auto`

共同原則：

- 補 preview / `--dry-run`
- 在 help 與文件明確揭露系統層副作用
- read-only 聚合命令應支援分區查詢

### `needs_scope_fix`

- `list`
- `standards switch`
- `standards sync`
- `hooks install`
- `hooks uninstall`
- `hooks status`

共同原則：

- read-only 命令可以隱含 `all`
- 任何寫入 target 的命令都必須顯式 `--target`
- project state 命令預設只改 project state，不再偷偷同步 target
- 名稱泛用的命令不能隱含綁單一 target

### `split`

- `init-from`
- `sync init`
- `mem pull`

共同原則：

- 將重副作用 bootstrap / update / post-process 路徑改成顯式語意
- 不能再靠隱含後續處理完成主要工作流

## 維護規則

- 修改 `ai-dev` 命令行為後，必須同時更新本文件與 [ai-dev指令與資料流參考.md](/Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills/.worktrees/maintain-command-surface/docs/ai-dev指令與資料流參考.md)。
- 若 design pressure 改變，需同步更新對應 assessment report。

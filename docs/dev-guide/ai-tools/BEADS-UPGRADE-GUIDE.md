# Beads（bd）升級指南

> 依 Beads 官方 Upgrading 文件、v1.2.2／v1.3.0／v1.3.1 release notes，以及一次 embedded 模式
> `1.2.1 → 1.3.1` 實測整理。查核日期：2026-10-06。

---

## 先看結論

這份指南給已經在用 Beads 的 repo，用來把 `bd` 升到官方最新穩定版，並安全遷移 `.beads` 的
資料庫結構。安裝與日常使用見 [Beads 指南](BEADS-GUIDE.md)。

升級前先記住四件事：

1. **從 1.3.x 起，裝上新版就可能等於套用。** embedded 模式設有 Dolt remote，而且 remote 與
   本機結構同版時，新版第一次開啟資料庫就會自動遷移。備份、基線與 push 都要在安裝前用
   舊版完成。
2. **先在 `.beads` 完整副本演練。** 現行資料庫沒有可靠的遷移預覽，`bd migrate --dry-run`
   只顯示版本 metadata。
3. **共用同一個 Dolt remote 的多個 clone，只能有一個遷移者。** 其他 clone 裝同一版後用
   `bd bootstrap` 採用遷移後的資料庫，不各自遷移。
4. **不要從 1.2.1 退到 1.2.2。** 1.2.0 與 1.2.1 已被上游撤回，從 1.2.1 只能往前升到 1.3.x。

## 一、判斷你的升級情境

先在 repo 根目錄用目前的 `bd` 收集資訊：

```bash
bd version
type -a bd
bd where
bd dolt status
bd dolt remote list
bd config get dolt.auto-push
git config --get core.hooksPath
bd hooks list
bd setup claude --check
bd setup codex --check
```

各項要回答的問題：

| 項目 | 看什麼 | 影響 |
| --- | --- | --- |
| 版本 | `bd version` | 決定要跨哪些遷移、是否碰到撤回版本 |
| 實際執行檔 | `type -a bd` 的第一個；若是 wrapper，再找它呼叫的檔案 | 決定替換目標與回復方式 |
| 安裝方式 | Homebrew、npm、官方腳本或手動放置的二進位檔 | 決定安裝命令與能否釘選版本 |
| 儲存模式 | `bd dolt status` 顯示 embedded、server 或 proxied | server 類模式不會自動遷移，流程不同 |
| remote | `bd dolt remote list` 有沒有輸出 | 有 remote 時受遷移閘門管制，遷移後要 push |
| 共用者 | 自行清點：其他電腦、clone、CI、cron、長駐 `bd serve` | 多個共用者時要凍結並指定遷移者 |
| hooks 位置 | `core.hooksPath` 與 `bd hooks list` | 更新 hooks 時要裝回同一個位置 |
| 代理整合 | `bd setup <recipe> --check` | 升級後可能顯示 stale，需要重裝 |

上游無法偵測其他電腦或 clone 的版本，共用者必須自己清點。

依結果選流程：

| 情境 | 流程 |
| --- | --- |
| embedded、沒有 remote | 第三節到第六節；略過所有 push 步驟 |
| embedded、有 remote、只有這一個 clone | 第三節到第六節；安裝前用舊版 `bd dolt push`，遷移後再 push |
| 有 remote、多個 clone | 全部 clone 先用舊版同步並凍結；只有一個 clone 跑第三節到第六節；其他 clone 依 5.4 採用 |
| server、shared server 或 proxied | 依第七節，先升級所有 client 再一次同意遷移 |

## 二、確認目標版本

### 2.1 查官方最新穩定版

```bash
curl -fsSL https://api.github.com/repos/gastownhall/beads/releases/latest \
  | jq -r 'select(.draft == false and .prerelease == false) | .tag_name'
```

不要用 `-rc` 等預覽版。目前版本高於 GitHub latest 時，停止並查清來源，不要自動降級。

用 Homebrew 安裝時，先執行 `brew info beads`。formula 的版本可能晚於 GitHub latest，目標版本
以實際能安裝的版本為準，避免演練的版本與最後裝上的不同。

### 2.2 撤回版本與已知版本線

| 版本 | 狀態 | 要注意什麼 |
| --- | --- | --- |
| v1.2.0、v1.2.1 | 2026-08-11 誤發，已撤回 | 執行過 1.2.1 的資料庫結構是 v65 |
| v1.2.2 | 復原版，內容是 v1.1.2 程式碼 | 只認得 v53；開啟 v65 資料庫會停在 `schema version mismatch` |
| v1.3.0 | 第一個測試過的 1.3 版 | 1.1.x／1.2.2 的 v53 一次升到 v66，約 28 支遷移 |
| v1.3.1 | 1.3 的修補版 | 相對 v1.3.0 沒有結構遷移，但有影響腳本的行為變更 |

用過 1.2.1 的 repo 直接升到 1.3.x。上游另有把結構紀錄撥回 v53 的
[復原程序](https://beads.gascity.com/recovery/accidental-1-2-1-release)，那是給要改用
1.2.2 或 1.1.x 的人用的。

v1.3.0 從 v53 升級時，終端機上的遷移計數會跑到 0066 後又從 0012 重新開始。後半段是
clone-local（只留在本機、不同步到 remote 的表）的遷移，不是迴圈，不要中斷。輸出不是
終端機時不會顯示進度。

### 2.3 讀目標版的 Upgrading Notes

每個 release 的 Upgrading Notes 都列出會改變腳本行為的項目。v1.3.x 常見的影響：

- `bd search` 預設包含已關閉的 issue；只要 open 時加 `--status open`。
- `bd close` 一次關多個 ID，任一失敗就回傳非零。
- `BEADS_DIR` 必須指向 `.beads` 目錄本身，不能指向專案根目錄。
- `bd dolt push` 不再默默採用由 git origin 推導的 Dolt remote；非互動環境會直接失敗。CI 或
  cron 依賴舊行為時要先調整。
- `bd --readonly serve` 會被拒絕；長駐服務若帶這個參數，升級後起不來。
- 過期的 `defer_until` 會回到 `bd ready`；自訂的 active 類 status 也會列入 ready。

## 三、比對兩版的遷移檔

這一步判斷能不能直接升級。目標版若改寫了目前版本已套用過的遷移檔，直接升級會讓本機與
remote 對同一號遷移套用不同內容，上游稱為 content skew。

```bash
BEADS_CURRENT_TAG=v1.2.1   # 改成你的目前版本
BEADS_TARGET_TAG=v1.3.1    # 改成目標版本
BEADS_WORK=$(mktemp -d)

for BEADS_TAG in "$BEADS_CURRENT_TAG" "$BEADS_TARGET_TAG"; do
  curl -fsSL \
    "https://api.github.com/repos/gastownhall/beads/git/trees/$BEADS_TAG?recursive=1" \
    -o "$BEADS_WORK/tree-$BEADS_TAG.json"
  jq -e '.truncated == false' "$BEADS_WORK/tree-$BEADS_TAG.json" >/dev/null
  jq -r '.tree[] | select(.type == "blob")
      | select(.path | startswith("internal/storage/schema/migrations/"))
      | "\(.sha) \(.path)"' "$BEADS_WORK/tree-$BEADS_TAG.json" \
    | sort -k2 > "$BEADS_WORK/migrations-$BEADS_TAG.txt"
done

diff "$BEADS_WORK/migrations-$BEADS_CURRENT_TAG.txt" \
  "$BEADS_WORK/migrations-$BEADS_TARGET_TAG.txt"
```

本節在登入 shell 執行，沒有 strict mode。任何命令報錯（例如 `jq -e` 回傳非零或下載失敗）
就停止，不要依不完整的檔案判讀結果。

判讀方式：

- 只有 `>` 開頭的行：目標版只新增遷移，可以直接升級。
- 出現 `<` 開頭的行：已套用的遷移被改寫或移除。停止，先讀上游 recovery 文件。

實測的 `v1.2.1 → v1.3.1` 只新增主線 `0066` 與 clone-local `0025`、`0026`，其餘遷移檔的
git blob 雜湊完全相同。

## 四、安裝前：用舊版準備

### 4.1 開一個專用子 shell

需要的工具：`git`、`curl`、`jq`、`tar`、`pgrep`、`sha256sum` 或 macOS 的 `shasum`，以及
`lsof`（Linux 沒有時改用 `/proc`）。

以下命令在同一個子 shell 依序執行。不要在登入 shell 開 strict mode，命令失敗時會直接關掉
整個登入 shell。

```bash
bash --noprofile --norc
```

先定義設定與函式。這一段可以重跑：

```bash
set -euo pipefail

BEADS_TARGET_TAG=v1.3.1   # 與第三節相同；子 shell 不會繼承登入 shell 的變數
BEADS_REPO=$(git rev-parse --show-toplevel)
cd "$BEADS_REPO"

# 實際執行檔。若 PATH 第一個 bd 是 wrapper，改成 wrapper 呼叫的檔案。
BEADS_BIN=$(readlink -f "$(command -v bd)")
BEADS_BACKUP_PARENT="${XDG_DATA_HOME:-$HOME/.local/share}/beads-upgrade-backups"

beads_sha256() {
  if command -v sha256sum >/dev/null; then sha256sum "$@"; else shasum -a 256 "$@"; fi
}

# 先把輸出存進變數再判斷。直接接 grep -q 時，pipefail 會因權限錯誤或 SIGPIPE
# 把「有檔案開著」誤判成「沒有」。
beads_assert_idle() {
  local open_files=""
  if pgrep -x bd >/dev/null; then
    printf '偵測到其他 bd 程序，停止\n' >&2
    pgrep -l -x bd >&2
    return 1
  fi
  if command -v lsof >/dev/null; then
    open_files=$(lsof +D "$BEADS_REPO/.beads" 2>/dev/null || true)
  elif [[ -d /proc ]]; then
    # 只看得到目前使用者可讀的程序；bd 以其他帳號執行時改用 sudo 或 lsof。
    open_files=$(find /proc/[0-9]*/fd -maxdepth 1 \
      -lname "$BEADS_REPO/.beads/*" 2>/dev/null || true)
  fi
  if [[ -n "$open_files" ]]; then
    printf '.beads 有開啟中的檔案，停止\n%s\n' "$open_files" >&2
    return 1
  fi
}
```

第一次執行時建立本次備份目錄，並把印出的路徑記下來：

```bash
install -d -m 700 "$BEADS_BACKUP_PARENT"
BEADS_BACKUP_DIR=$(mktemp -d "$BEADS_BACKUP_PARENT/backup-XXXXXXXX")
BEADS_TEST_WORKSPACE="$BEADS_BACKUP_DIR/test-workspace"
BEADS_CANDIDATE="$BEADS_BACKUP_DIR/candidate/bd"
printf 'backup=%s\n' "$BEADS_BACKUP_DIR"
```

子 shell 因檢查失敗而結束時，重開子 shell、重跑上面的設定段，然後用下面這段接回原本的
備份目錄，不要再建一個新的：

```bash
BEADS_BACKUP_DIR='<上面印出的 backup 路徑>'
test -d "$BEADS_BACKUP_DIR"
BEADS_TEST_WORKSPACE="$BEADS_BACKUP_DIR/test-workspace"
BEADS_CANDIDATE="$BEADS_BACKUP_DIR/candidate/bd"
```

macOS 12.3 以前的 `readlink` 沒有 `-f`，這時把 `type -a bd` 顯示的實際檔案路徑直接填進
`BEADS_BIN`。接回後從失敗的那一步重新開始，已完成的基線、備份與下載不必重做。

### 4.2 暫停其他使用者並同步

升級期間暫停其他代理工作階段、手動 bd 操作、CI 與 cron。Claude Code 或 Codex 的
SessionStart hook、Git hooks 都會呼叫 bd，裝上新版後任何一次呼叫都可能觸發遷移。

有 remote 時，用舊版同步：

```bash
bd dolt push
```

多個 clone 共用 remote 時，每個 clone 都要用舊版完成 `bd dolt push` 與 `bd dolt pull`，
然後停止寫入，直到遷移者發布完成。指定一個 clone 當遷移者；其他 clone 做完這裡的同步後，
跳到 5.4 的「其他 clone」步驟，等遷移者通知已發布再繼續。

### 4.3 固定基線

```bash
beads_assert_idle

bd version | tee "$BEADS_BACKUP_DIR/version-before.txt"
bd status --json > "$BEADS_BACKUP_DIR/status-before.json"
bd ready --json --limit 0 > "$BEADS_BACKUP_DIR/ready-before.json"
jq -r '.[].id' "$BEADS_BACKUP_DIR/ready-before.json" | sort | beads_sha256 \
  | tee "$BEADS_BACKUP_DIR/ready-before.sha256"
bd list --all --json --limit 0 | jq -r '.[] | [.id, .status] | @tsv' \
  | sort > "$BEADS_BACKUP_DIR/id-status-before.tsv"
bd memories > "$BEADS_BACKUP_DIR/memories-before.txt"
bd hooks list > "$BEADS_BACKUP_DIR/hooks-before.txt"
```

注意事項：

- 用 Beads 追蹤這次升級時，先認領任務再取基線；認領會改變 in-progress 數量。
- `bd ready` 預設只列部分結果，一律加 `--limit 0`。
- `bd status` 的 `ready_issues` 與 `bd ready` 的筆數算法不同，只拿同一個命令前後互比。
- `bd memories` 先存檔再讀。在 `pipefail` 下直接接 `| head`，上游收到 SIGPIPE 會回傳
  141，讓子 shell 結束。

### 4.4 用舊版備份

```bash
beads_assert_idle

bd export --all -o "$BEADS_BACKUP_DIR/issues-before.jsonl"
test -s "$BEADS_BACKUP_DIR/issues-before.jsonl"

cp -a "$BEADS_BIN" "$BEADS_BACKUP_DIR/bd-old"
cp -a .beads "$BEADS_BACKUP_DIR/beads-before"
diff -qr .beads "$BEADS_BACKUP_DIR/beads-before"

install -d -m 700 "$BEADS_TEST_WORKSPACE"
cp -a .beads "$BEADS_TEST_WORKSPACE/.beads"
```

`bd export --all` 包含 issue 與 memories，可跨版本匯入，但不含 Dolt history 與設定，不能
取代資料庫備份。新版的 `bd export` 會先遷移再匯出，所以這一步一定要在安裝前做。需要保留
history 的 Dolt 原生備份時，另用 `bd backup init <path>` 與 `bd backup sync`。

從備份完成到安裝新版之間，不要再對 Beads 寫入。

## 五、演練、安裝與驗證

### 5.1 在副本演練

先下載與目標版相同的官方 release 檔並核對 checksum。不論最後用哪種方式安裝，演練都用這個
檔案。

```bash
BEADS_VERSION=${BEADS_TARGET_TAG#v}
BEADS_OS=$(uname -s | tr '[:upper:]' '[:lower:]')   # linux、darwin 或 freebsd
case "$(uname -m)" in
  x86_64|amd64) BEADS_ARCH=amd64 ;;
  aarch64|arm64) BEADS_ARCH=arm64 ;;
  *) printf '不支援的架構\n' >&2; exit 1 ;;
esac
BEADS_ARCHIVE="beads_${BEADS_VERSION}_${BEADS_OS}_${BEADS_ARCH}.tar.gz"
BEADS_URL="https://github.com/gastownhall/beads/releases/download/$BEADS_TARGET_TAG"

install -d -m 700 "$BEADS_BACKUP_DIR/candidate"
curl -fsSL "$BEADS_URL/$BEADS_ARCHIVE" -o "$BEADS_BACKUP_DIR/$BEADS_ARCHIVE"
curl -fsSL "$BEADS_URL/checksums.txt" -o "$BEADS_BACKUP_DIR/checksums.txt"
(cd "$BEADS_BACKUP_DIR" && grep " $BEADS_ARCHIVE\$" checksums.txt | beads_sha256 -c -)
tar -xzf "$BEADS_BACKUP_DIR/$BEADS_ARCHIVE" -C "$BEADS_BACKUP_DIR/candidate" bd
```

副本保留了原本的 remote 設定。遷移前先用舊版確認 `dolt.auto-push` 未開啟（1.3.1 預設
`false`），演練期間也不要執行任何 push：

```bash
"$BEADS_BACKUP_DIR/bd-old" -C "$BEADS_TEST_WORKSPACE" config get dolt.auto-push
```

候選版會從目前目錄往上找 `.beads`。在 repo 目錄裡執行候選版，它找到的就是現行資料庫；
會開庫的命令會直接用新版遷移現行庫。因此演練命令都先切到副本目錄，並加 `-C`：

```bash
cd "$BEADS_TEST_WORKSPACE"

diff <(jq -S . "$BEADS_BACKUP_DIR/status-before.json") \
  <("$BEADS_BACKUP_DIR/bd-old" -C "$BEADS_TEST_WORKSPACE" status --json | jq -S .)

"$BEADS_CANDIDATE" -C "$BEADS_TEST_WORKSPACE" where
"$BEADS_CANDIDATE" -C "$BEADS_TEST_WORKSPACE" migrate --dry-run
"$BEADS_CANDIDATE" -C "$BEADS_TEST_WORKSPACE" migrate --yes
"$BEADS_CANDIDATE" -C "$BEADS_TEST_WORKSPACE" migrate schema --json
```

`where` 必須指向副本。`migrate schema --json` 應回報目標版的結構版本，例如 1.3.1 是
`✓ Schema already at v66`。

有 remote 時，遷移閘門（smart gate）會先看 remote 快取的結構狀態再決定：

| 閘門結果 | 意思 | 處理 |
| --- | --- | --- |
| `auto-applying … remote at same version — safe first-mover` | remote 與本機同版，本 clone 是第一個遷移者 | 正常，繼續比對 |
| 要求指定遷移者確認（`--force` 或 `BD_ALLOW_REMOTE_MIGRATE=1`） | remote 快取狀態讀不到或版本不同 | 只有本 clone 確定是唯一遷移者時，副本改用 `migrate --force --yes` 重跑並完成比對 |
| 要求先 `bd dolt pull` | 本機資料落後 remote | 停止。不要加 `--force`；回到 4.2 用舊版同步 |
| 要求 `bd bootstrap`，或回報 fork、content skew | remote 已被其他 clone 遷移，或兩邊同一號遷移內容不同 | 停止。前者依 5.4 採用；後者依上游 recovery 文件處理 |

接著比對副本與基線：

```bash
diff <(jq -S . "$BEADS_BACKUP_DIR/status-before.json") \
  <("$BEADS_CANDIDATE" -C "$BEADS_TEST_WORKSPACE" status --json | jq -S .)
"$BEADS_CANDIDATE" -C "$BEADS_TEST_WORKSPACE" ready --json --limit 0 \
  | jq -r '.[].id' | sort | beads_sha256 \
  | diff - "$BEADS_BACKUP_DIR/ready-before.sha256"
"$BEADS_CANDIDATE" -C "$BEADS_TEST_WORKSPACE" list --all --json --limit 0 \
  | jq -r '.[] | [.id, .status] | @tsv' | sort \
  | diff "$BEADS_BACKUP_DIR/id-status-before.tsv" -
"$BEADS_CANDIDATE" -C "$BEADS_TEST_WORKSPACE" memories \
  > "$BEADS_BACKUP_DIR/memories-test.txt"
diff <(head -n 1 "$BEADS_BACKUP_DIR/memories-before.txt") \
  <(head -n 1 "$BEADS_BACKUP_DIR/memories-test.txt")
"$BEADS_CANDIDATE" -C "$BEADS_TEST_WORKSPACE" ping
```

任何 `diff` 有輸出時，`set -e` 會結束子 shell，這就是停止點。差異已印在畫面上；依 4.1
接回備份目錄後逐筆檢查。2.3 列的 ready 行為變更可能讓 ready 變多；無法對應到文件記載的
變更時，不要安裝新版。

1.3.1 的 `bd doctor` 仍不支援 embedded 模式，只印出說明。embedded 模式改跑它支援的檢查：

```bash
for BEADS_CHECK in artifacts conventions pollution; do
  "$BEADS_CANDIDATE" -C "$BEADS_TEST_WORKSPACE" doctor --check="$BEADS_CHECK"
done
```

content skew 沒有 doctor 可查時，證據是兩項：閘門沒有因 fork 阻擋，以及第三節的遷移檔比對
只有新增。

副本出現以下任一情況就停止，不安裝新版：`where` 指到現行庫、遷移錯誤、lock、
`schema version mismatch`、閘門要求停止、比對結果無法解釋。

### 5.2 安裝新版並立即遷移

回到 repo，確認現行庫仍是備份時的狀態：

```bash
cd "$BEADS_REPO"
beads_assert_idle
diff -qr .beads "$BEADS_BACKUP_DIR/beads-before"
```

`diff -qr` 有輸出代表備份後又有寫入，回到 4.4 重做備份。

依安裝方式安裝與副本相同的版本：

| 安裝方式 | 命令 | 說明 |
| --- | --- | --- |
| 手動二進位檔 | 見下方原子替換 | 用演練過的同一個檔案 |
| npm | `npm install -g @beads/bd@<版本>` | 釘選版本，不用 `npm update` |
| Homebrew | `brew upgrade beads` | 只能裝 formula 目前的版本；先用 `brew info beads` 確認等於演練版本，裝完再核對 |
| 官方安裝腳本 | 重跑 `scripts/install.sh` | 只裝最新版；先確認 2.1 查到的 latest 仍等於演練版本，裝完再核對 |

手動二進位檔用同目錄暫存檔加 `mv` 替換，避免執行到寫一半的檔案：

```bash
BEADS_TMP="$BEADS_BIN.upgrade.new"
test ! -e "$BEADS_TMP"
install -m 755 "$BEADS_CANDIDATE" "$BEADS_TMP"
mv "$BEADS_TMP" "$BEADS_BIN"
```

裝完立刻觸發遷移，不要等其他程序先開庫：

```bash
bd version
BEADS_MIGRATE_RC=0
bd migrate --yes > "$BEADS_BACKUP_DIR/live-migrate.txt" 2>&1 || BEADS_MIGRATE_RC=$?
sleep 1
cat "$BEADS_BACKUP_DIR/live-migrate.txt"
test "$BEADS_MIGRATE_RC" -eq 0
bd migrate schema --json
```

- `bd version` 的版本號必須等於演練版本。Homebrew 或安裝腳本裝到不同版本時，停止並依第六節
  回復，或重新演練該版本。
- 副本是用 `migrate --force --yes` 通過的，這裡也照做；副本沒用過 `--force`，這裡也不加。
- 透過 wrapper 呼叫 bd，且 wrapper 用 `2> >(...)` 過濾 stderr 時，閘門訊息可能在命令結束後
  才寫入，所以先 `sleep` 再讀。判斷是否完成以 `bd migrate schema --json` 為準。

### 5.3 驗證、更新 hooks 與代理整合

```bash
diff <(jq -S . "$BEADS_BACKUP_DIR/status-before.json") <(bd status --json | jq -S .)
bd ready --json --limit 0 | jq -r '.[].id' | sort | beads_sha256 \
  | diff - "$BEADS_BACKUP_DIR/ready-before.sha256"
bd list --all --json --limit 0 | jq -r '.[] | [.id, .status] | @tsv' | sort \
  | diff "$BEADS_BACKUP_DIR/id-status-before.tsv" -
bd memories > "$BEADS_BACKUP_DIR/memories-after.txt"
diff <(head -n 1 "$BEADS_BACKUP_DIR/memories-before.txt") \
  <(head -n 1 "$BEADS_BACKUP_DIR/memories-after.txt")
bd ping
bd where
bd upgrade review
```

任何比對失敗時子 shell 會結束。差異無法用 2.3 的行為變更解釋時，依第六節回復。

`bd upgrade review` 列出舊版到新版之間的變更。沒有上一版紀錄時會顯示
`No previous version recorded`，這時改讀 release notes 或 `bd info --whats-new`。

hooks 要裝回原本的位置。先備份 active hooks 目錄，再依 `core.hooksPath` 選參數：

```bash
BEADS_HOOKS_DIR=$(git rev-parse --git-path hooks)
cp -a "$BEADS_HOOKS_DIR" "$BEADS_BACKUP_DIR/hooks-before"

case "$(git config --get core.hooksPath || true)" in
  "") bd hooks install ;;
  *.beads/hooks) bd hooks install --beads ;;
  *.beads-hooks) bd hooks install --shared ;;
  *) printf '自訂 core.hooksPath，先人工確認再安裝\n' >&2; exit 1 ;;
esac
bd hooks list
```

hook 只改 Beads marker 區塊，marker 外的內容會保留。`bd hooks list` 應顯示新版的 shim
版本。`.beads/hooks` 也包含在 4.4 的 `.beads` 備份裡。

第一節 `bd setup <recipe> --check` 有用到的代理整合，升級後再檢查一次。顯示 stale 或未
安裝時重新安裝，然後重開該工具：

```bash
bd setup claude --check
bd setup codex --check
# 顯示 stale 時：
# bd setup claude
# bd setup codex
```

### 5.4 發布與其他 clone

沒有 remote 時略過本節。

遷移者在驗證通過後發布：

```bash
bd dolt push
```

不要加 `--force`。push 被拒絕、remote 已經前進或回報 content skew 時，停止調查。

其他 clone 依序執行：

1. 確認 4.2 已用舊版 push 所有工作，並等遷移者通知已發布。
2. 開子 shell，跑 4.1 的設定段與建立備份目錄段，再用舊版備份
   `cp -a .beads "$BEADS_BACKUP_DIR/beads-before"`。
3. 安裝同一版 `bd`。手動二進位檔要先依 5.1 前半下載並核對 checksum，再依 5.2 原子替換。
4. 執行 `bd bootstrap`，採用遷移後的資料庫。它會取代本機資料庫，未 push 的工作會遺失。
5. 用 `bd migrate schema --json` 確認結構版本與遷移者相同，再用 `bd status`、`bd ready`
   確認看得到遷移者那邊的工作。
6. 執行 5.3 的 hooks 與代理整合更新。

其他 clone 執行 `bd dolt pull` 會因為仍有待處理遷移而被拒絕，這是預期行為。

## 六、回復

回復只適用於新結構尚未 push 到 remote 的情況。push 之後不要在單一 clone 還原舊結構，也不要
force push 覆蓋 remote；改依上游 remote-backed recovery 流程處理。

子 shell 已結束時，先依 4.1 重開並接回原本的備份目錄。

舊版執行檔開不了已遷移的資料庫，所以先判斷現行庫有沒有被新版開過，有差異時保留失敗現場，
再一起回復資料庫：

```bash
cd "$BEADS_REPO"
beads_assert_idle
if diff -qr .beads "$BEADS_BACKUP_DIR/beads-before" >/dev/null; then
  printf '現行庫未被新版開過，只回復執行檔\n'
else
  mv .beads "$BEADS_BACKUP_DIR/beads-failed"
  cp -a "$BEADS_BACKUP_DIR/beads-before" .beads
fi
```

回復執行檔的方式：

- 手動二進位檔：

  ```bash
  install -m 755 "$BEADS_BACKUP_DIR/bd-old" "$BEADS_BIN.rollback.new"
  mv "$BEADS_BIN.rollback.new" "$BEADS_BIN"
  ```

- npm：`npm install -g @beads/bd@<舊版>`。
- Homebrew 或安裝腳本：沒有簡單的舊版安裝方式。把 `bd-old` 以 `bd` 為檔名複製到 PATH 中
  較前面的目錄，暫時使用。

舊版是已撤回的 1.2.0 或 1.2.1 時，回復只能當暫時措施；查清原因後仍要升到 1.3.x。

`.beads/hooks` 已隨上面的 `.beads` 一起回復。hooks 在 `.git/hooks` 時，另外放回 5.3 的備份。
代理整合用舊版檢查，顯示 stale 時再執行 `bd setup claude` 或 `bd setup codex`：

```bash
if [[ -d "$BEADS_BACKUP_DIR/hooks-before" ]]; then
  cp -a "$BEADS_BACKUP_DIR/hooks-before/." "$(git rev-parse --git-path hooks)/"
fi
bd hooks list
bd setup claude --check
bd setup codex --check
```

回復後重跑 5.3 的比對，結果必須與基線相同。不一致時保留現場並停止，不要執行 `bd init`、
`bd import`、rebuild 或 `bd doctor --fix`。

## 七、server、shared server 與 proxied 模式

本節依官方文件整理，未經本指南實測。

- server 類資料庫不會隨版本自動遷移，因為遷移會同時影響連到同一個 Dolt server 的所有 client。
- 先把所有 client 升級到新版。升級後的 client 可以讀，但寫入會被拒絕，直到完成同意步驟。
- 在一個已設定好的 workspace 執行一次 `bd migrate schema` 表示同意，共用 global 資料庫時加
  `--global`；接著用 `bd doctor` 確認。
- shared server 同時設有 Dolt remote 時，`bd migrate schema` 不夠，要由唯一一台機器執行
  `bd migrate --force`，再 `bd dolt push`。
- proxied 模式下，長駐的 `bd serve` 遇到待處理遷移會拒絕啟動。先完成同意步驟再啟動服務。

細節見官方 [Upgrading：Shared servers](https://beads.gascity.com/getting-started/upgrading#shared-servers)。

## 八、常見問題

| 問題 | 原因 | 處理 |
| --- | --- | --- |
| 候選版或新版的訊息指向現行 `.beads` | 在 repo 目錄執行候選版，它往上找到現行 workspace | 立刻 `diff -qr .beads "$BEADS_BACKUP_DIR/beads-before"`；有差異依第六節回復 |
| 候選版顯示 0 筆 issue | 只用 `--db` 指向資料庫目錄，缺少 `.beads` 父層設定 | 複製完整 `.beads`，用 `-C` 指向副本 |
| 安裝新版後 `bd dolt push`／`pull` 被拒絕 | 有待處理遷移時，閘門擋下所有同步 | 同步要在安裝前用舊版完成；遷移者先遷移再 push |
| 從 1.2.1 改用 1.2.2 後出現 `schema version mismatch: database is at v65` | 1.2.1 已撤回，1.2.2 只認得 v53 | 改升到 1.3.x；或依上游復原程序撥回結構紀錄 |
| `bd doctor` 只印出 embedded 不支援 | 1.3.1 的 doctor 尚未支援 embedded | 改跑 `doctor --check=artifacts`、`conventions`、`pollution` 與 5.3 的比對 |
| 遷移看似卡住或計數倒退 | v1.3.0 的 clone-local 遷移重新計數；非終端機不顯示進度 | 不要中斷；它可從中斷處續跑 |
| `migrate` 輸出缺少閘門訊息 | wrapper 非同步過濾 stderr | 稍等再讀輸出；以 `bd migrate schema --json` 判斷 |
| 命令回傳 141 讓子 shell 結束 | `pipefail` 下把輸出直接接給 `head` | 先存檔再用 `head` |
| `lsof: command not found` | 系統沒有安裝 `lsof` | Linux 改查 `/proc/<pid>/fd`，見 4.1 的函式 |
| 代理整合顯示 stale | 管理區段版本與新版不一致 | 重新執行 `bd setup claude` 或 `bd setup codex`，再重開工具 |
| 升級後 ready 變多 | 過期 defer 回到 ready，或自訂 active status 列入 ready | 逐筆確認屬於 2.3 的行為變更 |

## 九、實測摘要

2026-10-06 在一個 embedded 模式、設有 Dolt remote、只有一個 clone 的工作區，從 1.2.1 升到
1.3.1：

- 第三節比對只新增主線 `0066` 與 clone-local `0025`、`0026`。
- 副本與現行庫都由閘門判定 remote 同版，自動套用 1 支主線遷移（v65 → v66），沒有用
  `--force`；兩次都在 5 秒內完成。
- 約 800 筆 issue 的逐筆狀態、ready ID 雜湊與 memories 數量前後一致。
- `bd doctor` 在 embedded 模式不可用；hooks 只改 marker 版號。
- 在 repo 目錄執行過一次候選版的 `version`，它找到現行 `.beads`；`diff -qr` 證明現行庫沒有
  變動，之後改在副本目錄執行。

這次沒有涵蓋多 clone、server 模式與 Homebrew／npm 安裝。

## 相關資源

- [Beads 指南](BEADS-GUIDE.md)
- [官方 Upgrading](https://beads.gascity.com/getting-started/upgrading)
- [Accidental v1.2.1 Release](https://beads.gascity.com/recovery/accidental-1-2-1-release)
- [v1.3.0 release notes](https://github.com/gastownhall/beads/releases/tag/v1.3.0)
- [v1.3.1 release notes](https://github.com/gastownhall/beads/releases/tag/v1.3.1)
- [設定參考（v1.3.1）](https://github.com/gastownhall/beads/blob/v1.3.1/docs/reference/configuration.md)
- [官方安裝文件](https://github.com/gastownhall/beads/blob/main/docs/getting-started/installation.md)

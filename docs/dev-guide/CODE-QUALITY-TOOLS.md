# 程式碼品質工具安裝指南

ecc-hooks 的 PostToolUse hooks 會在編輯檔案後自動執行程式碼品質檢查。這些工具為**可選安裝**，若未安裝則 hooks 會靜默跳過。

## JavaScript / TypeScript

### Prettier（格式化）

```bash
# npm
npm install --save-dev prettier

# pnpm
pnpm add -D prettier

# yarn
yarn add -D prettier
```

**配置檔（可選）**：`.prettierrc` 或 `prettier.config.js`

### TypeScript（型別檢查）

```bash
# npm
npm install --save-dev typescript

# pnpm
pnpm add -D typescript

# yarn
yarn add -D typescript
```

**必要配置**：`tsconfig.json`（hooks 會搜尋此檔案，不存在則跳過型別檢查）

```bash
# 初始化 tsconfig.json
npx tsc --init
```

---

## PHP

### Laravel Pint（格式化，推薦）

```bash
composer require laravel/pint --dev
```

**配置檔（可選）**：`pint.json`

### PHP-CS-Fixer（格式化，替代方案）

```bash
composer require friendsofphp/php-cs-fixer --dev
```

**配置檔**：`.php-cs-fixer.php` 或 `.php-cs-fixer.dist.php`

### PHPStan（靜態分析）

```bash
composer require phpstan/phpstan --dev
```

**配置檔（可選）**：`phpstan.neon` 或 `phpstan.neon.dist`

```neon
# phpstan.neon 範例
parameters:
    level: 5
    paths:
        - src
        - app
```

### PHPUnit（測試）

```bash
composer require phpunit/phpunit --dev
```

**配置檔**：`phpunit.xml` 或 `phpunit.xml.dist`

```bash
# 初始化 phpunit.xml
./vendor/bin/phpunit --generate-configuration
```

**執行測試**：

```bash
./vendor/bin/phpunit
./vendor/bin/phpunit --filter TestClassName
./vendor/bin/phpunit --coverage-html coverage/
```

---

## Python

### Ruff（格式化 + Linting，推薦）

```bash
# pip
pip install ruff

# uv
uv add --dev ruff

# pipx（全域安裝）
pipx install ruff
```

**配置檔（可選）**：`ruff.toml` 或 `pyproject.toml`

```toml
# pyproject.toml 範例
[tool.ruff]
line-length = 88
select = ["E", "F", "I"]
```

### Black（格式化，替代方案）

```bash
# pip
pip install black

# uv
uv add --dev black
```

**配置檔（可選）**：`pyproject.toml`

### mypy（型別檢查）

```bash
# pip
pip install mypy

# uv
uv add --dev mypy
```

**配置檔（可選）**：`mypy.ini` 或 `pyproject.toml`

```toml
# pyproject.toml 範例
[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true
```

### pytest（測試）

```bash
# pip
pip install pytest pytest-cov

# uv
uv add --dev pytest pytest-cov
```

**配置檔（可選）**：`pyproject.toml` 或 `pytest.ini`

```toml
# pyproject.toml 範例
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --cov=src"
```

**執行測試**：

```bash
pytest
pytest -v tests/test_specific.py
pytest --cov=src --cov-report=html
```

---

## 工具偵測邏輯

ecc-hooks 會自動偵測專案中已安裝的工具：

| 語言 | 格式化偵測 | 靜態分析偵測 |
|------|-----------|-------------|
| JS/TS | `npx prettier`（假設可用） | `tsconfig.json` 存在 |
| PHP | `vendor/bin/pint` → `.php-cs-fixer.php` | `vendor/bin/phpstan` 存在 |
| Python | `ruff` → `black`（fallback） | `pyproject.toml` 或 `mypy.ini` 存在 |

## Debug 程式碼偵測

hooks 會警告以下 debug 程式碼：

| 語言 | 偵測模式 |
|------|---------|
| JS/TS | `console.log` |
| PHP | `var_dump`, `print_r`, `dd`, `dump`, `error_log`, `ray` |
| Python | `print`, `pprint`, `breakpoint`, `pdb`, `ic` |

---

## 快速安裝腳本

### JavaScript/TypeScript 專案

```bash
npm install --save-dev prettier typescript
npx tsc --init
```

### PHP 專案（Laravel）

```bash
composer require --dev laravel/pint phpstan/phpstan phpunit/phpunit
```

### PHP 專案（一般）

```bash
composer require --dev friendsofphp/php-cs-fixer phpstan/phpstan phpunit/phpunit
```

### Python 專案

```bash
# 使用 uv
uv add --dev ruff mypy pytest pytest-cov

# 使用 pip
pip install ruff mypy pytest pytest-cov
```

---

## 疑難排解

### 工具未被偵測

**症狀**：編輯檔案後未自動執行格式化或檢查

**通用排查步驟**：

1. 確認已在專案目錄中執行
2. 檢查 Claude Code 輸出視窗是否有錯誤訊息
3. 確認工具已正確安裝（見下方各語言範例）

### JavaScript / TypeScript

**Prettier 未格式化**：

```bash
# 確認安裝
npx prettier --version

# 測試執行
npx prettier --check src/
```

**TypeScript 未檢查**：

```bash
# 確認 tsconfig.json 存在
ls tsconfig.json

# 確認安裝
npx tsc --version

# 測試執行
npx tsc --noEmit
```

### PHP

**Pint/PHP-CS-Fixer 未格式化**：

```bash
# 確認安裝（擇一）
./vendor/bin/pint --version
./vendor/bin/php-cs-fixer --version

# 測試執行
./vendor/bin/pint --test
```

**PHPStan 未執行**：

```bash
# 確認安裝
./vendor/bin/phpstan --version

# 確認配置檔存在
ls phpstan.neon phpstan.neon.dist 2>/dev/null

# 測試執行
./vendor/bin/phpstan analyse src/
```

### Python

**Ruff/Black 未格式化**：

```bash
# 確認安裝
ruff --version
black --version

# 測試執行
ruff check src/
ruff format --check src/
```

**mypy 未執行**：

```bash
# 確認安裝
mypy --version

# 確認配置檔存在
ls mypy.ini pyproject.toml 2>/dev/null

# 測試執行
mypy src/
```

### 常見錯誤訊息

| 錯誤訊息 | 可能原因 | 解決方式 |
|---------|---------|---------|
| `command not found` | 工具未安裝或不在 PATH 中 | 重新安裝或使用 npx/vendor/bin 路徑執行 |
| `No files matched` | Glob 模式不符合檔案 | 檢查配置檔中的 paths/include 設定 |
| `Configuration file not found` | 缺少必要配置檔 | 依上方指南建立配置檔 |
| `Permission denied` | 腳本無執行權限 | 執行 `chmod +x <script>` |

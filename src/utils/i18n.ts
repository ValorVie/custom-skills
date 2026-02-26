export type Locale = "en" | "zh-TW";

const DEFAULT_LOCALE: Locale = "en";

const messages: Record<Locale, Record<string, string>> = {
  en: {
    "install.checking_prerequisites": "Checking prerequisites...",
    "install.progress": "[{current}/{total}]",
    "format.example_only_en": "Only in English",

    "common.enabled": "Enabled",
    "common.disabled": "Disabled",
    "common.success": "Success",
    "common.failed": "Failed",
    "common.none": "(none)",

    "list.no_resources": "No resources found.",
    "list.status_enabled": "✓ Enabled",
    "list.status_disabled": "✗ Disabled",

    "toggle.invalid_target": "Invalid target: {target}",
    "toggle.invalid_type": "Invalid type: {type}",
    "toggle.invalid_combo": "Invalid target/type combination: {target}/{type}",
    "toggle.missing_target_type": "Missing --target and/or --type option",
    "toggle.missing_name": "Missing --name option",
    "toggle.choose_one": "Choose exactly one: --enable or --disable",
    "toggle.failed": "Resource toggle failed.",

    "hooks.source_not_found": "ecc-hooks plugin source not found.",
    "hooks.uninstall_confirm": "Uninstall ECC hooks plugin?",
    "hooks.uninstall_cancelled": "Uninstall cancelled.",
    "hooks.not_installed": "ecc-hooks plugin is not installed.",
    "hooks.installed": "Installed: {path}",
    "hooks.removed": "Removed: {path}",
    "hooks.source": "Source: {path}",

    "add_repo.added": "Tracked repo added: {name} ({repo})",
    "add_repo.duplicate": "Repository already tracked",
    "add_repo.failed": "Failed to add upstream repository",

    "add_custom.added": "Custom repo registered: {name}",
    "add_custom.created_dirs": "Created missing directories: {dirs}",
    "add_custom.missing_dirs": "Missing directories: {dirs}",

    "update_custom.done": "Custom repositories update complete",
    "update_custom.no_repos": "No custom repositories configured.",
    "update_custom.errors": "Errors: {errors}",

    "test.unsupported_framework": "Unsupported framework: {framework}",
    "coverage.unsupported_framework": "Unsupported framework: {framework}",

    "status.updates_available": "↑ {count} updates available",
    "status.upstream_behind": "⚠ behind {count}",
  },
  "zh-TW": {
    "install.checking_prerequisites": "檢查前置需求...",
    "install.progress": "[{current}/{total}]",

    "common.enabled": "已啟用",
    "common.disabled": "已停用",
    "common.success": "成功",
    "common.failed": "失敗",
    "common.none": "（無）",

    "list.no_resources": "找不到資源。",
    "list.status_enabled": "✓ 已啟用",
    "list.status_disabled": "✗ 已停用",

    "toggle.invalid_target": "無效 target: {target}",
    "toggle.invalid_type": "無效 type: {type}",
    "toggle.invalid_combo": "無效 target/type 組合: {target}/{type}",
    "toggle.missing_target_type": "缺少 --target 或 --type 參數",
    "toggle.missing_name": "缺少 --name 參數",
    "toggle.choose_one": "請擇一使用 --enable 或 --disable",
    "toggle.failed": "資源切換失敗。",

    "hooks.source_not_found": "找不到 ecc-hooks plugin 來源。",
    "hooks.uninstall_confirm": "要移除 ECC hooks plugin 嗎？",
    "hooks.uninstall_cancelled": "已取消移除。",
    "hooks.not_installed": "ecc-hooks plugin 尚未安裝。",
    "hooks.installed": "已安裝：{path}",
    "hooks.removed": "已移除：{path}",
    "hooks.source": "來源：{path}",

    "add_repo.added": "已加入追蹤 repo：{name} ({repo})",
    "add_repo.duplicate": "此 repo 已存在於追蹤清單",
    "add_repo.failed": "新增上游 repo 失敗",

    "add_custom.added": "已註冊自訂 repo：{name}",
    "add_custom.created_dirs": "已建立缺少目錄：{dirs}",
    "add_custom.missing_dirs": "仍缺少目錄：{dirs}",

    "update_custom.done": "自訂 repositories 更新完成",
    "update_custom.no_repos": "沒有設定任何自訂 repository。",
    "update_custom.errors": "錯誤：{errors}",

    "test.unsupported_framework": "不支援的測試框架：{framework}",
    "coverage.unsupported_framework": "不支援的測試框架：{framework}",

    "status.updates_available": "↑ 可更新 {count} 筆",
    "status.upstream_behind": "⚠ 落後 {count}",
  },
};

let locale: Locale = DEFAULT_LOCALE;

function interpolate(
  template: string,
  params: Record<string, string> | undefined,
): string {
  if (!params) {
    return template;
  }

  return template.replaceAll(/\{([a-zA-Z0-9_]+)\}/g, (full, key: string) => {
    return params[key] ?? full;
  });
}

export function t(key: string, params?: Record<string, string>): string {
  const template = messages[locale][key] ?? messages.en[key] ?? key;
  return interpolate(template, params);
}

export function setLocale(nextLocale: Locale): void {
  locale = nextLocale;
}

export function getLocale(): Locale {
  return locale;
}

export function isLocale(value: string): value is Locale {
  return value === "en" || value === "zh-TW";
}

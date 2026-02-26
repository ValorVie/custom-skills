import { beforeEach, describe, expect, test } from "bun:test";

import { getLocale, setLocale, t } from "../../src/utils/i18n";

describe("i18n DEFAULT_LOCALE", () => {
  test("initial locale is zh-TW", () => {
    expect(getLocale()).toBe("zh-TW");
    expect(t("install.checking_prerequisites")).toBe("檢查前置需求...");
  });
});

describe("utils/i18n", () => {
  beforeEach(() => {
    setLocale("en");
  });

  test("works with english locale", () => {
    expect(getLocale()).toBe("en");
    expect(t("install.checking_prerequisites")).toBe(
      "Checking prerequisites...",
    );
  });

  test("switches locale to zh-TW", () => {
    setLocale("zh-TW");
    expect(getLocale()).toBe("zh-TW");
    expect(t("install.checking_prerequisites")).toBe("檢查前置需求...");
  });

  test("supports parameterized translation", () => {
    expect(t("install.progress", { current: "3", total: "6" })).toBe("[3/6]");
  });

  test("falls back to english for missing locale key", () => {
    setLocale("zh-TW");
    expect(t("format.example_only_en")).toBe("Only in English");
  });

  test("returns key when translation is missing everywhere", () => {
    expect(t("missing.key")).toBe("missing.key");
  });
});

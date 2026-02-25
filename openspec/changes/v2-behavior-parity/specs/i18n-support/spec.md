## ADDED Requirements

### Requirement: Locale configuration
The system SHALL support configurable output language with English as default.

#### Scenario: Default locale is English
- **WHEN** no locale is configured
- **THEN** all CLI output is in English

#### Scenario: Configure locale via config file
- **WHEN** `~/.config/ai-dev/config.yaml` contains `locale: zh-TW`
- **THEN** all CLI output is in Traditional Chinese

#### Scenario: CLI flag overrides config file
- **WHEN** user runs `ai-dev --lang zh-TW status`
- **THEN** output is in Traditional Chinese regardless of config file setting

### Requirement: Translation function
The system SHALL provide `t(key, params?)` function for all user-facing strings.

#### Scenario: Simple translation
- **WHEN** code calls `t("install.checking_prerequisites")` with locale `en`
- **THEN** returns `"Checking prerequisites..."`

#### Scenario: Parameterized translation
- **WHEN** code calls `t("install.progress", { current: "3", total: "6" })` with locale `en`
- **THEN** returns `"[3/6]"`

#### Scenario: Missing translation falls back to English
- **WHEN** a key has no zh-TW translation
- **THEN** English translation is used as fallback

### Requirement: Supported locales
The system SHALL support `en` (English) and `zh-TW` (Traditional Chinese).

#### Scenario: English locale
- **WHEN** locale is `en`
- **THEN** all strings are in English

#### Scenario: Traditional Chinese locale
- **WHEN** locale is `zh-TW`
- **THEN** all strings are in Traditional Chinese with technical terms preserved in English

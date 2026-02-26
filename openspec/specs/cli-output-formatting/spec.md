# cli-output-formatting Specification

## Purpose
TBD - Defines CLI output formatting requirements including table output, color-coded indicators, progress spinners, and formatter utilities.

## Requirements

### Requirement: Formatted table output
The system SHALL provide formatted table output for non-JSON CLI modes using cli-table3.

#### Scenario: Status command displays formatted table
- **WHEN** user runs `ai-dev status` without `--json`
- **THEN** system displays tool versions, NPM packages, and repository statuses in formatted tables with borders and alignment

#### Scenario: List command displays formatted table
- **WHEN** user runs `ai-dev list` without `--json`
- **THEN** system displays resources grouped by target/type in a formatted table with enabled/disabled status indicators

#### Scenario: JSON mode bypasses formatting
- **WHEN** user runs any command with `--json`
- **THEN** system outputs raw JSON without any table formatting or color codes

### Requirement: Color-coded status indicators
The system SHALL use chalk color codes to indicate success/failure/warning states.

#### Scenario: Success indicator
- **WHEN** an operation completes successfully
- **THEN** system displays green checkmark `✓` and green text

#### Scenario: Failure indicator
- **WHEN** an operation fails
- **THEN** system displays red cross `✗` and red error message

#### Scenario: Warning indicator
- **WHEN** a non-critical issue is detected
- **THEN** system displays yellow warning text

### Requirement: Progress spinner for long operations
The system SHALL display ora spinners during long-running operations (install, update, clone, sync).

#### Scenario: Install with spinner
- **WHEN** user runs `ai-dev install`
- **THEN** system shows spinner with current operation name (e.g., "Installing @anthropic-ai/claude-code...")

#### Scenario: Spinner suppressed in JSON mode
- **WHEN** user runs `ai-dev install --json`
- **THEN** no spinner is displayed

### Requirement: Progress counter
The system SHALL display `[i/total]` progress counters for batch operations.

#### Scenario: NPM package install progress
- **WHEN** installing 6 NPM packages
- **THEN** system displays `[1/6] Installing pkg-name...` through `[6/6] Installing pkg-name...`

### Requirement: Formatter utility module
The system SHALL provide `src/utils/formatter.ts` with reusable formatting functions.

#### Scenario: printTable function
- **WHEN** code calls `printTable(headers, rows)`
- **THEN** a cli-table3 formatted table is printed to stdout

#### Scenario: printSuccess function
- **WHEN** code calls `printSuccess("message")`
- **THEN** green colored success message is printed to stdout

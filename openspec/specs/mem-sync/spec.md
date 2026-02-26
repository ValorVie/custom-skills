# mem-sync Specification

## Purpose
TBD - Defines memory synchronization capabilities including push/pull via HTTP API with hash deduplication and auto-sync scheduling.

## Requirements

### Requirement: Memory push uploads observations via HTTP API
The mem push command SHALL upload local observations to the remote sync server using HTTP API with hash deduplication.

#### Scenario: Push new observations
- **WHEN** user runs `ai-dev mem push` and local observations exist
- **THEN** system uploads observations not yet on remote (deduplicated by content hash)

#### Scenario: Batched upload
- **WHEN** pushing more than 100 observations
- **THEN** system uploads in batches of 100 with progress indicator

#### Scenario: Hash deduplication
- **WHEN** an observation with identical content hash exists on remote
- **THEN** system skips that observation

### Requirement: Memory pull downloads observations via HTTP API
The mem pull command SHALL download remote observations with paginated retrieval and merge logic.

#### Scenario: Pull new observations
- **WHEN** user runs `ai-dev mem pull`
- **THEN** system downloads observations not yet in local store

#### Scenario: Paginated pull
- **WHEN** remote has more than 100 new observations
- **THEN** system fetches in pages of 100 until all received

### Requirement: Auto-sync scheduling
The mem auto command SHALL configure automatic sync via system scheduler.

#### Scenario: Enable auto-sync on Linux
- **WHEN** user runs `ai-dev mem auto --enable` on Linux
- **THEN** system creates systemd timer or cron job for periodic sync

#### Scenario: Enable auto-sync on macOS
- **WHEN** user runs `ai-dev mem auto --enable` on macOS
- **THEN** system creates launchd plist for periodic sync

#### Scenario: Disable auto-sync
- **WHEN** user runs `ai-dev mem auto --disable`
- **THEN** system removes the scheduled sync job

#### Scenario: Check auto-sync status
- **WHEN** user runs `ai-dev mem auto --status`
- **THEN** system displays whether auto-sync is enabled and next scheduled run

### Requirement: Memory status shows sync state
The mem status command SHALL display device info, observation count, and remote sync state.

#### Scenario: Status with sync info
- **WHEN** user runs `ai-dev mem status`
- **THEN** system displays device name, observation count, last sync time, and pending push count

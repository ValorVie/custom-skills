## MODIFIED Requirements

### Requirement: List command shows enabled/disabled status and source
The list command SHALL display enabled/disabled status indicators and resource source information.

#### Scenario: Enabled resource display
- **WHEN** a resource is enabled
- **THEN** system shows green `✓ Enabled` indicator

#### Scenario: Disabled resource display
- **WHEN** a resource is disabled
- **THEN** system shows red `✗ Disabled` indicator

#### Scenario: Source display
- **WHEN** listing resources
- **THEN** each resource shows its source (e.g., "custom-skills", "anthropic-skills", "user-custom")

#### Scenario: Hide disabled option
- **WHEN** user runs `ai-dev list --hide-disabled`
- **THEN** disabled resources are excluded from output

### Requirement: Status command shows upstream sync state
The status command SHALL display upstream repository sync status with commit counts.

#### Scenario: Upstream sync display
- **WHEN** user runs `ai-dev status`
- **THEN** system shows for each upstream repo whether it is up-to-date or N commits behind

#### Scenario: Repository update availability
- **WHEN** a repository has available updates
- **THEN** system shows `↑ N updates available` indicator

### Requirement: Toggle validates target/type combinations
The toggle command SHALL validate that the target/type combination is valid before toggling.

#### Scenario: Invalid combination
- **WHEN** user runs `ai-dev toggle --target gemini --type agents`
- **THEN** system displays error if Gemini does not support agents

#### Scenario: List with formatted table
- **WHEN** user runs `ai-dev toggle --list`
- **THEN** system displays toggle state in formatted table

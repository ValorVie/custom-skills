## MODIFIED Requirements

### Requirement: Standards switch computes disabled items
The standards switch command SHALL compute disabled items by comparing the new profile with the full standard set and generate disabled.yaml.

#### Scenario: Switch profile
- **WHEN** user runs `ai-dev standards switch <profile>`
- **THEN** system writes active-profile.yaml, computes disabled items (standards not in new profile), generates disabled.yaml, and moves disabled standards to .disabled/

#### Scenario: Disabled items computation
- **WHEN** switching from level-3 to level-1 profile
- **THEN** system identifies all level-2 and level-3 standards as disabled and records them in disabled.yaml

## ADDED Requirements

### Requirement: Standards sync to tool directories
The standards sync command SHALL synchronize standards files to all configured tool directories.

#### Scenario: Sync standards
- **WHEN** user runs `ai-dev standards sync`
- **THEN** system copies .standards/ content to each target tool directory that supports standards

#### Scenario: Sync with move operations
- **WHEN** standards are disabled
- **THEN** system moves disabled standard files from .standards/ to .standards/.disabled/

### Requirement: Formatted overlaps display
The standards overlaps command SHALL display overlap detection results in formatted tables.

#### Scenario: Overlaps table output
- **WHEN** user runs `ai-dev standards overlaps`
- **THEN** system displays overlapping standards in a formatted table showing standard name, overlapping profiles, and conflict description

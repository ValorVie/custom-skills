# Capability: Git Workflow

## ADDED Requirements

### Requirement: Merge Strategy (合併策略)
The workflow MUST support a `merge` mode to combine multiple feature branches into a transient test branch.

#### Scenario: Multi-branch Integration
Given a list of feature branches `feature/A`, `feature/B`
When `git-commit merge feature/A feature/B` is executed
Then the system should:
1. Switch to `master` and pull latest changes.
2. Create a new branch named `test-dev-YYYYMMDDhhmmss`.
3. Merge `feature/A` and `feature/B` into the new branch using `--no-ff`.
4. Push the new branch to remote.

### Requirement: Branch Naming (分支命名)
The transient integration branch MUST follow the naming convention `test-dev-$TIMESTAMP`.

#### Scenario: Timestamp Format
When creating the test branch
Then the name should be strictly `test-dev-YYYYMMDDhhmmss` (e.g., `test-dev-20260115170000`).

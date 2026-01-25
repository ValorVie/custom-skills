# git-workflow Specification Delta

## ADDED Requirements

### Requirement: PR Mode (建立 Pull Request 模式)

The workflow MUST support a `pr` mode to automate the "squash commits → push → create PR" workflow.

#### Scenario: Basic PR Creation (Draft by Default)

Given a feature branch `feature/my-feature` with commits since branching from main
When `git-commit pr` is executed
Then the system should:
1. Verify the current branch is not the main branch.
2. Verify `gh` CLI is installed and authenticated.
3. Calculate the merge-base with main/master.
4. Squash all commits since merge-base into one commit.
5. Push the branch to remote.
6. Create a **draft** Pull Request using `gh pr create --draft`.
7. Display the PR URL (without opening browser).

#### Scenario: PR with Direct Mode (Non-draft)

Given a feature branch with commits
When `git-commit pr --direct` is executed
Then the PR should be created as a regular (non-draft) PR.

#### Scenario: PR without Squash

Given a feature branch with multiple commits
When `git-commit pr --no-squash` is executed
Then all original commits should be preserved (not squashed).

### Requirement: PR Range Specification (範圍指定)

The `pr` mode MUST allow users to specify custom commit ranges.

#### Scenario: Range with --from

Given a feature branch with commits A, B, C, D (oldest to newest)
When `git-commit pr --from B` is executed
Then only commits B, C, D should be included in the PR.

#### Scenario: Range with --range

Given a feature branch with commits A, B, C, D
When `git-commit pr --range B..D` is executed
Then only commits B, C, D should be included in the PR.

### Requirement: PR Content Generation (內容生成)

The workflow MUST auto-generate meaningful PR title and body.

#### Scenario: Auto-generated PR Content

Given a feature branch with meaningful commit messages
When `git-commit pr` is executed without `--title` or `--body`
Then the system should:
1. Generate a PR title from the squashed commit message.
2. Generate a PR body with:
   - Summary section
   - Changes section (bullet points)
   - Files Changed section (grouped by operation)
   - Footer with generation attribution.

#### Scenario: Custom PR Title

Given a feature branch
When `git-commit pr --title "Custom Title"` is executed
Then the PR should use the custom title instead of auto-generated one.

### Requirement: PR Prerequisites Check (前置檢查)

The workflow MUST validate prerequisites before proceeding.

#### Scenario: Main Branch Protection

Given the current branch is `main` or `master`
When `git-commit pr` is executed
Then the system should display an error and abort.

#### Scenario: gh CLI Not Installed

Given `gh` CLI is not installed
When `git-commit pr` is executed
Then the system should display installation instructions and abort.

#### Scenario: gh CLI Not Authenticated

Given `gh` CLI is installed but not authenticated
When `git-commit pr` is executed
Then the system should prompt `gh auth login` and abort.

#### Scenario: No Changes to PR

Given the current branch has no commits since merge-base
When `git-commit pr` is executed
Then the system should display "No changes to create PR" and abort.

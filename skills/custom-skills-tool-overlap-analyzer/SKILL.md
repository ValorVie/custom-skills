---
name: custom-skills-tool-overlap-analyzer
description: |
  Analyze tooling overlap and optimization opportunities in AI-assisted development projects.
  Use when: (1) auditing project tooling ecosystem, (2) identifying duplicate or redundant tools,
  (3) finding consolidation opportunities, (4) generating tooling health reports.
  Triggers: "analyze tools", "tool overlap", "tooling audit", "redundant skills", "consolidate commands"
---

# Tool Overlap Analyzer

Analyze project tooling (agents, skills, commands, hooks, workflows) for overlap and optimization opportunities. Each tool type is compared only within its own category.

## Workflow

```
┌──────────────────────────────────────────────────────────────────┐
│                      Analysis Pipeline                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  0. Dedup       1. Discovery    2. Coarse Scan                   │
│  ┌─────────┐    ┌─────────┐     ┌─────────┐                     │
│  │ Remove  │───▶│ Find all│────▶│ Read 20 │                     │
│  │platform │    │  tools  │     │  lines  │                     │
│  │ copies  │    └─────────┘     └─────────┘                     │
│  └─────────┘                         │                           │
│                                      ▼                           │
│                              Similar? ──No──▶ Skip               │
│                                  │                               │
│                                 Yes                              │
│                                  │                               │
│                                  ▼                               │
│  3. Deep Analysis       3.5. Cross-Reference      4. Report     │
│  ┌─────────────┐        ┌─────────────────┐     ┌──────────┐   │
│  │Full semantic│───────▶│ Check if tool   │────▶│ Generate │   │
│  │ comparison  │        │ is referenced   │     │  report  │   │
│  └─────────────┘        │ by other files  │     └──────────┘   │
│                         └─────────────────┘                     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Step 0: Deduplication (Cross-Platform Copies)

Many projects distribute identical tools to multiple platform directories (e.g., `agents/claude/`, `agents/opencode/`, `skills/agents/`). These are **intentional copies for distribution**, not redundancy issues.

**Before analysis, deduplicate by:**

1. **Identify platform directories**:
   - `*/claude/`, `*/opencode/`, `*/gemini/` → platform-specific
   - `skills/agents/` → may mirror `agents/*/`

2. **Compare files with same name across platforms**:
   - If content is identical (or near-identical) → treat as single tool
   - Keep one representative for analysis (prefer `claude/` or first found)

3. **Record deduplication**:
   ```
   Deduplicated: code-architect.md
   - agents/claude/code-architect.md (analyzed)
   - agents/opencode/code-architect.md (skipped - identical)
   - skills/agents/code-architect.md (skipped - identical)
   ```

**Important**: Cross-platform copies are NOT overlap issues. Only compare unique tools within each type.

## Step 1: Discovery

Scan the project for each tool type:

| Type | Search Locations |
|------|------------------|
| **Agents** | `.claude/agents/`, `agents/`, `skills/agents/` |
| **Skills** | `.claude/skills/`, `skills/`, `.agent/skills/` |
| **Commands** | `.claude/commands/`, `commands/` |
| **Hooks** | `.claude/settings*.json` (hooks section) |
| **Workflows** | `skills/workflows/`, `.agent/workflows/`, `**/*.workflow.yaml` |

For each discovered tool, record:
- File path
- Name (from filename or frontmatter)
- First 20 lines (for coarse scan)

## Step 2: Coarse Scan (Within Same Type Only)

For each tool type separately, compare tools using:

1. **Name similarity** - Similar names suggest overlap (e.g., `git-commit` vs `commit-standards`)
2. **Keyword extraction** - Extract key terms from first 20 lines
3. **Purpose inference** - Infer primary purpose from description/frontmatter

Flag pairs as "potentially overlapping" if:
- Name similarity > 60% (Levenshtein or semantic)
- Shared keywords > 3
- Similar inferred purpose

## Step 3: Deep Analysis

For flagged pairs, read full content and analyze:

### Overlap Categories

| Category | Description | Example |
|----------|-------------|---------|
| **Duplicate** | Nearly identical functionality | Two commit message generators |
| **Subset** | One is subset of another | Basic TDD vs full TDD workflow |
| **Complementary** | Different aspects of same domain | BDD scenarios vs BDD runner |
| **Naming Conflict** | Same name, different purpose | Rare, flag for rename |

### Comparison Dimensions

```
┌────────────────────────────────────────────────────────────┐
│                  Comparison Matrix                          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   Dimension         Weight    How to Compare               │
│   ─────────────────────────────────────────────────────── │
│   Purpose           40%       What problem does it solve?  │
│   Trigger Context   20%       When is it invoked?          │
│   Output/Action     25%       What does it produce?        │
│   Dependencies      15%       What does it rely on?        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Overlap Score Calculation

```
Overlap Score = (Purpose × 0.4) + (Trigger × 0.2) + (Output × 0.25) + (Deps × 0.15)

Score Interpretation:
  90-100%  →  Duplicate (recommend: merge or remove)
  70-89%   →  High overlap (recommend: consolidate)
  50-69%   →  Moderate overlap (recommend: clarify boundaries)
  30-49%   →  Low overlap (recommend: document relationship)
  0-29%    →  Distinct (no action needed)
```

## Step 3.5: Cross-Reference Analysis (Before Optimization)

Before recommending merges or removals, check if tools are referenced by other files:

### Why This Matters

Tools often have **inter-dependencies**:
- Commands may reference Skills (e.g., `see: skill-name`)
- README files may list available tools
- Documentation may link to specific commands
- Other tools may call or reference the tool

### How to Check

For each tool flagged for potential merge/removal, search for references:

```bash
# Search for tool name in entire project
grep -r "tool-name" --include="*.md" --include="*.yaml" --include="*.json"

# Common reference patterns to find:
# - Direct links: [link](./tool-name.md)
# - Command references: /tool-name
# - Skill references: skill: tool-name
# - Import/see-also: see: tool-name
```

### Reference Categories

| Category | Impact | Action Required |
|----------|--------|-----------------|
| **Documentation** | README, guides | Update docs to reflect change |
| **Tool References** | Other skills/commands | Update calling tools |
| **Configuration** | mapping.yaml, overlaps.yaml | Update config files |
| **Archive/History** | Old proposals, reports | No action (historical) |

### Include in Report

For each optimization recommendation, add:

```markdown
**Cross-References Found:**
- `README.md:466` - Lists /tool-name in command table
- `commands/claude/README.md:91` - Command list entry
- `skills/other-skill/SKILL.md:15` - References as related

**Required Updates:** 3 files need updating before removal
```

## Step 4: Report Generation

Generate report at `docs/report/tool-overlap-analysis-{YYYY-MM-DD}.md`

### Report Structure

```markdown
# Tool Overlap Analysis Report
Generated: {date}
Project: {project-name}

## Executive Summary
- Total tools analyzed: {count}
- Overlap issues found: {count}
- Optimization opportunities: {count}

## Analysis by Tool Type

### Agents ({count} analyzed)
[Per-type analysis with findings]

### Skills ({count} analyzed)
[Per-type analysis with findings]

### Commands ({count} analyzed)
[Per-type analysis with findings]

### Hooks ({count} analyzed)
[Per-type analysis with findings]

### Workflows ({count} analyzed)
[Per-type analysis with findings]

## Detailed Findings

### High Priority (Score >= 70%)
[Detailed comparison for each high-overlap pair]

### Medium Priority (Score 50-69%)
[Detailed comparison for each moderate-overlap pair]

### Low Priority (Score 30-49%)
[Brief notes on low-overlap pairs]

## Optimization Recommendations

### Merge Candidates
[Tools that should be combined]

### Deprecation Candidates
[Tools that could be removed]

### Boundary Clarification Needed
[Tools that need clearer scope definition]

### Documentation Improvements
[Tools that need better relationship documentation]

## Appendix: Tool Inventory
[Complete list of all discovered tools by type]
```

## Writing Style for Report

The report should be written in natural, readable prose:

- Use clear headings and subheadings
- Explain findings in context, not just list data
- Provide actionable recommendations
- Include reasoning for each suggestion
- Use tables for comparisons, prose for analysis
- Maintain professional but accessible tone

## Example Analysis Output

```markdown
### Skills: custom-skills-git-commit vs commit-standards

**Overlap Score: 78% (High)**

| Dimension | custom-skills-git-commit | commit-standards | Similarity |
|-----------|-------------------|------------------|------------|
| Purpose | Generate commits with custom workflow | Format commit messages | 85% |
| Trigger | "git commit", "commit changes" | "commit message", "format commit" | 70% |
| Output | Git commit executed | Commit message text | 75% |
| Dependencies | Git CLI | None | 60% |

**Analysis:**
Both skills address commit message generation, but `custom-skills-git-commit` includes
the full workflow (staging, committing, pushing) while `commit-standards` focuses
solely on message formatting according to Conventional Commits.

**Recommendation:**
Consider merging `commit-standards` into `custom-skills-git-commit` as the message
formatting module, or clearly document that `commit-standards` is the lightweight
option for users who only need message formatting.
```

## Invocation

To run this analysis:

1. Ensure you're in the project root
2. Invoke: "Analyze tool overlap" or "Run tooling audit"
3. Review generated report at `docs/report/`

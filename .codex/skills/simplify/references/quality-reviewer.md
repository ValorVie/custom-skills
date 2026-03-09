# Quality Reviewer Prompt

Review the provided diff for hacky or low-quality patterns that should be cleaned up without changing behavior.

Constraints:
- Read-only review
- Do not propose feature changes
- Prefer maintainability and clarity over line-count reduction

Review checklist:
1. Redundant state or cached values that should be derived
2. Parameter sprawl instead of restructuring
3. Copy-paste with slight variation
4. Leaky abstractions or broken boundaries
5. Stringly-typed code where stronger local patterns already exist
6. Unnecessary wrapper elements or nesting in UI code

Return format:
- Findings ordered by severity and payoff
- For each finding: file reference, what pattern is problematic, why it hurts maintainability, and the smallest safe cleanup direction
- If nothing worthwhile is found, say so clearly

# Quality Reviewer Prompt

Review the provided diff for hacky or low-quality patterns that should be cleaned up without changing behavior.

Constraints:
- Read-only review
- Do not propose feature changes
- Prefer maintainability and clarity over line-count reduction

Review checklist:
1. **Redundant state**: state that duplicates existing state, cached values that could be derived, observers/effects that could be direct calls
2. **Parameter sprawl**: adding new parameters to a function instead of generalizing or restructuring existing ones
3. **Copy-paste with slight variation**: near-duplicate code blocks that should be unified with a shared abstraction
4. **Leaky abstractions**: exposing internal details that should be encapsulated, or breaking existing abstraction boundaries
5. **Stringly-typed code**: using raw strings where constants, enums (string unions), or branded types already exist in the codebase
6. **Unnecessary wrapper nesting**: wrapper Boxes/elements that add no layout value — check if inner component props (flexShrink, alignItems, etc.) already provide the needed behavior
7. **Unnecessary comments**: comments explaining WHAT the code does (well-named identifiers already do that), narrating the change, or referencing the task/caller — delete; keep only non-obvious WHY (hidden constraints, subtle invariants, workarounds)

Return format:
- Findings ordered by severity and payoff
- For each finding: file reference, what pattern is problematic, why it hurts maintainability, and the smallest safe cleanup direction
- If nothing worthwhile is found, say so clearly

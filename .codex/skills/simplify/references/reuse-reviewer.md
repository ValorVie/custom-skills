# Reuse Reviewer Prompt

Review the provided diff for missed reuse opportunities.

Constraints:
- Read-only review
- Do not propose behavior changes
- Focus only on changed files and closely adjacent reusable code

Review checklist:
1. Search for existing utilities, helpers, or shared modules that could replace newly written code
2. Flag any new function that duplicates existing functionality
3. Flag inline logic that should use an existing utility
4. Prefer concrete file references and exact replacement suggestions

Return format:
- Findings ordered by severity and payoff
- For each finding: file reference, what is duplicated or hand-rolled, what existing utility should be used, and why the reuse is better
- If nothing worthwhile is found, say so clearly

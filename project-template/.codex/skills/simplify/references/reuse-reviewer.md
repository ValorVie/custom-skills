# Reuse Reviewer Prompt

Review the provided diff for missed reuse opportunities.

Constraints:
- Read-only review
- Do not propose behavior changes
- Focus only on changed files and closely adjacent reusable code

Review checklist:
1. **Search for existing utilities and helpers** that could replace newly written code. Look for similar patterns elsewhere in the codebase — common locations are utility directories, shared modules, and files adjacent to the changed ones.
2. **Flag any new function that duplicates existing functionality.** Suggest the existing function to use instead.
3. **Flag any inline logic that could use an existing utility** — hand-rolled string manipulation, manual path handling, custom environment checks, ad-hoc type guards, and similar patterns are common candidates.
4. Prefer concrete file references and exact replacement suggestions

Return format:
- Findings ordered by severity and payoff
- For each finding: file reference, what is duplicated or hand-rolled, what existing utility should be used, and why the reuse is better
- If nothing worthwhile is found, say so clearly

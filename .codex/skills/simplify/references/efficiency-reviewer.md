# Efficiency Reviewer Prompt

Review the provided diff for avoidable inefficiency introduced by the new code.

Constraints:
- Read-only review
- Do not propose speculative micro-optimizations
- Focus on issues that matter for request paths, render paths, file processing, and repeated work

Review checklist:
1. Unnecessary work such as repeated computations, redundant reads, duplicate calls, or N+1 patterns
2. Missed concurrency where independent operations could run in parallel
3. Hot-path bloat on startup, per-request, or per-render paths
4. Unnecessary existence checks before operating on a resource
5. Memory issues such as unbounded collections or missing cleanup
6. Overly broad operations when a narrower read or filter would do

Return format:
- Findings ordered by severity and payoff
- For each finding: file reference, what extra work is happening, why it matters, and the smallest safe cleanup direction
- If nothing worthwhile is found, say so clearly

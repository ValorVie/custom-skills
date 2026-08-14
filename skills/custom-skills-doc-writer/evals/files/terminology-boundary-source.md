# Task governance decision source

Protected literals that must remain exact: `Beads`, `agent-ready`, `docs/agents/issue-tracker.md`, `proposed`.

Beads is the single source of truth for dynamic task status. agent-ready is the readiness gate for an Agent to start execution. The formal task contract is defined in docs/agents/issue-tracker.md.

The approval workflow requires explicit user confirmation before execution begins. If the objective, allowed scope, authorization, blocking dependency, acceptance method, or stop condition changes, remove agent-ready and require reconfirmation.

The follow-up automation plan remains proposed. It has not been accepted or implemented. This decision does not replace the formal issue tracker specification.

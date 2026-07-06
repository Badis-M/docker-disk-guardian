# ADR 0002: Make analysis the default behavior

- Status: Accepted
- Date: 2026-08-27

## Context

Unused Docker resources can still contain important data. A convenient cleanup command must not
turn incomplete usage information into an implicit deletion decision.

## Decision

Inspection and planning are read-only. Deletion is available only through `apply`, after policy
evaluation, invariant checks, a visible summary, and explicit confirmation. Named volumes are
protected unless policy opts in. Running containers and their dependencies are always protected.

## Consequences

- Users can review identical human-readable and machine-readable plans.
- The executor rejects operations that bypass the planner's safety contract.
- Automation must explicitly supply `--yes` and a policy.


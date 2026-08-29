# Safety model

Docker Disk Guardian separates observation, policy decisions, and mutation into distinct stages.

## Read-only commands

`inspect` converts Docker SDK responses into typed resource models. `plan` evaluates those models
against a strict policy. Neither command has a path to the gateway's removal operation.

## Apply sequence

1. Load and validate the explicit policy.
2. Collect current inventory and calculate an explainable plan.
3. Display the complete plan.
4. Require confirmation unless `--yes` was supplied.
5. Collect inventory again.
6. Recalculate eligibility using the same policy.
7. Remove only resources present in both candidate sets.
8. Report every success, failure, skip, or interruption.

This second inventory and planning pass protects against a container starting or a resource becoming
referenced while the user reviews the plan.

## Hard protections

- Running containers are never candidates.
- Images referenced by any existing container are protected.
- Volumes and networks referenced by existing containers are protected.
- Docker's `bridge`, `host`, and `none` networks are always protected.
- Matching protection labels prevent deletion.
- In-use build-cache entries are protected.

## Failure behavior

A failed deletion does not become a global success. The executor records the error and continues
with independently approved operations. `apply` exits non-zero when any operation fails.

`SIGINT` requests a cooperative stop. The current Docker call may finish, but no new deletion is
scheduled, and completed results remain visible.

## Integration-test ownership

Integration tests are disabled by default. When explicitly enabled, they use a unique
`docker-disk-guardian.test-id` label and remove only the container created by that test. They never
pull images automatically or prune user resources.


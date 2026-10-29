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

Integration tests are disabled by default locally. The CI integration job prepares a digest-pinned
image on a disposable runner, then explicitly enables the tests. Tests use unique UUID names and
`docker-disk-guardian.test-id` labels and remove only their own container/volume objects. They never
pull images automatically or prune unrelated resources. Inventory, default volume protection and
explicitly opted-in targeted volume deletion are covered; full concurrent-daemon behavior is not.


## Volume provenance and remaining races

Docker volume names do not establish whether a user named the volume. The SDK adapter therefore reports every discovered volume as non-anonymous, including 64-character hexadecimal names. Default policy protects these volumes; deletion requires the existing named-volume opt-in and all other checks. The `anonymous` model field remains for compatibility, not as a name-based safety assertion.

The post-confirmation inventory narrows, but does not eliminate, races before individual removal calls. Network reference completeness, particularly stopped-container associations, still needs focused Docker integration evidence. Removing resources has no undo operation.

Expected SDK inventory failures are translated to exit code 3 with an actionable message instead of leaking raw daemon responses.

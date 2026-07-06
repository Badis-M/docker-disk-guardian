# ADR 0001: Separate Docker access from domain decisions

- Status: Accepted
- Date: 2026-08-27

## Context

Docker API responses are untyped dictionaries tied to daemon capabilities. Passing them through
the application would couple policy evaluation, reporting, and execution to the SDK.

## Decision

The Docker SDK is isolated behind a typed boundary. Inventory converts API responses into domain
models. Planning consumes only domain models and policies, while execution receives validated
operations.

## Consequences

- Unit tests can use in-memory fakes without a Docker daemon.
- SDK compatibility logic stays at the system boundary.
- New resource types require explicit domain and adapter changes.


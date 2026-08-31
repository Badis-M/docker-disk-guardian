# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `doctor` command for a fast, read-only Docker connectivity check.

## [1.0.0] - 2026-08-27

### Added

- Read-only inventory for containers, images, volumes, networks, and build cache.
- Strict versioned YAML policies with bounded safe loading.
- Explainable cleanup candidates, retained resources, and protection reasons.
- Table, JSON, and Markdown inventory and plan reports.
- Confirmed `apply` workflow with current-state revalidation.
- Explicit success, failure, skip, and interruption results.
- Isolated opt-in Docker integration tests and GitHub Actions CI.

### Security

- Running containers and referenced resources are always protected.
- Docker default networks cannot become deletion candidates.
- Named volumes and build cache are protected by default.
- Targeted build-cache deletion remains disabled because prune scope cannot be guaranteed.

[1.0.0]: https://github.com/Badis-M/docker-disk-guardian/releases/tag/v1.0.0

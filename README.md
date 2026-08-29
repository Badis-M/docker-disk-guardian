# Docker Disk Guardian

[![CI](https://github.com/Badis-M/docker-disk-guardian/actions/workflows/ci.yml/badge.svg)](https://github.com/Badis-M/docker-disk-guardian/actions/workflows/ci.yml)

Docker Disk Guardian is a safety-first Python CLI for understanding local Docker disk usage,
planning policy-based cleanup, and applying only explicitly approved operations.

## Safety guarantees

- `inspect` and `plan` never modify Docker.
- `apply` requires a reviewed policy and confirmation unless `--yes` is explicit.
- Candidates are recalculated from current daemon state immediately before deletion.
- Running containers, referenced resources, and Docker default networks are protected.
- Named volumes and build cache are protected by default.
- Every decision includes a human-readable reason.
- Partial failures and skipped operations remain visible.

Review the complete [safety model](docs/safety-model.md) before enabling automated cleanup.

## Requirements

- Python 3.12 or newer
- A local Docker Engine or compatible Docker socket

No cloud account is required.

## Installation

From a local clone:

```bash
python3 -m venv .venv
.venv/bin/pip install .
```

For development:

```bash
.venv/bin/pip install -e '.[dev]'
make check
```

## Usage

Inspect all supported resources:

```bash
docker-disk-guardian inspect
```

Export a read-only inventory:

```bash
docker-disk-guardian inspect --format json --output inventory.json
```

Validate and review a cleanup policy:

```bash
docker-disk-guardian policy validate examples/policy.yaml
docker-disk-guardian plan --policy examples/policy.yaml
```

Apply the reviewed policy interactively:

```bash
docker-disk-guardian apply --policy examples/policy.yaml
```

`--yes` is intended only for automation where the generated plan is already understood:

```bash
docker-disk-guardian apply --policy examples/policy.yaml --yes
```

Reports support `table`, `json`, and `markdown` formats. JSON output has an explicit schema version
and deterministic ordering for automation and review.

## Resource support

| Resource | Inspect | Plan | Apply |
|---|:---:|:---:|:---:|
| Containers | Yes | Yes | Yes |
| Images | Yes | Yes | Yes |
| Volumes | Yes | Yes | Policy opt-in |
| Networks | Yes | Yes | Policy opt-in |
| Build cache | Yes | Yes | Report-only in V1 |

Targeted build-cache removal is intentionally not executed because Docker's prune endpoint can
affect resources beyond a single reviewed cache entry.

## Documentation

- [Policy reference](docs/policy-reference.md)
- [Safety model](docs/safety-model.md)
- [Examples](docs/examples.md)
- [Architecture decisions](docs/adr/)

## License

MIT

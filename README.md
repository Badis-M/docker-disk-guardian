# Docker Disk Guardian

[![CI](https://github.com/Badis-M/docker-disk-guardian/actions/workflows/ci.yml/badge.svg)](https://github.com/Badis-M/docker-disk-guardian/actions/workflows/ci.yml)

Docker Disk Guardian is a safety-first Python CLI for understanding local Docker disk usage,
planning policy-based cleanup, and applying only explicitly approved operations.

## Safety guarantees

- `inspect` and `plan` never modify Docker.
- `apply` requires a reviewed policy and confirmation unless `--yes` is explicit.
- Candidates are recalculated from current daemon state immediately before deletion.
- Running containers, referenced resources, and Docker default networks are protected.
- All discovered volumes and build cache are protected by default; a hexadecimal name does not prove anonymous creation.
- Every decision includes a human-readable reason.
- Partial failures and skipped operations remain visible.

Review the complete [safety model](docs/safety-model.md) before enabling automated cleanup.

## Requirements

- Python 3.12 or newer
- A local Docker Engine or compatible Docker socket

No cloud account is required. Policy-file validation currently uses POSIX file-opening protections (Linux/macOS); Windows support is not claimed or included in CI.

## Installation

From a local clone:

```bash
python3 -m venv .venv
.venv/bin/pip install .
```

For development:

```bash
uv sync --locked --extra dev --group build --group security --python 3.12
make check coverage
```

## Usage

Check that Docker is reachable before running an inventory:

```bash
docker-disk-guardian doctor
```

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

## Agent context, validation and delivery

- Read [agent.md](agent.md) and the applicable repository instructions before making changes.
- [docs/VALIDATION.md](docs/VALIDATION.md) records dated results and remaining limits.
- [docs/RELEASE.md](docs/RELEASE.md) explains CI, artifact checks and explicitly authorized manual publication.
- The French `contexte.md` guide is local and ignored by Git; it is intentionally absent from clones and distributions.

A normal push to `main` runs CI but does not publish a release. Existing GitHub runs describe earlier commits and do not validate the current uncommitted changes.

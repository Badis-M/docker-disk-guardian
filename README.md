# Docker Disk Guardian

Docker Disk Guardian is a safety-first Python CLI for understanding local Docker disk usage,
planning policy-based cleanup, and applying only explicitly approved operations.

> The project is under active development. Destructive commands are not available yet.

## Requirements

- Python 3.12 or newer
- A local Docker Engine or compatible Docker socket

## Development setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

## License

MIT


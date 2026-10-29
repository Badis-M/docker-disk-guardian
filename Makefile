.PHONY: install format lint typecheck test coverage check quality build audit

UV ?= uv
RUN = $(UV) run --locked --extra dev

install:
	$(UV) sync --locked --extra dev --group build --group security

format:
	$(RUN) ruff check --fix .
	$(RUN) ruff format .

lint:
	$(RUN) ruff format --check .
	$(RUN) ruff check .

typecheck:
	$(RUN) mypy src

test:
	$(RUN) pytest -m 'not integration'

coverage:
	$(RUN) pytest -m 'not integration' --cov=docker_disk_guardian --cov-report=term-missing --cov-fail-under=80

check: lint typecheck test
quality: check

build:
	$(UV) run --locked --group build python -m build --no-isolation
	$(UV) run --locked --group build twine check dist/*

audit:
	@report=$$(mktemp); trap 'rm -f "$$report"' EXIT; \
	$(UV) export --locked --no-dev --no-emit-project --format requirements-txt --output-file "$$report" > /dev/null && \
	$(UV) run --locked --group security pip-audit --require-hashes --disable-pip -r "$$report"

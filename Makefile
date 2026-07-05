.PHONY: install format lint typecheck test check

install:
	python3 -m pip install -e '.[dev]'

format:
	ruff format .
	ruff check --fix .

lint:
	ruff format --check .
	ruff check .

typecheck:
	mypy src

test:
	pytest

check: lint typecheck test


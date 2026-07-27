.PHONY: install lint reformat test-local fetch-spec

install:
	uv pip install -U -e ".[dev]"

lint:
	uv run ruff check .
	uv run ty check || true

reformat:
	uv run ruff format .
	uv run ruff check --fix .

test-local:
	uv run pytest -q

fetch-spec:
	python scripts/fetch_spec.py

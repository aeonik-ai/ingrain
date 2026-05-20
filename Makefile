.PHONY: install test lint check eval clean

install:
	pip install -e ".[dev]"

test:
	PYTHONPATH=src python -m unittest discover -s tests -v

lint:
	@command -v ruff >/dev/null 2>&1 && ruff check src tests || echo "(ruff not installed — skipping lint)"

check: lint test

# LES-Core regression gate. Deterministic. No LLM. No network.
eval:
	ingrain eval

# LES-Hard self-eval. Local, scenario-based. No LLM. No network.
les-hard:
	ingrain les-hard

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info
	find . -name __pycache__ -type d -exec rm -rf {} +

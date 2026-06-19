.PHONY: install test lint demo clean

install:
	python -m pip install -e ".[dev]"

test:
	pytest --cov=quality_monitor --cov-report=term-missing

lint:
	ruff check .

demo:
	quality-monitor generate --rows 3000 --output data/production_data.csv
	quality-monitor analyse --input data/production_data.csv --output-dir artifacts --method robust-z

clean:
	rm -rf artifacts .pytest_cache .ruff_cache .coverage htmlcov

.PHONY: help test unit-test lint format coverage pre-commit install install-hooks configure clean

help: ## Show this help message
	@echo "Available make tasks:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

test: ## Run all tests (lint + unit tests)
	tox

unit-test: ## Run unit tests only
	tox -e py312

lint: ## Run linting checks (black + flake8)
	tox -e lint

format: ## Format code with black and check with flake8
	tox -e format

coverage: ## Run unit tests with coverage report
	python run_tests --cov=. --cov-report=html --cov-report=term

pre-commit: format lint unit-test ## Run pre-commit checks (format + lint + test)

install: ## Install development dependencies
	pip install -r requirements-dev.txt

install-hooks: ## Install git hooks
	git config core.hooksPath .githooks
	@echo "✓ Git hooks installed"

configure: install install-hooks ## Install dependencies and git hooks
	@echo "✓ Project configured"

clean: ## Clean up build artifacts and cache
	rm -rf .tox
	rm -rf *.egg-info
	rm -rf htmlcov
	rm -f .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

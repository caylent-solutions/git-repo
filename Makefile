.PHONY: help test unit-test lint lint-python lint-markdown lint-yaml format format-python format-markdown format-yaml coverage pre-commit install install-hooks configure clean

help: ## Show this help message
	@echo "Available make tasks:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

test: ## Run all tests (lint + unit tests)
	tox

unit-test: ## Run unit tests only
	tox -e py312

lint: lint-python lint-markdown lint-yaml ## Run all linting checks

lint-python: ## Run Python linting (ruff)
	ruff check .

lint-markdown: ## Run Markdown linting (pymarkdown)
	pymarkdown --config .pymarkdown.yml scan -e claude-plugin-marketplace-spec.md -e docs/release-process.md '**/*.md'

lint-yaml: ## Run YAML linting (yamlfix)
	yamlfix --check .

format: format-python format-markdown format-yaml ## Format all code

format-python: ## Format Python code (ruff)
	ruff format .

format-markdown: ## Format Markdown files (pymarkdown)
	pymarkdown --config .pymarkdown.yml fix '**/*.md'

format-yaml: ## Format YAML files (yamlfix)
	yamlfix .

coverage: ## Run unit tests with coverage report
	python run_tests --cov=. --cov-report=html --cov-report=term

pre-commit: format lint unit-test ## Run pre-commit checks (format + lint + test)

install: ## Install development dependencies
	pip install -r requirements-dev.txt

install-hooks: ## Install git hooks
	git config core.hooksPath .githooks
	@echo "Git hooks installed"

configure: install install-hooks ## Install dependencies and git hooks
	@echo "Project configured"

clean: ## Clean up build artifacts and cache
	rm -rf .tox
	rm -rf .ruff_cache
	rm -rf *.egg-info
	rm -rf htmlcov
	rm -f .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

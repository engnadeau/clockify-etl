.DEFAULT_GOAL := all

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Variables

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# PHONY Targets

.PHONY: all
all: secrets lint

.PHONY: lint
lint:
	poetry run black --check .
	poetry run isort -c .
	poetry run ruff check .

.PHONY: format
format:
	poetry run black .
	poetry run isort .
	poetry run ruff --fix .

.PHONY: secrets
secrets: .secrets.toml

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# File Targets

.secrets.toml: .secrets.example.toml
	cp -f $< $@

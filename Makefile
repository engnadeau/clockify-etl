.DEFAULT_GOAL := all

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# PHONY Targets

.PHONY: all
all: clean build

.PHONY: clean
clean:
	-rm -rf build

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

.PHONY: build
build:
	poetry run python src/main.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# File Targets

.secrets.toml: .secrets.example.toml
	cp -f $< $@

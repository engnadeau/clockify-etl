.DEFAULT_GOAL := all

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Variables

MONTHS_BACK := 3
TODAY := $(shell date +%Y-%m-%d)
START_DATE := $(shell date -d "$(TODAY) -$(MONTHS_BACK) months" +%Y-%m-01)

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
	poetry run \
		python \
		src/main.py \
		--start-date $(START_DATE) \
		--end-date $(TODAY)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# File Targets

.secrets.toml: .secrets.example.toml
	cp -f $< $@

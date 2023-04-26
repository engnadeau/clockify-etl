.DEFAULT_GOAL := all

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Variables

TODAY := $(shell date +%Y-%m-%d)
DAYS_BACK := 90

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# PHONY Targets

.PHONY: all
all: timesheets

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

.PHONY: timesheets
timesheets:
	PYTHONPATH='src' \
	poetry run \
		luigi \
		--module main RangeDaily \
		--of AllReports \
		--local-scheduler \
		--stop $(TODAY) \
		--reverse \
		--task-limit $(DAYS_BACK) \
		--days-back $(DAYS_BACK)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# File Targets

.secrets.toml: .secrets.example.toml
	cp -f $< $@

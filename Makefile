run:
	python -m sim_framework.main --local

test:
	echo "No tests implemented yet"

lint:
	flake8 sim_framework

update:
	pip list --outdated

ZIP_DIRS ?= .
ZIP_DIRTY ?= false
ZIP_ROOT := $(shell git rev-parse --show-toplevel)
ZIP_NAME := $(shell basename "$(ZIP_ROOT)")_$(shell date -u +%Y%m%d_%H%M%S).zip
ZIP_OUT := $(ZIP_ROOT)/snapshots/$(ZIP_NAME)

.PHONY: zip zip_all warn_git_status

zip: warn_git_status
ifeq ($(ZIP_DIRTY),true)
	@echo "Creating zip (all files): $(ZIP_OUT)"
	@mkdir -p "$(ZIP_ROOT)/snapshots"
	@zip -r "$(ZIP_OUT)" $(ZIP_DIRS) -x '*.git*'
else
	@echo "Creating zip (only tracked files): $(ZIP_OUT)"
	@mkdir -p "$(ZIP_ROOT)/snapshots"
	@git ls-files -z | xargs -0 zip "$(ZIP_OUT)"
endif

zip_all:
	$(MAKE) zip ZIP_DIRTY=true

warn_git_status:
	@if [ -n "$$(git ls-files --others --exclude-standard)" ]; then \
		echo "Warning: untracked files present."; \
	fi
	@if ! git diff --quiet || ! git diff --cached --quiet; then \
		echo "Warning: uncommitted changes present."; \
	fi

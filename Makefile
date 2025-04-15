.PHONY: build run test clean logs-clean validate-project lint \
		scrape-docs zip zip_all warn_git_status

LOG_DIR := logs
LOG_FILE := logs/$(shell date -u +%Y%m%d_%H%M%S)_$(MAKECMDGOALS).log

build:
	@mkdir -p $(LOG_DIR)
	@{ \
		echo "==== Build started: $$(date -u) ===="; \
		echo "[1/3] Running clean..."; \
		$(MAKE) clean; \
		echo "[2/3] Running validate-project..."; \
		$(MAKE) validate-project; \
		echo "[3/3] Running lint..."; \
		$(MAKE) lint || echo "Lint failed (non-blocking)"; \
		echo "==== Build finished: $$(date -u) ===="; \
	} 2>&1 | tee $(LOG_FILE)
	@echo "Build complete. Log written to $(LOG_FILE)"

run:
	@mkdir -p logs
	@echo "Running project... (logging to $(LOG_FILE))"
	@python -m sim_framework.main --local 2>&1 | tee $(LOG_FILE)

test:
	echo "No tests implemented yet"

clean:
	@echo "Cleaning build artifacts..."
	@rm -f docs/raw/*.raw.html || true
	@rm -f snapshots/*.zip || true
	@find . -name '__pycache__' -type d -exec rm -rf {} +
	@find . -name '*.pyc' -delete
	@find . -name '*.pyo' -delete
	@find . -name '*.DS_Store' -delete
	@echo "Clean complete."

logs-clean:
	@echo "Removing old log files..."
	@rm -f logs/*.log
	@echo "Log cleanup complete."


validate-project:
	@echo "Validating project metadata..."
	@python3 scripts/validate_project.py || (echo "Project validation failed."; exit 1)

lint:
	flake8 sim_framework

scrape-docs:
	@python3 scripts/scrape_docs.py

ZIP_DIRS ?= .
ZIP_DIRTY ?= false
ZIP_ROOT := $(shell git rev-parse --show-toplevel)
ZIP_NAME := $(shell basename "$(ZIP_ROOT)")_$(shell date -u +%Y%m%d_%H%M%S).zip
ZIP_OUT := $(ZIP_ROOT)/snapshots/$(ZIP_NAME)

LATEST_BUILD_LOG := $(shell ls -1t $(ZIP_ROOT)/logs/build_*.log 2>/dev/null | head -n 1)
LATEST_RUN_LOG   := $(shell ls -1t $(ZIP_ROOT)/logs/run_*.log   2>/dev/null | head -n 1)

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

ifneq ($(strip $(LATEST_BUILD_LOG)),)
	@echo "Including latest build log as build.log"
	@cp "$(LATEST_BUILD_LOG)" "$(ZIP_ROOT)/build.log"
	@zip "$(ZIP_OUT)" "$(ZIP_ROOT)/build.log"
	@rm "$(ZIP_ROOT)/build.log"
endif

ifneq ($(strip $(LATEST_RUN_LOG)),)
	@echo "Including latest run log as run.log"
	@cp "$(LATEST_RUN_LOG)" "$(ZIP_ROOT)/run.log"
	@zip "$(ZIP_OUT)" "$(ZIP_ROOT)/run.log"
	@rm "$(ZIP_ROOT)/run.log"
endif

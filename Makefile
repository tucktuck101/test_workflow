VENV?=.venv
PYTHON?=$(VENV)/bin/python
PIP?=$(PYTHON) -m pip
FRONTEND_DIR?=frontend
CONFIG?=configs/dqn_train.yaml

.PHONY: setup backend-test backend-typecheck backend-coverage frontend-install frontend-test load-test lint train train-smoke

setup:
	python -m venv $(VENV)
	$(PIP) install -r requirements.txt
	cd $(FRONTEND_DIR) && npm install

backend-test:
	$(PYTHON) -m pytest -q

backend-typecheck:
	mypy .

backend-coverage:
	$(PYTHON) -m pytest --cov=app --cov=tests --cov-fail-under=90

frontend-install:
	cd $(FRONTEND_DIR) && npm install

frontend-test:
	cd $(FRONTEND_DIR) && npm test -- --coverage --watch=false

load-test:
	k6 run load_tests/k6_load.js

smoke:
	./scripts/smoke.sh

train-smoke:
	./scripts/train_smoke.sh

train:
	@if [ ! -f "$(CONFIG)" ]; then \
		echo "Config file '$(CONFIG)' not found. Override with CONFIG=<path> or create the default."; \
		exit 1; \
	fi
	@RC=0; \
	$(PYTHON) -m training.dqn_selfplay --config "$(CONFIG)" || RC=$$?; \
	$(PYTHON) scripts/plot_dqn_metrics.py || true; \
	exit $$RC

run:
	docker compose up --build

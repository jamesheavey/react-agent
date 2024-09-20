VENV := venv
PYTHON := python3
PIP := pip
OC := oc
FASTAPI_PORT := 8000
CHAINLIT_PORT := 8001

default: help

help:
	@echo "Please use 'make <target>' where <target>' is one of"
	@echo "  setup           to create a virtual environment"
	@echo "  start-ui        to start the FastAPI server and Chainlit server within the virtual environment"
	@echo "  start           to start only the FastAPI server"
	@echo "  create-db       run script to create collection and upload data."
	@echo "  test-api        run API tests using pytest"

.PHONY: check-python-version
check-python-version:
	@$(PYTHON) -c 'import sys; sys.exit("\033[31mPython 3.11 or higher is required to run this project. Please ensure that `python3` is pointing at a valid python version\033[0m" if sys.version_info < (3, 11) else 0)' || exit 1

.PHONY: setup
setup: check-python-version
	$(PYTHON) -m venv $(VENV)
	@echo "Virtual environment created."
	@echo "Installing dependencies in api..."
	@. $(VENV)/bin/activate && cd api && $(PIP) install --no-cache-dir --upgrade -r requirements.txt
	@echo "Installing dependencies in ui..."
	@. $(VENV)/bin/activate && cd ui && $(PIP) install --no-cache-dir --upgrade -r requirements.txt

.PHONY: start-api
start-api: check-python-version
	@echo "Starting \033[34mFastAPI\033[0m server..."
	@. $(VENV)/bin/activate && cd api && uvicorn main:app --reload --port $(FASTAPI_PORT)

.PHONY: start-ui
start-ui: check-python-version
	@echo "Starting \033[31mChainlit\033[0m server..."
	@. $(VENV)/bin/activate && cd ui && chainlit run app.py -w --port $(CHAINLIT_PORT)

.PHONY: start
start: check-python-version
	@echo "Starting \033[34mFastAPI\033[0m and \033[31mChainlit\033[0m servers..."
	@source .env && \
	. $(VENV)/bin/activate && cd api && uvicorn main:app --reload --port $(FASTAPI_PORT) & \
	. $(VENV)/bin/activate && cd ui && chainlit run app.py -w --port $(CHAINLIT_PORT) & \
	wait

.PHONY: create-db
create-db: check-python-version
	@. $(VENV)/bin/activate && python3 scripts/create_db.py
	wait
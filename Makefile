PROJECT_DIR = $(shell pwd)
VENV_DIR = $(PROJECT_DIR)/.venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip

.PHONY: install start backend frontend stop clean venv

## Create venv if it doesn't exist
venv:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv $(VENV_DIR); \
		echo "venv created at $(VENV_DIR)"; \
	else \
		echo "venv already exists."; \
	fi

## Install all dependencies (Python + Node)
install: venv
	@echo "Installing Python dependencies..."
	$(PIP) install -r $(PROJECT_DIR)/requirements.txt
	@echo ""
	@echo "Installing Remotion dependencies..."
	cd $(PROJECT_DIR)/remotion-video && npm install
	@echo ""
	@echo "Installing frontend dependencies..."
	cd $(PROJECT_DIR)/frontend && npm install
	@echo ""
	@echo "Done! Make sure you have:"
	@echo "  1. GEMINI_API_KEY in ../.env"
	@echo "  2. reference_voice.wav in assets/"

## Start both backend and frontend
start: backend frontend

## Start backend only (port 8000)
backend:
	@echo "Starting backend on http://localhost:8000 ..."
	cd $(PROJECT_DIR) && $(PYTHON) server.py &

## Start frontend only (port 5173)
frontend:
	@echo "Starting frontend on http://localhost:5173 ..."
	cd $(PROJECT_DIR)/frontend && npm run dev &

## Stop all running servers
stop:
	@-pkill -f "python server.py" 2>/dev/null || true
	@-pkill -f "vite" 2>/dev/null || true
	@echo "Stopped all servers."

## Run pipeline directly via CLI
run:
	@echo "Usage: make run SRC=path/to/manual.pdf"
	@test -n "$(SRC)" || (echo "Error: SRC is required" && exit 1)
	cd $(PROJECT_DIR) && $(PYTHON) pipeline.py "$(SRC)"

## Clean temp and output files
clean:
	@echo "Cleaning temp and output files..."
	@-find $(PROJECT_DIR)/temp -type f -not -name '.gitkeep' -delete 2>/dev/null || true
	@-find $(PROJECT_DIR)/outputs -type f -not -name '.gitkeep' -delete 2>/dev/null || true
	@echo "Done."

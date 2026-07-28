VENV_DIR := .venv
STAMP    := $(VENV_DIR)/.installed

ifeq ($(OS),Windows_NT)
    PYTHON   := python
    VENV_PY  := $(VENV_DIR)/Scripts/python.exe
    VENV_PIP := $(VENV_DIR)/Scripts/pip.exe
    VENV_ACTIVATE := $(VENV_DIR)/Scripts/activate
    RM_RF    := $(PYTHON) -c "import shutil,sys; shutil.rmtree(sys.argv[1], ignore_errors=True)"
    TOUCH    := $(PYTHON) -c "import pathlib,sys; pathlib.Path(sys.argv[1]).touch()"
else
    PYTHON   := python3
    VENV_PY  := $(VENV_DIR)/bin/python
    VENV_PIP := $(VENV_DIR)/bin/pip
    VENV_ACTIVATE := $(VENV_DIR)/bin/activate
    RM_RF    := rm -rf
    TOUCH    := touch
endif

.PHONY: all setup clean run

all: setup

# Create the venv only if it doesn't already exist
$(VENV_ACTIVATE):
	$(PYTHON) -m venv $(VENV_DIR)

# Re-run pip install only if requirements.txt changed since the last install
$(STAMP): requirements.txt $(VENV_ACTIVATE)
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements.txt
	$(TOUCH) $(STAMP)

setup: $(STAMP)
	./setup.sh

run:
	$(VENV_PY) src/main.py

clean:
	$(RM_RF) $(VENV_DIR)
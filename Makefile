VENV_DIR := .venv
PYTHON   := python3
VENV_PY  := $(VENV_DIR)/bin/python
VENV_PIP := $(VENV_DIR)/bin/pip
STAMP    := $(VENV_DIR)/.installed

.PHONY: all setup clean

all: setup

# Create the venv only if it doesn't already exist
$(VENV_DIR)/bin/activate:
	$(PYTHON) -m venv $(VENV_DIR)

# Re-run pip install only if requirements.txt changed since the last install
$(STAMP): requirements.txt $(VENV_DIR)/bin/activate
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements.txt
	touch $(STAMP)

setup: $(STAMP)

clean:
	rm -rf $(VENV_DIR)
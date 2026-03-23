PYTHON := python
SRC := bot migrations tests

.PHONY: help lint lint-ruff lint-mypy lint-pyright audit semgrep fmt fmt-check test deploy logs status restart

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "  lint        Run all linters (ruff + mypy + pyright)"
	@echo "  lint-ruff   Run ruff linter"
	@echo "  lint-mypy   Run mypy type checker"
	@echo "  lint-pyright Run pyright type checker"
	@echo "  audit       Run pip-audit for dependency vulnerabilities"
	@echo "  semgrep     Run semgrep static analysis"
	@echo "  fmt         Auto-format code with ruff"
	@echo "  fmt-check   Check formatting without writing"
	@echo "  test        Run test suite"
	@echo "  deploy      Rsync to server and restart bot"
	@echo "  logs        Tail bot logs on server"
	@echo "  status      Show bot service status"
	@echo "  restart     Restart bot on server"

# --- Linting ---

lint: lint-ruff lint-mypy lint-pyright

lint-ruff:
	$(PYTHON) -m ruff check $(SRC)

lint-mypy:
	$(PYTHON) -m mypy $(SRC) --ignore-missing-imports --explicit-package-bases

lint-pyright:
	$(PYTHON) -m pyright $(SRC)

# --- Security ---

audit:
	$(PYTHON) -m pip_audit .

semgrep:
	semgrep scan --config auto $(SRC)

# --- Formatting ---

fmt:
	$(PYTHON) -m ruff format $(SRC)
	$(PYTHON) -m ruff check $(SRC) --fix

fmt-check:
	$(PYTHON) -m ruff format $(SRC) --check
	$(PYTHON) -m ruff check $(SRC)

# --- Testing ---

test:
	$(PYTHON) -m pytest tests/ -v

# --- Server ---

# --- Server (cp .env.deploy.example .env.deploy and fill in) ---

-include .env.deploy

DEPLOY_HOST  ?= your-server-ip
DEPLOY_USER  ?= tginvitebot
DEPLOY_DIR   ?= /home/$(DEPLOY_USER)/TgInviteBot
SSH_KEY      ?= ~/.ssh/id_ed25519
SSH          := ssh -i $(SSH_KEY) $(DEPLOY_USER)@$(DEPLOY_HOST)

deploy:
	rsync -av --exclude-from=.rsyncignore \
		-e "ssh -i $(SSH_KEY)" \
		. $(DEPLOY_USER)@$(DEPLOY_HOST):$(DEPLOY_DIR)/
	$(SSH) sudo systemctl restart tgbot
	@echo "Deployed and restarted."

logs:
	$(SSH) journalctl -u tgbot -f

status:
	$(SSH) systemctl status tgbot --no-pager

restart:
	$(SSH) sudo systemctl restart tgbot

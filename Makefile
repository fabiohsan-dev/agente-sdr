# ============================================
# SDR Agent - Makefile
# ============================================
# Para Windows, use os scripts .bat em infra/scripts/
# Este Makefile é para Linux/Mac ou WSL

.PHONY: help setup install run-api run-playground test clean

# Variáveis
PYTHON = python
PIP = pip
UVICORN = uvicorn
PYTEST = pytest

# Default target
help:
	@echo "SDR Agent - Comandos disponíveis:"
	@echo ""
	@echo "  make setup           - Configura ambiente virtual e instala dependências"
	@echo "  make install         - Instala dependências (ambiente já ativado)"
	@echo "  make run-api         - Roda API em http://127.0.0.1:8000"
	@echo "  make run-playground  - Roda Playground em http://127.0.0.1:8001"
	@echo "  make test            - Roda testes"
	@echo "  make clean           - Limpa arquivos temporários"
	@echo ""

# Setup inicial
setup:
	@echo "Criando ambiente virtual..."
	$(PYTHON) -m venv .venv
	@echo "Ativando ambiente e instalando dependências..."
	. .venv/bin/activate && $(PIP) install --upgrade pip && $(PIP) install -e .
	@echo "Setup concluído!"
	@echo ""
	@echo "IMPORTANTE: Copie .env.example para .env e configure as variáveis"

# Instalar dependências
install:
	$(PIP) install --upgrade pip
	$(PIP) install -e .

# Rodar API
run-api:
	. .venv/bin/activate && $(UVICORN) apps.api.main:app --host 127.0.0.1 --port 8000 --reload

# Rodar Playground
run-playground:
	. .venv/bin/activate && $(UVICORN) apps.playground.server:app --host 127.0.0.1 --port 8001 --reload

# Rodar testes
test:
	. .venv/bin/activate && $(PYTEST) tests/ -v

# Rodar testes com coverage
test-cov:
	. .venv/bin/activate && $(PYTEST) tests/ -v --cov=app --cov-report=html

# Limpar arquivos temporários
clean:
	@echo "Limpando arquivos temporários..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage
	@echo "Limpeza concluída!"

# Verificar código (lint)
lint:
	. .venv/bin/activate && python -m ruff check app/ apps/

# Type check
type-check:
	. .venv/bin/activate && python -m mypy app/ apps/

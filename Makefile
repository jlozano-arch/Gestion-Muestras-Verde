.PHONY: help install run test clean seed docker-build docker-up docker-down lint

help:
	@echo "Gestión de Muestras de Café Verde - Indian Ecotrade"
	@echo ""
	@echo "Comandos disponibles:"
	@echo "  make install       - Instalar dependencias"
	@echo "  make run           - Ejecutar aplicación en desarrollo"
	@echo "  make test          - Ejecutar tests"
	@echo "  make seed          - Cargar datos iniciales"
	@echo "  make clean         - Limpiar archivos temporales"
	@echo "  make docker-build  - Construir imagen Docker"
	@echo "  make docker-up     - Levantar contenedores"
	@echo "  make docker-down   - Parar contenedores"
	@echo "  make lint          - Verificar código"

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --tb=short

seed:
	python scripts/seed.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

lint:
	python -m py_compile app/*.py tests/*.py scripts/*.py

.DEFAULT_GOAL := help

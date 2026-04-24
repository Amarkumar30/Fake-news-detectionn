PYTHON ?= python
NPM ?= npm

.PHONY: install ensure-models train dev test build clean

install:
	$(PYTHON) -m pip install -r backend/requirements.txt && cd frontend && $(NPM) install

ensure-models:
	@if ls backend/models/*.pkl >/dev/null 2>&1; then \
		echo "Using existing trained model artifacts."; \
	else \
		echo "No trained model artifacts found. Running backend/train.py..."; \
		cd backend && $(PYTHON) train.py --data-dir ../data; \
	fi

train:
	cd backend && $(PYTHON) train.py --data-dir ../data

dev: ensure-models
	cd frontend && npx concurrently --kill-others-on-fail --names "flask,vite" "cd ../backend && FLASK_ENV=development FLASK_PORT=5000 $(PYTHON) app.py" "$(NPM) run dev"

test:
	$(PYTHON) -m pytest tests backend/tests -q && cd frontend && $(NPM) run test

build:
	cd frontend && $(NPM) run build

clean:
	-$(PYTHON) -c "import pathlib, shutil; [shutil.rmtree(path, ignore_errors=True) for path in pathlib.Path('.').rglob('__pycache__')]"
	-$(PYTHON) -c "import shutil; [shutil.rmtree(path, ignore_errors=True) for path in ['frontend/node_modules', 'frontend/dist']]"
	-$(PYTHON) -c "import shutil; [shutil.rmtree(path, ignore_errors=True) for path in ['.pytest_cache', '.pytest_cache_local', '.pytest_tmp', 'backend/logs']]"

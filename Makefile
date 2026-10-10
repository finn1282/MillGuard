PY=.venv/bin/python
.PHONY: setup fixtures api all roi
setup:
	uv venv --python 3.11 .venv && uv pip install --python $(PY) -r backend/requirements.txt
fixtures:
	$(PY) -m backend.api.make_fixtures
api:
	$(PY) -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
all:
	$(PY) -m backend.run_all
roi:
	$(PY) -m backend.scripts.roi
fetch-metropt:
	mkdir -p backend/data/metropt && curl -L -C - --retry 20 -o backend/data/metropt/metropt3.zip "https://archive.ics.uci.edu/static/public/791/metropt+3+dataset.zip"
	$(PY) -m backend.scripts.fetch_metropt

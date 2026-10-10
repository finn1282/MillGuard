PY=.venv/bin/python
.PHONY: setup fixtures api all
setup:
	uv venv --python 3.11 .venv && uv pip install --python $(PY) -r backend/requirements.txt
fixtures:
	$(PY) -m backend.api.make_fixtures
api:
	$(PY) -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
all:
	$(PY) -m backend.run_all

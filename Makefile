PY=.venv/bin/python
.PHONY: pitch demo bot stress setup libomp fixtures api all roi report
setup:
	uv venv --python 3.11 .venv && uv pip install --python $(PY) -r backend/requirements.txt
pitch:
	$(PY) -m backend.scripts.export_pitch
demo:
	sh backend/scripts/demo.sh $(PY)
demo-offline:
	sh backend/scripts/demo_offline.sh
check:
	sh backend/scripts/check.sh $(PY)
demo-all:
	sh backend/scripts/demo_all.sh $(PY)
bot:
	$(PY) -m backend.notify.telegram_bot
stress:
	$(PY) -m backend.robustness.stress
libomp:
	sh backend/scripts/fix_libomp.sh $(PY)
report:
	$(PY) -m backend.scripts.report
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
fetch-boiler:
	$(PY) -m backend.scripts.fetch_boiler

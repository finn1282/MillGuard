PY=.venv/bin/python
.PHONY: vercel-predeploy vercel-deploy set-webhook scenarios live stream pitch demo bot stress setup libomp fixtures api all roi report
setup:
	uv venv --allow-existing --python 3.11 .venv && uv pip install --python $(PY) -r backend/requirements.txt
	@if [ "$$(uname)" = Darwin ]; then $(PY) -c 'import lightgbm' 2>/dev/null || sh backend/scripts/fix_libomp.sh $(PY); fi
pitch:
	$(PY) -m backend.scripts.export_pitch
demo:
	sh backend/scripts/demo.sh $(PY)
live:   # API + polling bot with shared state and auto-notify; stream with `make stream SCENARIO=bad_sensor`
	sh backend/scripts/demo.sh $(PY)
scenarios:
	$(PY) -m backend.gateway.scenarios
stream:
	$(PY) -m backend.scripts.stream --scenario $(or $(SCENARIO),mill10) --speed $(or $(SPEED),2)
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
vercel-predeploy:   # the function reads built artifacts and scenarios (gitignored): build them if missing
	@test -f backend/artifacts/mill10_predictions.parquet || $(MAKE) all
	@test -f backend/artifacts/scenarios/bearing_p3/actions.json || $(MAKE) scenarios
	@for s in mill10 bearing_p3 worm_p1 boiler_water bad_sensor; do test -f backend/artifacts/scenarios/$$s/actions.json || { echo "missing scenario $$s"; exit 1; }; done
vercel-deploy: vercel-predeploy   # production deploy from this folder (uploads the artifacts: .vercelignore replaces .gitignore); needs `vercel login` + `vercel link`
	vercel deploy --prod
set-webhook:   # make set-webhook URL=https://<project>.vercel.app   (needs TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_SECRET); `make set-webhook URL=delete` removes it
	@test -n "$(URL)" || { echo "usage: make set-webhook URL=https://<project>.vercel.app"; exit 1; }
	$(PY) -m backend.scripts.set_webhook $(if $(filter delete,$(URL)),--delete,$(URL)/api/telegram/webhook)

#!/bin/sh
# make check: fixtures, backend tests and a frontend production build. Prints PASS/FAIL per stage.
PY=${1:-.venv/bin/python}
FAIL=0
run() {
    name=$1; shift
    if "$@" > /tmp/millguard_check_$$.log 2>&1; then echo "PASS  $name"; else echo "FAIL  $name"; tail -25 /tmp/millguard_check_$$.log; FAIL=1; fi
}
run "fixture checks (models, summaries, one number per signal, Malay text)" $PY -m backend.api.make_fixtures --check
run "backend tests" $PY -m pytest -q backend/tests
run "frontend production build" sh -c "cd frontend && npm install --no-audit --no-fund && npm run build"
rm -f /tmp/millguard_check_$$.log
[ $FAIL -eq 0 ] && echo "ALL PASS" || { echo "SOME CHECKS FAILED"; exit 1; }

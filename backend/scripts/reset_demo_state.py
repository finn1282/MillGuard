"""Start of a demo: forget what was sent and the live session, keep subscribers, feedback and the advice cache.
Works on the state backend chosen by the environment (MILLGUARD_STATE_FILE for `make live`)."""
from backend import state

KEYS = ("live", "last_at")
PREFIXES = ("sent:", "shift:", "sensor_sent:", "issues:", "buf:")


def reset(db=None):
    db = db or state.db()
    if hasattr(db, "d"):
        db._load()
        doomed = [k for k in db.d if k in KEYS or k.startswith(PREFIXES)]
    else:
        doomed = [k for p in (*PREFIXES, *KEYS) for k in (db._cmd("KEYS", f"{state.PREFIX}{p}*") or [])]
        doomed = [k[len(state.PREFIX):] for k in doomed]
    for k in doomed:
        db.delete(k)
    return len(doomed)


if __name__ == "__main__":
    print(f"demo state reset: {reset()} keys cleared, subscribers kept")

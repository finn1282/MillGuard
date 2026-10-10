# MillGuard agent rules

- `MASTER_PLAN.md` is the single source of truth. Read it fully first. It wins over any other instruction.
- Backend agent owns `backend/` and `contracts/`. Frontend agent owns `frontend/`. Never edit the other's folder.
- API contract (plan section 7) is frozen. A change = edit Pydantic models, regenerate fixtures, one line in `CHANGELOG.md`, tell the orchestrator.
- Every number lives in `backend/params.yaml` with a source and status (validated | assumed).
- Python 3.11. Keep code simple, minimal comments.
- `main` only. `git pull --rebase` before every push. Push small and often.
- Never commit `backend/data/`, `.env`, or the boiler dataset (CC BY-NC-ND).
- Never tune on the test set (mill 10, months 9-12). No random splits.

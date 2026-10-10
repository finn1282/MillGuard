# MillGuard agent rules

- `MASTER_PLAN.md` is the single source of truth; section 16 (overnight v2) overrides earlier sections where they conflict. Task prompts from Zhen/orchestrator that follow section 16 are authorised.
- Backend agent owns `backend/` and `contracts/`. Frontend agent owns `frontend/`. Never edit the other's folder.
- API contract changes are allowed under section 16 with the usual CHANGELOG rule. A change = edit Pydantic models, regenerate fixtures, one line in `CHANGELOG.md`, tell the orchestrator.
- Every number lives in `backend/params.yaml` with a source and status (validated | assumed).
- Python 3.11. Keep code simple, minimal comments.
- `main` only. `git pull --rebase` before every push. Push small and often.
- Never commit `backend/data/`, `.env`, or the boiler dataset (CC BY-NC-ND).
- Never tune on the test set (mill 10, months 9-12). No random splits.

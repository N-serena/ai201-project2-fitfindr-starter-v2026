# Plan — FitFindr (AI201 Project 2)

Unit 3 builds the agent; unit 4 tests it. Milestone details live in `RUNNING.md`.

## Contracts

Fixed by the starter; later steps implement against these.

- `search_listings(description: str, size: str | None, max_price: float | None) -> list[dict]`
  — `[]` on no match, at most `config.SEARCH_RESULT_LIMIT`, best first.
- `suggest_outfit(new_item: dict, wardrobe: dict) -> str` — never empty; empty
  wardrobe gets general styling advice.
- `create_fit_card(outfit: str, new_item: dict) -> str` — 2–4 sentences; empty
  outfit gets a descriptive message.
- `run_agent(query: str, wardrobe: dict) -> dict` — the session from
  `agent.new_session`; `error` set when the run stops early.

## Unit 3 — the build

| # | Step | Status |
|---|---|---|
| 0 | `docs/PLAN.md`, `docs/DECISIONS.md` | done |
| 1 | Tool Inventory in README (Milestone 2) | done |
| 2 | `criteria.md` — reasons for 1–2, write 3–5 (Milestone 3) | done |
| 3 | `search_listings` | done |
| 4 | `suggest_outfit` — needs `GEMINI_API_KEY` | done |
| 5 | `create_fit_card` — needs `GEMINI_API_KEY` | done |
| 6 | `run_agent` — parse, branch, session (Milestone 5) | done |
| 7 | README write-up (Milestone 6) | done |

Order: 1 → 2 must land before any tool code, so the commit history shows the
spec and criteria existed before results. 4–5 are blocked until the key is in
`.env`.

## Unit 4 — the test

Unit 3 is complete. Milestones are in `RUNNING.md`.

| # | Step | Status |
|---|---|---|
| 1 | MCP: register `search_listings`, agent calls it via `call_tool` (M1) | done |
| 2 | `trace.step()` per step + `ModelUnavailable` handler; bad-key run (M2) | done |
| 3 | `scenarios.py` for criteria 3–5 — commit before running (M3) | done |
| 4 | `run_eval.py --label before`, score, Run Log — Before (M3) | done |
| 5 | Verdicts and diagnoses (M4) | done |
| 6 | One improvement + `run_eval.py --label after` (M5) | done |
| 7 | What's Still Broken, Loop Trace, MCP note, checklist (M6) | done |

- Criterion 3 is scored from `--trace` output, so the `trace.step()` calls
  must log each tool's `new_item` id.
- `scenarios.py` needs: a repeated matching query (criteria 3 and 4) and an
  empty-wardrobe run tagged criterion 5.

## Open items

- Python 3.14.3 venv (starter wants 3.13); `test.py` passes 9 incl. the live model call.

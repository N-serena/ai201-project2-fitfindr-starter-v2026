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
| 4 | `suggest_outfit` — needs `GEMINI_API_KEY` | todo |
| 5 | `create_fit_card` — needs `GEMINI_API_KEY` | todo |
| 6 | `run_agent` — parse, branch, session (Milestone 5) | todo |
| 7 | README write-up (Milestone 6) | todo |

Order: 1 → 2 must land before any tool code, so the commit history shows the
spec and criteria existed before results. 4–5 are blocked until the key is in
`.env`.

## Unit 4 — the test

Not started. Milestones 1–6 in `RUNNING.md`.

- Criterion 3 is scored from `--trace` output, so the `trace.step()` calls
  must log each tool's `new_item` id.
- `scenarios.py` needs: a repeated matching query (criteria 3 and 4) and an
  empty-wardrobe run tagged criterion 5.

## Open items

- `GEMINI_API_KEY` in `.env` is still the placeholder (`python test.py` fails on it).

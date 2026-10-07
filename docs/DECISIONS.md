# Decisions — FitFindr

Newest first.

## 2026-10-07 — Acceptance criteria 3–5

- **3, state:** compare listing `id`s from the search result, the session and
  each tool's input. The check is an exact match, and the path has no model
  in it, so the target is 5 of 5.
- **4, fit card:** a sentence count, the exact price, the platform name, and a
  distinct first sentence across runs, with a target of 4 of 5. Each of these
  is checked by reading, and the first-sentence check also catches cache or
  temperature mistakes.
- **5, empty wardrobe:** chosen because it is a unit 4 failure mode and
  depends on the model obeying an instruction. The model might invent clothes
  the user doesn't own.

## 2026-10-07 — Tool specs (README Tool Inventory)

- **Size match is word-for-word.** The listing sizes mix formats (`S/M`,
  `US 8.5`, `W30 L30`, `XL (oversized)`), so a substring test would match
  `s` in `us 9` and `l` in `xl`. Splitting both sides into words and comparing
  exact words avoids that. "One Size" listings match any size because they
  are mostly accessories that fit anyone.
- **Search scoring is weighted keyword overlap.** Title, tag and category hits
  count 2 and description or colour hits count 1, so `graphic tee` ranks
  items tagged `graphic tee` above ones that only mention a tee in passing.
  Ties keep dataset order, which makes the result order repeatable.
- **Model tools never return an empty string.** A blank model reply becomes a
  fixed fallback string, so the loop never has to handle `""`.
- **`ModelUnavailable` is passed up to `run_agent`.** Unit 4 adds the handler
  in the agent, which is where the starter put the import.

## 2026-10-07 — Track project state in `docs/`

`docs/PLAN.md` holds step status and the tool contracts; this file holds the
reasoning behind choices. The work spans unit 3 and unit 4, so state lives in
the repo where either session can read it.

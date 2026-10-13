# Changelog

## Unreleased
- Reading-comprehension support: new `passage` command prints a passage and
  asks its N linked questions (`--id` to pick one, `--seed` for a reproducible
  pick, `--shuffle-options` supported). Passages live in
  `data/passages.json` with a validator (`validate_passages`) wired into the
  `subjects` health check; shipped with `DR-P01` ("The Waggle Dance", 5
  linked questions: main idea, detail ×2, vocabulary-in-context, inference).
  Linked questions inherit subject/topic from their passage, are logged under
  history mode `passage`, and are included in the `review` miss queue.
- Per-question time tracking in `mock` mode: each answer's time is logged to
  history, the mock report ranks your slowest topics by average time per
  question, and `stats` shows the same ranking across all timed attempts.
- `--shuffle-options` flag on `practice`, `mock`, and `review`: shuffles each
  question's option positions and remaps the answer index, so correct letters
  can't be memorized. Original bank is never mutated; combine with `--seed`
  for a reproducible session.

## 0.1.0 — 2026-10-04
- Initial release: terminal practice drills for the DDCET exam.
- `practice` mode: untimed, subject/topic filters, instant feedback with explanations.
- `mock` mode: timed, intermixed subjects, DDCET marking (+2 / −0.5 / E).
- `stats`: topic-wise accuracy from append-only history in `~/.ddcet-drill/history.jsonl`.
- `subjects`: bank coverage report + integrity health check.
- Seed bank: 49 questions across all 7 DDCET subjects, each with an explanation.
- Standard library only, no dependencies.

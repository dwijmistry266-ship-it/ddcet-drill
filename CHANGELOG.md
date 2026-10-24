# Changelog

## Unreleased
- `stats` now prints per-subject aggregate rows after the topic rows: each
  subject's correct/attempted count, accuracy, and average seconds per
  question over timed attempts ("-" when a subject has no timed data).
  Backed by `history.accuracy_by_subject()` and `history.time_by_subject()`
  (same skipped/untimed rules as the topic helpers); the `--csv` export is
  unchanged. 3 new tests in `tests/test_stats.py`.
- Graceful Ctrl+C handling: pressing Ctrl+C during a session now exits with
  the conventional code 130 and a one-line message ("Interrupted. If a
  session was in progress, it was not logged.") instead of dumping a
  traceback; the interrupted session never reaches `history.log_attempt`.
  2 new tests in `tests/test_interrupt.py`.
- `streak` command: shows days practiced this week (Mon–Sun weekly grid), the
  current consecutive-day streak (survives the day until you miss one — it
  isn't zeroed at midnight before you practice), and the best streak so far.
  Backed by `history.practice_days()`, `current_streak()`, `longest_streak()`
  and `week_of()`; 10 new tests in `tests/test_streak.py`. README usage added.
- CSV export for `stats`: `ddcet-drill stats --csv FILE` writes one row per
  (subject, topic) with `subject, topic, correct, attempted, accuracy_pct,
  avg_secs` so progress can be tracked in a spreadsheet. Timed topics carry
  their average seconds per question; untimed topics leave `avg_secs` empty.
  7 new tests in `tests/test_stats.py`.
- Difficulty tags + adaptive drill: every bank question (74) and passage
  question (5) now carries a `difficulty` tag (`easy`/`medium`/`hard`),
  required and validated by `validate`/`validate_passages`; the new `adapt`
  command samples questions weighted toward the topics you get wrong (neutral
  weight for never-attempted topics) and adapts the difficulty pool to your
  overall accuracy (<50% easy only, 50–80% easy+medium, >80% medium+hard;
  discovery mix with no history). Difficulty is shown in the question prompt
  and broken down per subject in `subjects`; attempts log under mode `adapt`.
  10 new tests in `tests/test_adapt.py`.
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

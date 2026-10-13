<p align="center">
  <img src="assets/banner.svg" width="100%" alt="DDCET-DRILL">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-00f0ff?style=for-the-badge&logo=python&logoColor=white&labelColor=04060c" alt="python">
  <img src="https://img.shields.io/badge/license-MIT-ff2a6d?style=for-the-badge&labelColor=04060c" alt="license">
  <img src="https://img.shields.io/badge/version-0.1.0-b967ff?style=for-the-badge&labelColor=04060c" alt="version">
</p>

---

# ddcet-drill

> **Terminal practice drills for the DDCET exam** — Gujarat's diploma-to-degree
> engineering entrance. Practice by subject, run timed mocks, and track
> topic-wise accuracy. Uses the real DDCET marking scheme: **+2 correct,
> −0.5 wrong, 0 for Not attempted (E).**

Standard library only. No dependencies, no network, no accounts.

## Install

```bash
pip install .
```

## Usage

```bash
# Untimed drill: 10 physics questions, instant feedback
ddcet-drill practice --subject physics -n 10

# Timed mock: 20 questions, 30 minutes, subjects intermixed
ddcet-drill mock -n 20 --minutes 30

# Topic-wise accuracy across all your attempts
ddcet-drill stats

# Re-attempt only the questions you got wrong (cleared once you get one right)
ddcet-drill review --subject physics

# Reading comprehension: read a passage, answer its linked questions
ddcet-drill passage            # pick a random passage (--id DR-P01 for a specific one)
# Shuffle option positions so you can't memorize answer letters
# (works on practice, mock and review; add --seed for a reproducible session)
ddcet-drill practice -n 10 --shuffle-options

# What the question bank covers (and its health check)
ddcet-drill subjects
```

Attempts are logged to `~/.ddcet-drill/history.jsonl` (append-only), which
powers `stats` and `review`. Delete the file any time to reset.

## Reading comprehension

`ddcet-drill passage` prints a passage (e.g. `DR-P01`, "The Waggle Dance"),
then asks its linked questions with the usual +2 / −0.5 / E marking. Use
`--id` to pick a specific passage or `--seed` for a reproducible pick;
`--shuffle-options` works here too. Passages live in
`src/ddcet_drill/data/passages.json` — add more following the same schema
(`id`, `subject`, `topic`, `title`, `passage`, `questions` with the same
fields as bank questions but no `subject`/`topic`, which are inherited).
Attempts are logged under mode `passage`, so `stats` and `review` cover
passage questions automatically.

## Question bank

Seeded with 49 questions across all 7 DDCET subjects, each with an
explanation. The bank lives in `src/ddcet_drill/data/questions.json` — add
more following the same schema (`id`, `subject`, `topic`, `stem`, `options`
× 4, `answer` index, `explanation`) and they are picked up automatically.

## Marking

Matches the DDCET paper: +2 for a correct answer, −0.5 for a wrong one,
0 for E (Not attempted). The mock report breaks your score down per subject,
lists every mistake with its explanation, and ranks your slowest topics by
average time per question — so each attempt teaches. `stats` shows the same
slowest-topics ranking across all timed attempts in your history.

## License

MIT — see [LICENSE](LICENSE).

---
<p align="center"><sub>// end of transmission _</sub></p>

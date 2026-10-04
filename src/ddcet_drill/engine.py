"""Quiz engine: asking, DDCET-style scoring, practice and mock modes."""

import time

LETTERS = "ABCDE"
MARKS_CORRECT = 2.0
MARKS_WRONG = -0.5


def ask(q):
    """Present one question, return the chosen letter (A-E)."""
    print(f"\n[{q['subject']} / {q['topic']}] {q['stem']}")
    for i, opt in enumerate(q["options"]):
        print(f"  {LETTERS[i]}) {opt}")
    print("  E) Not attempted")
    while True:
        ans = input("Your answer (A-E): ").strip().upper()
        if len(ans) == 1 and ans in LETTERS:
            return ans
        print("Please enter A, B, C, D or E.")


def score_answer(q, ans):
    """Return (points, verdict) using DDCET marking: +2 / -0.5 / 0."""
    if ans == "E":
        return 0.0, "skipped"
    if ans == LETTERS[q["answer"]]:
        return MARKS_CORRECT, "correct"
    return MARKS_WRONG, "wrong"


def run_practice(questions):
    """Untimed drill with immediate feedback. Returns result dicts."""
    results = []
    for i, q in enumerate(questions, 1):
        print(f"\n--- Q{i}/{len(questions)} ---")
        ans = ask(q)
        pts, verdict = score_answer(q, ans)
        correct_letter = LETTERS[q["answer"]]
        if verdict == "correct":
            print("Correct! +2")
        elif verdict == "skipped":
            print(f"Skipped. Correct answer was {correct_letter}.")
        else:
            print(f"Wrong (-0.5). Correct answer was {correct_letter}.")
        print(f"Why: {q['explanation']}")
        results.append({"q": q, "ans": ans, "pts": pts, "verdict": verdict})
    return results


def run_mock(questions, minutes):
    """Timed mock, DDCET intermixed style. No feedback until the end."""
    deadline = time.time() + minutes * 60
    results = []
    for i, q in enumerate(questions, 1):
        if time.time() >= deadline:
            print("\nTime's up!")
            break
        print(f"\n--- Q{i}/{len(questions)} ---")
        ans = ask(q)
        pts, verdict = score_answer(q, ans)
        results.append({"q": q, "ans": ans, "pts": pts, "verdict": verdict})
    return results


def summarize(results):
    """Return totals and per-subject breakdown for a result list."""
    total = sum(r["pts"] for r in results)
    counts = {"correct": 0, "wrong": 0, "skipped": 0}
    per_subject = {}
    for r in results:
        counts[r["verdict"]] += 1
        sub = r["q"]["subject"]
        entry = per_subject.setdefault(sub, {"correct": 0, "wrong": 0, "skipped": 0, "pts": 0.0})
        entry[r["verdict"]] += 1
        entry["pts"] += r["pts"]
    return {"total": total, "counts": counts, "per_subject": per_subject}


def print_report(results):
    """Print the final score report with per-subject breakdown."""
    s = summarize(results)
    n = len(results)
    print("\n========== RESULT ==========")
    print(f"Score: {s['total']:.1f} / {2 * n}")
    c = s["counts"]
    print(f"Correct: {c['correct']}  Wrong: {c['wrong']}  Skipped: {c['skipped']}")
    print("\nPer subject:")
    for sub, e in sorted(s["per_subject"].items()):
        print(f"  {sub:<12} {e['pts']:+.1f}  (C:{e['correct']} W:{e['wrong']} S:{e['skipped']})")
    missed = [r for r in results if r["verdict"] == "wrong"]
    if missed:
        print("\nReview your mistakes:")
        for r in missed:
            q = r["q"]
            print(f"  - {q['stem'][:70]}... -> {LETTERS[q['answer']]}) "
                  f"{q['options'][q['answer']]} | {q['explanation']}")
    print("============================")

"""Command-line interface for ddcet-drill."""

import argparse
import random

from . import __version__
from . import engine, history
from .questions import (adaptive_sample, filter_questions,
                        load_bank, load_passages, passage_questions,
                        question_index, sample, shuffle_options, subjects,
                        validate, validate_passages)


def cmd_practice(args):
    bank = load_bank()
    pool = filter_questions(bank, subject=args.subject, topic=args.topic)
    if not pool:
        print("No questions match that filter. Try `ddcet-drill subjects`.")
        return 1
    qs = sample(pool, args.n, seed=args.seed)
    if args.shuffle_options:
        qs = shuffle_options(qs, seed=args.seed)
    print(f"Practice: {len(qs)} questions"
          + (f" [{args.subject}]" if args.subject else "")
          + (f" / {args.topic}" if args.topic else ""))
    print("Marking: +2 correct, -0.5 wrong, 0 for E (Not attempted).")
    results = engine.run_practice(qs)
    history.log_attempt("practice", results)
    engine.print_report(results)
    return 0


def cmd_mock(args):
    bank = load_bank()
    qs = sample(bank, args.n, seed=args.seed)
    if args.shuffle_options:
        qs = shuffle_options(qs, seed=args.seed)
    print(f"Mock: {len(qs)} questions, {args.minutes} minutes.")
    print("Subjects intermixed, DDCET style. E = Not attempted (0 marks).")
    input("Press Enter to start the timer...")
    results = engine.run_mock(qs, args.minutes)
    history.log_attempt("mock", results)
    engine.print_report(results)
    return 0


def cmd_passage(args):
    passages = load_passages()
    if not passages:
        print("No passages in the bank yet.")
        return 1
    if args.id:
        match = [p for p in passages if p["id"] == args.id]
        if not match:
            print(f"No passage {args.id!r}. Available: "
                  + ", ".join(p["id"] for p in passages))
            return 1
        passage = match[0]
    else:
        passage = random.Random(args.seed).choice(passages)
    qs = passage_questions(passage)
    if args.shuffle_options:
        qs = shuffle_options(qs, seed=args.seed)
    print(f"Passage: {passage['title']} "
          f"({len(qs)} linked questions) [{passage['subject']}/{passage['topic']}]")
    engine.present_passage(passage)
    print("\nAnswer the questions below. The passage stays on screen in your "
          "scrollback; marking is +2 / -0.5 / E as usual.")
    results = engine.run_practice(qs)
    history.log_attempt("passage", results)
    engine.print_report(results)
    return 0


def cmd_adapt(args):
    bank = load_bank()
    entries = history.read_history()
    qs = adaptive_sample(bank, args.n, entries, seed=args.seed)
    if not qs:
        print("No questions in the bank.")
        return 1
    if args.shuffle_options:
        qs = shuffle_options(qs, seed=args.seed)
    print(f"Adapt: {len(qs)} questions, weighted toward your weak topics.")
    if not entries:
        print("No history yet — serving a discovery mix across all difficulties.")
    else:
        print("The difficulty pool grows as your overall accuracy improves.")
    print("Marking: +2 correct, -0.5 wrong, 0 for E (Not attempted).")
    results = engine.run_practice(qs)
    history.log_attempt("adapt", results)
    engine.print_report(results)
    return 0


def cmd_review(args):
    bank = load_bank()
    entries = history.read_history()
    missed = history.missed_ids(entries)
    if not missed:
        print("No mistakes on record. Run `ddcet-drill practice` or `ddcet-drill mock` first.")
        return 0
    by_id = question_index(bank)
    pool = [by_id[qid] for qid in missed if qid in by_id]
    pool = filter_questions(pool, subject=args.subject, topic=args.topic)
    if not pool:
        print("No recorded mistakes match that filter.")
        return 1
    qs = sample(pool, args.n, seed=args.seed) if args.seed is not None else pool[:args.n]
    if args.shuffle_options:
        qs = shuffle_options(qs, seed=args.seed)
    print(f"Review: {len(qs)} question(s) you got wrong and haven't gotten right since.")
    print("Marking: +2 correct, -0.5 wrong, 0 for E (Not attempted).")
    results = engine.run_practice(qs)
    history.log_attempt("review", results)
    engine.print_report(results)
    return 0


def cmd_stats(_args):
    entries = history.read_history()
    if not entries:
        print("No attempts logged yet. Run `ddcet-drill practice` first.")
        return 0
    print(f"Attempts logged: {len(entries)}")
    for (sub, topic), (c, a) in sorted(history.accuracy_by_topic(entries).items()):
        pct = f"{100 * c / a:.0f}%" if a else "-"
        print(f"  {sub}/{topic:<28} {c}/{a} correct ({pct})")
    slowest = sorted(
        ((k, t / n) for k, (t, n) in history.time_by_topic(entries).items()),
        key=lambda kv: kv[1], reverse=True)[:5]
    if slowest:
        print("\nSlowest topics by avg time/question (timed attempts):")
        for (sub, topic), avg in slowest:
            print(f"  {sub}/{topic:<28} {avg:5.1f}s avg")
    return 0


def cmd_subjects(_args):
    bank = load_bank()
    print("Question bank coverage:")
    for sub in subjects(bank):
        topics = sorted({q["topic"] for q in bank if q["subject"] == sub})
        n = sum(1 for q in bank if q["subject"] == sub)
        diffs = {d: sum(1 for q in bank
                        if q["subject"] == sub and q.get("difficulty") == d)
                 for d in ("easy", "medium", "hard")}
        print(f"  {sub:<12} {n:>3} questions  "
              f"easy:{diffs['easy']} medium:{diffs['medium']} hard:{diffs['hard']}  "
              f"topics: {', '.join(topics)}")
    passages = load_passages()
    linked = sum(len(p["questions"]) for p in passages)
    print(f"\nPassages: {len(passages)} ({linked} linked reading-comprehension "
          f"questions):")
    for p in passages:
        print(f"  {p['id']:<10} {p['title']} — {len(p['questions'])} questions")
    problems = validate(bank) + validate_passages(
        passages, bank_ids=[q["id"] for q in bank])
    if problems:
        print("\nBank problems:")
        for p in problems:
            print(f"  ! {p}")
        return 1
    print(f"\nTotal: {len(bank)} questions + {linked} passage questions, "
          "bank healthy.")
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        prog="ddcet-drill",
        description="Terminal practice drills for the DDCET exam (+2 / -0.5 / E).",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("practice", help="Untimed drill with instant feedback.")
    pr.add_argument("--subject", default=None, help="Filter by subject.")
    pr.add_argument("--topic", default=None, help="Filter by topic.")
    pr.add_argument("-n", type=int, default=10, help="Number of questions.")
    pr.add_argument("--seed", type=int, default=None, help="Random seed.")
    pr.add_argument("--shuffle-options", action="store_true",
                    help="Shuffle option positions so letters can't be memorized.")
    pr.set_defaults(func=cmd_practice)

    mk = sub.add_parser("mock", help="Timed mock, subjects intermixed.")
    mk.add_argument("-n", type=int, default=20, help="Number of questions.")
    mk.add_argument("--minutes", type=int, default=30, help="Time limit.")
    mk.add_argument("--seed", type=int, default=None, help="Random seed.")
    mk.add_argument("--shuffle-options", action="store_true",
                    help="Shuffle option positions so letters can't be memorized.")
    mk.set_defaults(func=cmd_mock)

    ad = sub.add_parser("adapt", help="Adaptive drill: more of what you miss.")
    ad.add_argument("-n", type=int, default=10, help="Number of questions.")
    ad.add_argument("--seed", type=int, default=None, help="Random seed.")
    ad.add_argument("--shuffle-options", action="store_true",
                    help="Shuffle option positions so letters can't be memorized.")
    ad.set_defaults(func=cmd_adapt)

    st = sub.add_parser("stats", help="Topic-wise accuracy from history.")
    st.set_defaults(func=cmd_stats)

    rv = sub.add_parser("review", help="Re-attempt only questions you got wrong.")
    rv.add_argument("--subject", default=None, help="Filter by subject.")
    rv.add_argument("--topic", default=None, help="Filter by topic.")
    rv.add_argument("-n", type=int, default=None, help="Number of questions (default: all open misses).")
    rv.add_argument("--seed", type=int, default=None, help="Random seed.")
    rv.add_argument("--shuffle-options", action="store_true",
                    help="Shuffle option positions so letters can't be memorized.")
    rv.set_defaults(func=cmd_review)

    ps = sub.add_parser("passage", help="Read a passage, answer its linked questions.")
    ps.add_argument("--id", default=None,
                    help="Passage id (default: pick one at random).")
    ps.add_argument("--seed", type=int, default=None,
                    help="Random seed (also picks the passage reproducibly).")
    ps.add_argument("--shuffle-options", action="store_true",
                    help="Shuffle option positions so letters can't be memorized.")
    ps.set_defaults(func=cmd_passage)

    sj = sub.add_parser("subjects", help="Show bank coverage and health.")
    sj.set_defaults(func=cmd_subjects)
    return p


def main():
    args = build_parser().parse_args()
    raise SystemExit(args.func(args))

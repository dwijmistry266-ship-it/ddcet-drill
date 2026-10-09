"""Shuffle tests: option shuffling must keep scoring correct and never mutate."""

from ddcet_drill import engine
from ddcet_drill.cli import build_parser
from ddcet_drill.questions import shuffle_options


def _qs():
    return [
        {"id": "S-1", "subject": "physics", "topic": "units", "stem": "s1",
         "options": ["w1", "right", "w2", "w3"], "answer": 1, "explanation": "e"},
        {"id": "S-2", "subject": "maths", "topic": "logs", "stem": "s2",
         "options": ["w1", "w2", "w3", "right"], "answer": 3, "explanation": "e"},
    ]


def test_correct_option_follows_shuffle():
    """After shuffling, the correct option text must sit at the new answer index."""
    for seed in range(25):
        for q in shuffle_options(_qs(), seed=seed):
            orig = next(o for o in _qs() if o["id"] == q["id"])
            assert q["options"][q["answer"]] == orig["options"][orig["answer"]]
            assert 0 <= q["answer"] <= 3
            assert len(q["options"]) == 4


def test_options_are_preserved_as_a_set():
    for q in shuffle_options(_qs(), seed=7):
        orig = next(o for o in _qs() if o["id"] == q["id"])
        assert sorted(q["options"]) == sorted(orig["options"])


def test_shuffle_actually_moves_options():
    """At least one seed must relocate the correct option (else the feature is moot)."""
    orig = _qs()[0]
    moved = any(
        shuffle_options([orig], seed=s)[0]["answer"] != orig["answer"]
        for s in range(20)
    )
    assert moved


def test_deterministic_with_seed():
    first = shuffle_options(_qs(), seed=42)
    second = shuffle_options(_qs(), seed=42)
    assert [(q["options"], q["answer"]) for q in first] == \
           [(q["options"], q["answer"]) for q in second]


def test_original_questions_not_mutated():
    qs = _qs()
    before = [(list(q["options"]), q["answer"]) for q in qs]
    shuffle_options(qs, seed=3)
    assert [(list(q["options"]), q["answer"]) for q in qs] == before


def test_identity_fields_preserved():
    for q in shuffle_options(_qs(), seed=11):
        orig = next(o for o in _qs() if o["id"] == q["id"])
        for field in ("id", "subject", "topic", "stem", "explanation"):
            assert q[field] == orig[field]


def test_scoring_still_marks_correct_letter():
    """engine.score_answer must mark the shuffled correct letter as correct."""
    q = shuffle_options(_qs(), seed=5)[0]
    correct_letter = engine.LETTERS[q["answer"]]
    pts, verdict = engine.score_answer(q, correct_letter)
    assert pts == 2.0 and verdict == "correct"
    wrong_letter = engine.LETTERS[(q["answer"] + 1) % 4]
    pts, verdict = engine.score_answer(q, wrong_letter)
    assert pts == -0.5 and verdict == "wrong"


def test_parser_accepts_flag_on_all_modes():
    p = build_parser()
    for cmd in ("practice", "mock", "review"):
        args = p.parse_args([cmd, "--shuffle-options"])
        assert args.shuffle_options is True
        args = p.parse_args([cmd])
        assert args.shuffle_options is False

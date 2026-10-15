"""Adapt tests: difficulty tags and the adaptive drill sampler."""

from ddcet_drill.questions import (DIFFICULTIES, adaptive_sample,
                                   filter_questions, load_bank, load_passages,
                                   validate, validate_passages)


def _bank():
    return [
        {"id": "A-1", "subject": "s", "topic": "weak", "difficulty": "easy",
         "stem": "a1", "options": ["1", "2", "3", "4"], "answer": 0, "explanation": "e"},
        {"id": "A-2", "subject": "s", "topic": "weak", "difficulty": "medium",
         "stem": "a2", "options": ["1", "2", "3", "4"], "answer": 0, "explanation": "e"},
        {"id": "A-3", "subject": "s", "topic": "weak", "difficulty": "hard",
         "stem": "a3", "options": ["1", "2", "3", "4"], "answer": 0, "explanation": "e"},
        {"id": "B-1", "subject": "s", "topic": "strong", "difficulty": "easy",
         "stem": "b1", "options": ["1", "2", "3", "4"], "answer": 0, "explanation": "e"},
        {"id": "B-2", "subject": "s", "topic": "strong", "difficulty": "medium",
         "stem": "b2", "options": ["1", "2", "3", "4"], "answer": 0, "explanation": "e"},
        {"id": "B-3", "subject": "s", "topic": "strong", "difficulty": "hard",
         "stem": "b3", "options": ["1", "2", "3", "4"], "answer": 0, "explanation": "e"},
        {"id": "C-1", "subject": "s", "topic": "unseen", "difficulty": "easy",
         "stem": "c1", "options": ["1", "2", "3", "4"], "answer": 0, "explanation": "e"},
        {"id": "C-2", "subject": "s", "topic": "unseen", "difficulty": "medium",
         "stem": "c2", "options": ["1", "2", "3", "4"], "answer": 0, "explanation": "e"},
        {"id": "C-3", "subject": "s", "topic": "unseen", "difficulty": "hard",
         "stem": "c3", "options": ["1", "2", "3", "4"], "answer": 0, "explanation": "e"},
    ]


def _entries(verdicts):
    return [{"ts": 1, "mode": "practice",
             "items": [{"id": f"X-{i}", "subject": "s", "topic": t,
                        "verdict": v, "pts": 0.0}
                       for i, (t, v) in enumerate(verdicts)]}]


def test_bank_difficulties_valid():
    """Every shipped bank + passage question must carry a valid difficulty."""
    bank = load_bank()
    assert bank, "bank is empty"
    for q in bank:
        assert q.get("difficulty") in DIFFICULTIES, q.get("id")
    for p in load_passages():
        for q in p["questions"]:
            assert q.get("difficulty") in DIFFICULTIES, q.get("id")


def test_validate_rejects_bad_difficulty():
    q = dict(_bank()[0])
    q["difficulty"] = "extreme"
    problems = validate([q])
    assert any("difficulty" in p for p in problems), problems


def test_validate_passages_rejects_missing_difficulty():
    p = {"id": "P", "subject": "s", "topic": "t", "title": "T", "passage": "txt",
         "questions": [dict(_bank()[0])]}
    del p["questions"][0]["difficulty"]
    problems = validate_passages([p])
    assert any("difficulty" in prob for prob in problems), problems


def test_filter_by_difficulty():
    bank = load_bank()
    easy = filter_questions(bank, difficulty="easy")
    assert easy and all(q["difficulty"] == "easy" for q in easy)
    assert len(easy) < len(bank)
    combined = filter_questions(bank, subject="physics", difficulty="hard")
    assert all(q["subject"] == "physics" and q["difficulty"] == "hard"
               for q in combined)


def test_adaptive_sample_deterministic():
    bank = _bank()
    entries = _entries([("weak", "wrong"), ("strong", "correct")])
    first = [q["id"] for q in adaptive_sample(bank, 4, entries, seed=7)]
    second = [q["id"] for q in adaptive_sample(bank, 4, entries, seed=7)]
    assert first == second


def test_adaptive_sample_biases_weak_topics():
    """Across fixed seeds, weak topics must dominate the sampled questions."""
    bank = _bank()
    # 2 wrong on "weak", 5+4 correct elsewhere -> overall 9/11, medium+hard pool
    entries = _entries([("weak", "wrong")] * 2 + [("strong", "correct")] * 5
                       + [("unseen", "correct")] * 4)
    counts = {"weak": 0, "strong": 0, "unseen": 0}
    for seed in range(10):
        for q in adaptive_sample(bank, 4, entries, seed=seed):
            counts[q["topic"]] += 1
    assert counts["weak"] > counts["strong"], counts
    assert counts["weak"] > counts["unseen"], counts


def test_adaptive_sample_covers_unseen_topics():
    """Topics with no history get neutral weight, so new ground is covered."""
    bank = _bank()
    entries = _entries([("weak", "wrong")] * 2 + [("strong", "correct")] * 2)
    counts = {"weak": 0, "strong": 0, "unseen": 0}
    for seed in range(10):
        for q in adaptive_sample(bank, 4, entries, seed=seed):
            counts[q["topic"]] += 1
    assert counts["unseen"] > 0, counts
    assert counts["weak"] > counts["strong"], counts


def test_adaptive_sample_no_history_serves_all():
    bank = _bank()
    got = adaptive_sample(bank, 9, [], seed=3)
    assert len(got) == 9
    assert {q["difficulty"] for q in got} == set(DIFFICULTIES)


def test_adaptive_difficulty_pool_gates_on_accuracy():
    """Weak overall accuracy -> easy only; strong -> medium+hard."""
    bank = _bank()
    all_wrong = _entries([("weak", "wrong")] * 3 + [("strong", "wrong")] * 3)
    got = adaptive_sample(bank, 6, all_wrong, seed=1)
    assert {q["difficulty"] for q in got} == {"easy"}, [q["id"] for q in got]
    all_right = _entries([("weak", "correct")] * 3 + [("strong", "correct")] * 3)
    got = adaptive_sample(bank, 6, all_right, seed=1)
    assert {q["difficulty"] for q in got} <= {"medium", "hard"}, [q["id"] for q in got]
    mixed = _entries([("weak", "correct")] * 3 + [("strong", "wrong")] * 3)
    got = adaptive_sample(bank, 6, mixed, seed=1)
    assert {q["difficulty"] for q in got} <= {"easy", "medium"}, [q["id"] for q in got]


def test_adaptive_sample_caps_at_bank_size():
    bank = _bank()
    got = adaptive_sample(bank, 100, [], seed=1)
    assert len(got) == len(bank)
    assert len({q["id"] for q in got}) == len(bank)  # no repeats

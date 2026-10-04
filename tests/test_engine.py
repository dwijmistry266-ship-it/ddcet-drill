"""Engine tests: DDCET marking scheme and score summaries."""

from ddcet_drill import engine


def _q(answer=1):
    return {"id": "T-1", "subject": "physics", "topic": "units",
            "stem": "s", "options": ["a", "b", "c", "d"],
            "answer": answer, "explanation": "e"}


def test_correct_scores_plus_two():
    pts, verdict = engine.score_answer(_q(answer=1), "B")
    assert pts == 2.0 and verdict == "correct"


def test_wrong_scores_minus_half():
    pts, verdict = engine.score_answer(_q(answer=1), "A")
    assert pts == -0.5 and verdict == "wrong"


def test_skip_scores_zero():
    pts, verdict = engine.score_answer(_q(answer=1), "E")
    assert pts == 0.0 and verdict == "skipped"


def test_summarize_totals():
    results = [
        {"q": _q(), "ans": "B", "pts": 2.0, "verdict": "correct"},
        {"q": _q(), "ans": "A", "pts": -0.5, "verdict": "wrong"},
        {"q": _q(), "ans": "E", "pts": 0.0, "verdict": "skipped"},
    ]
    s = engine.summarize(results)
    assert s["total"] == 1.5
    assert s["counts"] == {"correct": 1, "wrong": 1, "skipped": 1}
    assert s["per_subject"]["physics"]["pts"] == 1.5

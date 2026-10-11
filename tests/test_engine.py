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


def _timed(subject, topic, secs):
    q = _q()
    q["subject"] = subject
    q["topic"] = topic
    return {"q": q, "ans": "B", "pts": 2.0, "verdict": "correct", "secs": secs}


def test_run_mock_records_per_question_time(monkeypatch):
    monkeypatch.setattr(engine, "ask", lambda q: "B")
    results = engine.run_mock([_q(), _q()], minutes=30)
    assert len(results) == 2
    for r in results:
        assert "secs" in r
        assert isinstance(r["secs"], float)
        assert r["secs"] >= 0.0


def test_run_mock_times_up_records_no_results(monkeypatch):
    monkeypatch.setattr(engine, "ask", lambda q: "B")
    results = engine.run_mock([_q()], minutes=0)
    assert results == []


def test_summarize_per_topic_time():
    results = [
        _timed("physics", "units", 10.0),
        _timed("physics", "units", 20.0),
        _timed("maths", "limits", 60.0),
        {"q": _q(), "ans": "E", "pts": 0.0, "verdict": "skipped"},  # untimed: ignored
    ]
    s = engine.summarize(results)
    t = s["per_topic_time"]
    assert t[("physics", "units")]["n"] == 2
    assert t[("physics", "units")]["avg"] == 15.0
    assert t[("maths", "limits")]["n"] == 1
    assert t[("maths", "limits")]["avg"] == 60.0


def test_print_report_lists_slowest_topics_first(capsys):
    results = [
        _timed("physics", "units", 10.0),
        _timed("maths", "limits", 60.0),
    ]
    engine.print_report(results)
    out = capsys.readouterr().out
    assert "Slowest topics" in out
    limits_pos = out.index("limits")
    units_pos = out.index("units")
    assert limits_pos < units_pos  # slower topic printed first


def test_print_report_omits_time_section_when_untimed(capsys):
    results = [{"q": _q(), "ans": "B", "pts": 2.0, "verdict": "correct"}]
    engine.print_report(results)
    out = capsys.readouterr().out
    assert "Slowest topics" not in out

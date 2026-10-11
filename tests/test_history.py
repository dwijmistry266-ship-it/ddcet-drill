"""History tests: review queue of open misses."""

from ddcet_drill import history


def _item(qid, verdict):
    return {"id": qid, "subject": "physics", "topic": "units",
            "verdict": verdict, "pts": 0.0}


def _entry(items):
    return {"ts": 1, "mode": "practice", "items": items}


def test_open_miss_included():
    entries = [_entry([_item("Q1", "wrong")])]
    assert history.missed_ids(entries) == ["Q1"]


def test_correct_clears_miss():
    entries = [
        _entry([_item("Q1", "wrong")]),
        _entry([_item("Q1", "correct")]),
    ]
    assert history.missed_ids(entries) == []


def test_latest_verdict_wins():
    entries = [
        _entry([_item("Q1", "correct")]),
        _entry([_item("Q1", "wrong")]),
    ]
    assert history.missed_ids(entries) == ["Q1"]


def test_skip_does_not_clear_miss():
    entries = [
        _entry([_item("Q1", "wrong")]),
        _entry([_item("Q1", "skipped")]),
    ]
    assert history.missed_ids(entries) == ["Q1"]


def test_skip_alone_is_not_a_miss():
    entries = [_entry([_item("Q1", "skipped")])]
    assert history.missed_ids(entries) == []


def test_most_recently_missed_first():
    entries = [
        _entry([_item("Q1", "wrong")]),
        _entry([_item("Q2", "wrong")]),
        _entry([_item("Q3", "correct")]),
    ]
    assert history.missed_ids(entries) == ["Q2", "Q1"]


def test_no_history_means_no_misses():
    assert history.missed_ids([]) == []


def _item_timed(qid, secs):
    item = _item(qid, "correct")
    item["secs"] = secs
    return item


def test_time_by_topic_aggregates():
    entries = [
        _entry([_item_timed("Q1", 10.0), _item_timed("Q2", 20.0)]),
        _entry([_item("Q3", "correct")]),  # untimed: skipped
    ]
    stats = history.time_by_topic(entries)
    assert stats[("physics", "units")] == (30.0, 2)


def test_time_by_topic_ignores_untimed_entries():
    entries = [_entry([_item("Q1", "correct")])]
    assert history.time_by_topic(entries) == {}


def test_log_attempt_persists_secs(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "HIST_FILE", tmp_path / "h.jsonl")
    q = {"id": "Q1", "subject": "physics", "topic": "units"}
    entry = history.log_attempt("mock", [{"q": q, "ans": "B", "pts": 2.0,
                                          "verdict": "correct", "secs": 12.34}])
    assert entry["items"][0]["secs"] == 12.3  # rounded to 0.1
    roundtrip = history.read_history()
    assert roundtrip[0]["items"][0]["secs"] == 12.3


def test_log_attempt_omits_secs_when_untimed(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "HIST_FILE", tmp_path / "h.jsonl")
    q = {"id": "Q1", "subject": "physics", "topic": "units"}
    entry = history.log_attempt("practice", [{"q": q, "ans": "B", "pts": 2.0,
                                              "verdict": "correct"}])
    assert "secs" not in entry["items"][0]

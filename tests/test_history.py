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

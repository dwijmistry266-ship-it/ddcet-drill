"""Streak tests: practice days, current/best streaks, week layout."""

from datetime import date, datetime, timedelta

from ddcet_drill import history

TODAY = date(2026, 10, 20)  # a Tuesday (verified against `date -d`)


def _ts(d):
    return int(datetime(d.year, d.month, d.day, 12).timestamp())


def _entries(*days):
    return [{"ts": _ts(d), "mode": "practice", "items": []} for d in days]


def _d(days_ago):
    return TODAY - timedelta(days=days_ago)


def test_practice_days_collapses_same_day():
    entries = _entries(TODAY, TODAY, _d(1))
    assert history.practice_days(entries) == {TODAY, _d(1)}


def test_practice_days_empty_history():
    assert history.practice_days([]) == set()


def test_practice_days_ignores_missing_ts():
    assert history.practice_days([{"mode": "practice", "items": []}]) == set()


def test_current_streak_ending_today():
    days = {_d(0), _d(1), _d(2)}
    assert history.current_streak(days, TODAY) == 3


def test_current_streak_gap_breaks_it():
    days = {_d(0), _d(2)}  # missed yesterday
    assert history.current_streak(days, TODAY) == 1


def test_current_streak_survives_today_not_yet_practiced():
    days = {_d(1), _d(2), _d(3)}
    assert history.current_streak(days, TODAY) == 3


def test_current_streak_dead_after_a_missed_day():
    assert history.current_streak({_d(2)}, TODAY) == 0
    assert history.current_streak(set(), TODAY) == 0


def test_longest_streak_picks_longest_run():
    days = {_d(9), _d(8), _d(7), _d(4), _d(3)}
    assert history.longest_streak(days) == 3


def test_longest_streak_single_day_and_empty():
    assert history.longest_streak({_d(5)}) == 1
    assert history.longest_streak(set()) == 0


def test_week_of_is_monday_to_sunday_containing_date():
    week = history.week_of(TODAY)
    assert len(week) == 7
    assert week[0].weekday() == 0  # Monday
    assert week == [week[0] + timedelta(days=i) for i in range(7)]
    assert TODAY in week

"""Attempt history: append-only JSONL log in the user's home directory."""

import json
import time
from datetime import date, datetime, timedelta
from pathlib import Path

HIST_FILE = Path.home() / ".ddcet-drill" / "history.jsonl"


def log_attempt(mode, results):
    """Append one attempt's per-question outcomes. Returns the entry.

    Per-question times ("secs") are logged when the result carries them
    (timed modes like mock); untimed modes omit the field.
    """
    HIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    items = []
    for r in results:
        item = {
            "id": r["q"]["id"],
            "subject": r["q"]["subject"],
            "topic": r["q"]["topic"],
            "verdict": r["verdict"],
            "pts": r["pts"],
        }
        if r.get("secs") is not None:
            item["secs"] = round(r["secs"], 1)
        items.append(item)
    entry = {
        "ts": int(time.time()),
        "mode": mode,
        "items": items,
    }
    with HIST_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def read_history():
    """Return all logged attempts (empty list if none)."""
    if not HIST_FILE.exists():
        return []
    entries = []
    with HIST_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def accuracy_by_topic(entries):
    """Return {(subject, topic): (correct, attempted)} across entries."""
    stats = {}
    for e in entries:
        for it in e["items"]:
            key = (it["subject"], it["topic"])
            c, a = stats.get(key, (0, 0))
            if it["verdict"] != "skipped":
                a += 1
                if it["verdict"] == "correct":
                    c += 1
            stats[key] = (c, a)
    return stats


def time_by_topic(entries):
    """Return {(subject, topic): (total_secs, timed_attempts)} across entries.

    Only entries logged by timed modes carry "secs"; older and untimed
    entries are skipped.
    """
    stats = {}
    for e in entries:
        for it in e["items"]:
            secs = it.get("secs")
            if secs is None:
                continue
            key = (it["subject"], it["topic"])
            t, n = stats.get(key, (0.0, 0))
            stats[key] = (t + secs, n + 1)
    return stats


def practice_days(entries):
    """Return the set of local dates on which at least one attempt was logged.

    Multiple attempts on the same day collapse to one date; entries without
    a timestamp are ignored.
    """
    days = set()
    for e in entries:
        ts = e.get("ts")
        if ts is None:
            continue
        days.add(datetime.fromtimestamp(ts).date())
    return days


def current_streak(days, today=None):
    """Length of the consecutive-day practice streak ending at `today`.

    If `today` itself has no practice yet, the streak counts through
    yesterday — a streak isn't dead just because today's session hasn't
    happened yet. Returns 0 when the most recent practice day is older
    than yesterday.
    """
    if today is None:
        today = date.today()
    days = set(days)
    anchor = today if today in days else today - timedelta(days=1)
    streak = 0
    while anchor - timedelta(days=streak) in days:
        streak += 1
    return streak


def longest_streak(days):
    """Length of the longest run of consecutive practice days (0 if none)."""
    days = set(days)
    best = 0
    for d in days:
        if d - timedelta(days=1) not in days:  # start of a run
            run = 1
            while d + timedelta(days=run) in days:
                run += 1
            best = max(best, run)
    return best


def week_of(d):
    """Return the Monday..Sunday list of 7 dates containing date `d`."""
    monday = d - timedelta(days=d.weekday())
    return [monday + timedelta(days=i) for i in range(7)]


def missed_ids(entries):
    """Return ids of questions to review, most-recently-missed first.

    A question counts as an open miss if its latest attempted verdict was
    "wrong". Getting it "correct" later clears it from the review queue.
    "skipped" verdicts neither add nor clear an entry.
    """
    open_misses = []
    settled = set()
    for e in reversed(entries):
        for it in reversed(e["items"]):
            qid = it["id"]
            if qid in settled:
                continue
            verdict = it["verdict"]
            if verdict == "skipped":
                continue
            settled.add(qid)
            if verdict == "wrong":
                open_misses.append(qid)
    return open_misses

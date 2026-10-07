"""Attempt history: append-only JSONL log in the user's home directory."""

import json
import time
from pathlib import Path

HIST_FILE = Path.home() / ".ddcet-drill" / "history.jsonl"


def log_attempt(mode, results):
    """Append one attempt's per-question outcomes. Returns the entry."""
    HIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": int(time.time()),
        "mode": mode,
        "items": [
            {
                "id": r["q"]["id"],
                "subject": r["q"]["subject"],
                "topic": r["q"]["topic"],
                "verdict": r["verdict"],
                "pts": r["pts"],
            }
            for r in results
        ],
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

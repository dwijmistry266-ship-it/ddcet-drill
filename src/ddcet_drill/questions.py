"""Question bank loading, filtering, and sampling."""

import json
import random
from importlib import resources


def load_bank():
    """Load the full question bank as a list of dicts."""
    with resources.files("ddcet_drill").joinpath("data/questions.json").open(
        "r", encoding="utf-8"
    ) as f:
        return json.load(f)


def subjects(bank):
    """Sorted list of subjects present in the bank."""
    return sorted({q["subject"] for q in bank})


def filter_questions(bank, subject=None, topic=None):
    """Return questions matching subject and/or topic (None = no filter)."""
    return [
        q
        for q in bank
        if (subject is None or q["subject"] == subject)
        and (topic is None or q["topic"] == topic)
    ]


def sample(bank, n, seed=None):
    """Return up to n randomly sampled questions (stable with seed)."""
    rng = random.Random(seed)
    return rng.sample(bank, min(n, len(bank)))


def validate(bank):
    """Return a list of problems found in the bank (empty = healthy)."""
    problems = []
    seen = set()
    for i, q in enumerate(bank):
        tag = q.get("id", f"index-{i}")
        for field in ("id", "subject", "topic", "stem", "options", "answer", "explanation"):
            if field not in q:
                problems.append(f"{tag}: missing field '{field}'")
        if q.get("id") in seen:
            problems.append(f"{tag}: duplicate id")
        seen.add(q.get("id"))
        opts = q.get("options", [])
        if len(opts) != 4:
            problems.append(f"{tag}: expected 4 options, got {len(opts)}")
        ans = q.get("answer")
        if not isinstance(ans, int) or not 0 <= ans <= 3:
            problems.append(f"{tag}: answer index out of range: {ans!r}")
    return problems

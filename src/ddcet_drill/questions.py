"""Question bank loading, filtering, and sampling."""

import json
import random
from importlib import resources

from .history import accuracy_by_topic

DIFFICULTIES = ("easy", "medium", "hard")


def load_bank():
    """Load the full question bank as a list of dicts."""
    with resources.files("ddcet_drill").joinpath("data/questions.json").open(
        "r", encoding="utf-8"
    ) as f:
        return json.load(f)


def subjects(bank):
    """Sorted list of subjects present in the bank."""
    return sorted({q["subject"] for q in bank})


def filter_questions(bank, subject=None, topic=None, difficulty=None):
    """Return questions matching subject/topic/difficulty (None = no filter)."""
    return [
        q
        for q in bank
        if (subject is None or q["subject"] == subject)
        and (topic is None or q["topic"] == topic)
        and (difficulty is None or q.get("difficulty") == difficulty)
    ]


def sample(bank, n, seed=None):
    """Return up to n randomly sampled questions (stable with seed)."""
    rng = random.Random(seed)
    return rng.sample(bank, min(n, len(bank)))


def adaptive_sample(bank, n, entries, seed=None):
    """Weighted sample biased toward topics the user gets wrong.

    Each question's weight is ``0.25 + 1.75 * miss_rate(topic)`` where the
    miss rate comes from history accuracy (skips excluded); topics never
    attempted get a neutral 0.5 so new ground is still covered. The
    difficulty pool also adapts to overall accuracy: below 50% serves easy
    only, 50–80% serves easy+medium, above 80% serves medium+hard; with no
    history every difficulty is served. Deterministic with a seed. Returns
    up to n questions, never mutates the bank.
    """
    rng = random.Random(seed)
    acc = accuracy_by_topic(entries)
    total_c = sum(c for c, _ in acc.values())
    total_a = sum(a for _, a in acc.values())
    if total_a == 0:
        pool = list(bank)
    else:
        overall = total_c / total_a
        if overall < 0.5:
            allowed = {"easy"}
        elif overall <= 0.8:
            allowed = {"easy", "medium"}
        else:
            allowed = {"medium", "hard"}
        pool = [q for q in bank if q.get("difficulty") in allowed] or list(bank)

    def miss_rate(q):
        c, a = acc.get((q["subject"], q["topic"]), (0, 0))
        return 1.0 - c / a if a else 0.5

    weights = [0.25 + 1.75 * miss_rate(q) for q in pool]
    chosen = []
    remaining = list(range(len(pool)))
    for _ in range(min(n, len(pool))):
        total = sum(weights[i] for i in remaining)
        r = rng.random() * total
        for i in remaining:
            r -= weights[i]
            if r <= 0:
                chosen.append(pool[i])
                remaining.remove(i)
                break
    return chosen


def shuffle_options(questions, seed=None):
    """Return copies with each question's options shuffled, answer remapped.

    The correct option text follows its new position, so letter-based
    scoring (`engine.score_answer`) keeps working unchanged. Original
    question dicts are NOT modified. With a seed, shuffles are
    deterministic (one RNG shared across all questions).
    """
    rng = random.Random(seed)
    out = []
    for q in questions:
        order = list(range(len(q["options"])))
        rng.shuffle(order)
        new_options = [q["options"][i] for i in order]
        new_answer = order.index(q["answer"])
        out.append({**q, "options": new_options, "answer": new_answer})
    return out


def load_passages():
    """Load the reading-comprehension passages as a list of dicts.

    Each passage carries id, subject, topic, title, passage text, and a
    list of linked questions (each without subject/topic — those are
    inherited from the passage via passage_questions()).
    """
    with resources.files("ddcet_drill").joinpath("data/passages.json").open(
        "r", encoding="utf-8"
    ) as f:
        return json.load(f)


def passage_questions(passage):
    """Flatten one passage's linked questions into standalone question dicts.

    Subject and topic are inherited from the passage; passage id and
    title are attached so the engine, history log, and review queue keep
    working unchanged. The passage dict is NOT modified.
    """
    out = []
    for q in passage["questions"]:
        flat = dict(q)
        flat.setdefault("subject", passage["subject"])
        flat.setdefault("topic", passage["topic"])
        flat["passage_id"] = passage["id"]
        flat["passage_title"] = passage.get("title", "")
        out.append(flat)
    return out


def question_index(bank=None):
    """Map every question id (bank + passage-linked) to its question dict."""
    bank = load_bank() if bank is None else bank
    index = {q["id"]: q for q in bank}
    for p in load_passages():
        for q in passage_questions(p):
            index[q["id"]] = q
    return index


def validate_passages(passages, bank_ids=()):
    """Return a list of problems found in the passages (empty = healthy).

    Checks required fields, 4 options per linked question, answer index
    range, and id uniqueness across passages, linked questions, and the
    supplied bank ids.
    """
    problems = []
    seen = set(bank_ids)
    for p in passages:
        tag = p.get("id", "passage-?")
        for field in ("id", "subject", "topic", "title", "passage", "questions"):
            if field not in p:
                problems.append(f"{tag}: missing field '{field}'")
        if p.get("id") in seen:
            problems.append(f"{tag}: duplicate id")
        seen.add(p.get("id"))
        for i, q in enumerate(p.get("questions", [])):
            qtag = q.get("id", f"{tag}-q{i}")
            for field in ("id", "stem", "options", "answer", "explanation", "difficulty"):
                if field not in q:
                    problems.append(f"{qtag}: missing field '{field}'")
            if q.get("id") in seen:
                problems.append(f"{qtag}: duplicate id")
            seen.add(q.get("id"))
            if q.get("difficulty") not in DIFFICULTIES:
                problems.append(f"{qtag}: bad difficulty {q.get('difficulty')!r}")
            opts = q.get("options", [])
            if len(opts) != 4:
                problems.append(f"{qtag}: expected 4 options, got {len(opts)}")
            ans = q.get("answer")
            if not isinstance(ans, int) or not 0 <= ans <= 3:
                problems.append(f"{qtag}: answer index out of range: {ans!r}")
        if not p.get("questions"):
            problems.append(f"{tag}: passage has no linked questions")
    return problems


def validate(bank):
    """Return a list of problems found in the bank (empty = healthy)."""
    problems = []
    seen = set()
    for i, q in enumerate(bank):
        tag = q.get("id", f"index-{i}")
        for field in ("id", "subject", "topic", "difficulty", "stem", "options", "answer", "explanation"):
            if field not in q:
                problems.append(f"{tag}: missing field '{field}'")
        if q.get("difficulty") not in DIFFICULTIES:
            problems.append(f"{tag}: bad difficulty {q.get('difficulty')!r}")
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

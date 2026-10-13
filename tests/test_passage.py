"""Passage tests: reading-comprehension data, flattening, validation, CLI."""

from ddcet_drill import engine, history
from ddcet_drill.cli import build_parser, cmd_passage
from ddcet_drill.questions import (load_bank, load_passages, passage_questions,
                                   question_index, shuffle_options,
                                   validate_passages)


def _linked(n=2):
    return [
        {"id": f"P-Q{i}", "stem": f"s{i}",
         "options": ["a", "b", "c", "d"], "answer": i % 4,
         "explanation": "e"}
        for i in range(n)
    ]


def _passage(pid="P-1", questions=None):
    return {"id": pid, "subject": "english",
            "topic": "reading-comprehension", "title": "T",
            "passage": "Some text.", "questions": _linked()
            if questions is None else questions}


def test_passages_load_and_flatten():
    passages = load_passages()
    assert len(passages) >= 1
    for p in passages:
        qs = passage_questions(p)
        assert len(qs) == len(p["questions"]) >= 1
        for q, orig in zip(qs, p["questions"]):
            assert q["id"] == orig["id"]
            assert q["subject"] == p["subject"]
            assert q["topic"] == p["topic"]
            assert q["passage_id"] == p["id"]
            assert q["passage_title"] == p["title"]


def test_passage_questions_do_not_mutate_source():
    p = _passage()
    before = [dict(q) for q in p["questions"]]
    passage_questions(p)
    assert p["questions"] == before
    assert all("passage_id" not in q for q in p["questions"])


def test_shipped_passages_validate_clean():
    bank = load_bank()
    problems = validate_passages(load_passages(),
                                 bank_ids=[q["id"] for q in bank])
    assert problems == []


def test_validate_catches_bad_passage():
    bank_ids = ["DR-001"]
    bad = _passage(pid="DR-001", questions=[  # collides with bank id
        {"id": "Q-DUP", "stem": "s", "options": ["a", "b"],  # 2 options
         "answer": 7, "explanation": "e"},  # answer out of range
        {"id": "Q-DUP", "stem": "s", "options": ["a", "b", "c", "d"],
         "answer": 0},  # missing explanation + duplicate id
    ])
    problems = validate_passages([bad], bank_ids=bank_ids)
    joined = "\n".join(problems)
    assert "duplicate id" in joined
    assert "expected 4 options, got 2" in joined
    assert "answer index out of range" in joined
    assert "missing field 'explanation'" in joined


def test_validate_rejects_passage_without_questions():
    p = _passage(questions=[])
    problems = validate_passages([p])
    assert any("no linked questions" in x for x in problems)


def test_validate_rejects_missing_passage_field():
    p = _passage()
    del p["title"]
    problems = validate_passages([p])
    assert any("missing field 'title'" in x for x in problems)


def test_question_index_covers_bank_and_passages():
    bank = load_bank()
    index = question_index(bank)
    for q in bank:
        assert index[q["id"]] is q
    for p in load_passages():
        for q in passage_questions(p):
            assert index[q["id"]]["passage_id"] == p["id"]


def test_shuffle_keeps_passage_scoring_correct():
    p = load_passages()[0]
    for q in shuffle_options(passage_questions(p), seed=9):
        orig = next(o for o in p["questions"] if o["id"] == q["id"])
        assert q["options"][q["answer"]] == orig["options"][orig["answer"]]
        pts, verdict = engine.score_answer(q, engine.LETTERS[q["answer"]])
        assert (pts, verdict) == (2.0, "correct")


def test_present_passage_prints_title(capsys):
    engine.present_passage(_passage(pid="P-9"))
    out = capsys.readouterr().out
    assert "T" in out
    assert "Some text." in out


def test_parser_accepts_passage_flags():
    p = build_parser()
    args = p.parse_args(["passage"])
    assert args.id is None and args.seed is None
    assert args.shuffle_options is False
    args = p.parse_args(["passage", "--id", "DR-P01", "--seed", "3",
                         "--shuffle-options"])
    assert args.id == "DR-P01" and args.seed == 3
    assert args.shuffle_options is True


def test_cmd_passage_logs_history_and_reports(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(history, "HIST_FILE", tmp_path / "history.jsonl")
    monkeypatch.setattr(engine, "ask", lambda q: "E")  # skip everything
    p = build_parser()
    args = p.parse_args(["passage", "--id", "DR-P01"])
    assert cmd_passage(args) == 0
    entries = history.read_history()
    assert len(entries) == 1
    assert entries[0]["mode"] == "passage"
    ids = [it["id"] for it in entries[0]["items"]]
    assert ids == [f"DR-P01-Q{i}" for i in range(1, 6)]
    assert all(it["subject"] == "english"
               and it["topic"] == "reading-comprehension"
               for it in entries[0]["items"])
    out = capsys.readouterr().out
    assert "The Waggle Dance" in out
    assert "Score: 0.0 / 10" in out


def test_cmd_passage_bad_id_fails(capsys):
    p = build_parser()
    args = p.parse_args(["passage", "--id", "NOPE"])
    assert cmd_passage(args) == 1
    assert "No passage" in capsys.readouterr().out

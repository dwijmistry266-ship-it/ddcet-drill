"""Tests for `stats --csv`: topic-wise stats export."""

import argparse
import csv

from ddcet_drill import cli, history


def _item(qid, verdict, secs=None, subject="physics", topic="units"):
    item = {"id": qid, "subject": subject, "topic": topic,
            "verdict": verdict, "pts": 0.0}
    if secs is not None:
        item["secs"] = secs
    return item


def _entry(items):
    return {"ts": 1, "mode": "practice", "items": items}


def _rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _args(**kwargs):
    ns = argparse.Namespace(csv=None)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _write_history(tmp_path, monkeypatch, entries):
    import json
    hist = tmp_path / "history.jsonl"
    if entries:
        with hist.open("w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")
    monkeypatch.setattr(history, "HIST_FILE", hist)
    return hist


def test_csv_export_writes_header_and_rows(tmp_path, monkeypatch):
    _write_history(tmp_path, monkeypatch, [
        _entry([_item("Q1", "correct", secs=10.0),
                _item("Q2", "wrong", secs=20.0),
                _item("Q3", "correct", secs=30.0)]),
        _entry([_item("Q4", "correct", subject="maths", topic="algebra")]),
    ])
    out = tmp_path / "stats.csv"
    assert cli.cmd_stats(_args(csv=str(out))) == 0
    rows = _rows(out)
    assert len(rows) == 2
    phys = next(r for r in rows if r["subject"] == "physics")
    assert phys["topic"] == "units"
    assert phys["correct"] == "2" and phys["attempted"] == "3"
    assert phys["accuracy_pct"] == "67"
    assert phys["avg_secs"] == "20.0"
    maths = next(r for r in rows if r["subject"] == "maths")
    assert maths["avg_secs"] == ""  # untimed entries -> no avg time


def test_csv_export_skips_skipped_verdicts(tmp_path, monkeypatch):
    _write_history(tmp_path, monkeypatch, [
        _entry([_item("Q1", "skipped"), _item("Q2", "wrong")]),
    ])
    out = tmp_path / "stats.csv"
    assert cli.cmd_stats(_args(csv=str(out))) == 0
    rows = _rows(out)
    assert len(rows) == 1
    assert rows[0]["correct"] == "0" and rows[0]["attempted"] == "1"
    assert rows[0]["accuracy_pct"] == "0"


def test_csv_export_no_history_prints_and_writes_nothing(tmp_path, monkeypatch,
                                                        capsys):
    hist = _write_history(tmp_path, monkeypatch, [])
    out = tmp_path / "stats.csv"
    assert cli.cmd_stats(_args(csv=str(out))) == 0
    assert "No attempts logged yet" in capsys.readouterr().out
    assert not out.exists() and not hist.exists()


def test_stats_still_prints_without_csv(tmp_path, monkeypatch, capsys):
    _write_history(tmp_path, monkeypatch, [
        _entry([_item("Q1", "correct")]),
    ])
    out = tmp_path / "stats.csv"
    assert cli.cmd_stats(_args()) == 0
    printed = capsys.readouterr().out
    assert "Attempts logged: 1" in printed
    assert "physics/units" in printed
    assert not out.exists()


def test_csv_export_prints_confirmation(tmp_path, monkeypatch, capsys):
    _write_history(tmp_path, monkeypatch, [
        _entry([_item("Q1", "correct")]),
    ])
    out = tmp_path / "stats.csv"
    cli.cmd_stats(_args(csv=str(out)))
    printed = capsys.readouterr().out
    assert "1 topic row(s)" in printed and str(out) in printed


def test_parser_accepts_csv_flag():
    args = cli.build_parser().parse_args(["stats", "--csv", "s.csv"])
    assert args.cmd == "stats" and args.csv == "s.csv"


def test_parser_csv_defaults_to_none():
    args = cli.build_parser().parse_args(["stats"])
    assert args.csv is None


def _subject_section(printed):
    return printed.split("Per-subject totals:")[1]


def test_stats_prints_per_subject_aggregates(tmp_path, monkeypatch, capsys):
    _write_history(tmp_path, monkeypatch, [
        _entry([_item("Q1", "correct", secs=10.0),
                _item("Q2", "wrong", secs=20.0)]),
        _entry([_item("Q3", "correct", secs=30.0,
                      topic="mechanics")]),
        _entry([_item("Q4", "correct", subject="maths",
                      topic="algebra")]),
    ])
    assert cli.cmd_stats(_args()) == 0
    section = _subject_section(capsys.readouterr().out)
    phys = next(line for line in section.splitlines() if "physics" in line)
    assert "2/3 correct (67%)" in phys and "20.0s avg" in phys
    maths = next(line for line in section.splitlines() if "maths" in line)
    assert "1/1 correct (100%)" in maths and "-" in maths


def test_stats_subject_aggregates_exclude_skipped(tmp_path, monkeypatch, capsys):
    _write_history(tmp_path, monkeypatch, [
        _entry([_item("Q1", "skipped"), _item("Q2", "wrong")]),
        _entry([_item("Q3", "skipped", subject="maths",
                      topic="algebra")]),
    ])
    assert cli.cmd_stats(_args()) == 0
    section = _subject_section(capsys.readouterr().out)
    phys = next(line for line in section.splitlines() if "physics" in line)
    assert "0/1 correct (0%)" in phys
    maths = next(line for line in section.splitlines() if "maths" in line)
    assert "0/0 correct (-)" in maths


def test_accuracy_and_time_by_subject_helpers():
    entries = [
        _entry([_item("Q1", "correct", secs=10.0),
                _item("Q2", "skipped")]),
        _entry([_item("Q3", "wrong", secs=30.0, topic="mechanics")]),
    ]
    assert history.accuracy_by_subject(entries) == {"physics": (1, 2)}
    assert history.time_by_subject(entries) == {"physics": (40.0, 2)}

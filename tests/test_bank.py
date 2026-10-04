"""Bank integrity tests: every question must be well-formed."""

from ddcet_drill.questions import load_bank, validate


def test_bank_loads():
    bank = load_bank()
    assert len(bank) >= 40, "seed bank should hold a solid set of questions"


def test_bank_valid():
    bank = load_bank()
    assert validate(bank) == []


def test_ids_unique():
    bank = load_bank()
    ids = [q["id"] for q in bank]
    assert len(ids) == len(set(ids))


def test_all_subjects_present():
    bank = load_bank()
    subjects = {q["subject"] for q in bank}
    for expected in ("physics", "chemistry", "computer", "environment",
                     "maths", "english", "soft-skills"):
        assert expected in subjects, f"missing subject: {expected}"

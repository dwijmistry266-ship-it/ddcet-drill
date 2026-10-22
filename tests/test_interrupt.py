"""Interrupt tests: Ctrl+C exits cleanly, no traceback, exit code 130."""

import contextlib
import io
from unittest import mock

from ddcet_drill import cli


def _run_main_with(func):
    """Call cli.main() with a stub command that runs `func` instead of argparse."""
    fake_args = mock.Mock()
    fake_args.func = func
    fake_parser = mock.Mock()
    fake_parser.parse_args.return_value = fake_args
    with mock.patch.object(cli, "build_parser", return_value=fake_parser):
        cli.main()


def _interrupted(_args):
    raise KeyboardInterrupt


def test_ctrl_c_exits_130_and_prints_clean_message():
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            _run_main_with(_interrupted)
    except SystemExit as e:
        assert e.code == 130
    else:
        raise AssertionError("main() did not raise SystemExit")
    out = buf.getvalue()
    assert "Interrupted" in out
    assert "not logged" in out
    assert "Traceback" not in out


def test_normal_return_code_still_passes_through():
    try:
        _run_main_with(lambda _args: 3)
    except SystemExit as e:
        assert e.code == 3
    else:
        raise AssertionError("main() did not raise SystemExit")

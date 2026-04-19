"""Regression tests for the clipboard_key paste path in dictate.py.

These tests pin the contract of:
- `_detect_paste_combo` (terminal vs non-terminal window class mapping)
- `paste_text_clipboard_key` (happy path, three subprocess failure modes)
- `copy_to_clipboard` (must route xclip/xsel stdout/stderr through DEVNULL
  so the forked daemon doesn't inherit open pipes and hang)
"""

import subprocess
from unittest.mock import patch, MagicMock, call

import pytest

from automation_scripts.dictation import dictate


# ---------------------------------------------------------------------------
# _detect_paste_combo
# ---------------------------------------------------------------------------

def _mock_xdotool(class_name: str):
    """Return a side_effect that mimics getactivewindow + getwindowclassname."""
    def side_effect(cmd, **kwargs):
        result = MagicMock()
        result.returncode = 0
        if cmd[:2] == ["xdotool", "getactivewindow"]:
            result.stdout = "12345\n"
        elif cmd[:2] == ["xdotool", "getwindowclassname"]:
            result.stdout = f"{class_name}\n"
        else:
            result.stdout = ""
        return result
    return side_effect


@pytest.mark.parametrize('class_name', [
    'Xfce4-terminal', 'xterm', 'URxvt', 'Alacritty', 'kitty',
    'WezTerm', 'gnome-terminal', 'Konsole',
])
def test_detect_paste_combo_terminal_uses_ctrl_shift_v(class_name):
    """Terminal window classes must map to ctrl+shift+v."""
    with patch.object(dictate.subprocess, 'run', side_effect=_mock_xdotool(class_name)):
        assert dictate._detect_paste_combo() == 'ctrl+shift+v'


@pytest.mark.parametrize('class_name', [
    'Cursor', 'Code', 'firefox', 'Brave-browser', 'Slack', 'obsidian',
])
def test_detect_paste_combo_non_terminal_uses_ctrl_v(class_name):
    """Non-terminal window classes must map to ctrl+v."""
    with patch.object(dictate.subprocess, 'run', side_effect=_mock_xdotool(class_name)):
        assert dictate._detect_paste_combo() == 'ctrl+v'


def test_detect_paste_combo_falls_back_when_xdotool_missing():
    """Missing xdotool must not raise; fall back to ctrl+v."""
    with patch.object(dictate.subprocess, 'run', side_effect=FileNotFoundError):
        assert dictate._detect_paste_combo() == 'ctrl+v'


def test_detect_paste_combo_falls_back_on_subprocess_error():
    """A subprocess failure must not propagate; fall back to ctrl+v."""
    with patch.object(dictate.subprocess, 'run',
                      side_effect=subprocess.SubprocessError("boom")):
        assert dictate._detect_paste_combo() == 'ctrl+v'


# ---------------------------------------------------------------------------
# paste_text_clipboard_key
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_clipboard_ok():
    """copy_to_clipboard is stubbed to succeed."""
    with patch.object(dictate, 'copy_to_clipboard', return_value=True) as m:
        yield m


def test_paste_text_clipboard_key_empty_text_returns_false():
    assert dictate.paste_text_clipboard_key("") is False


def test_paste_text_clipboard_key_aborts_when_clipboard_fails():
    """If clipboard copy fails, no keystroke should be sent."""
    with patch.object(dictate, 'copy_to_clipboard', return_value=False), \
         patch.object(dictate.subprocess, 'run') as run:
        assert dictate.paste_text_clipboard_key("hello") is False
        run.assert_not_called()


def test_paste_text_clipboard_key_happy_path_sends_xdotool_key(mock_clipboard_ok, monkeypatch):
    """Happy path: copy to clipboard, then xdotool key with --clearmodifiers."""
    monkeypatch.setitem(dictate.CONFIG, 'paste_key', 'ctrl+v')
    monkeypatch.setitem(dictate.CONFIG, 'clear_modifiers', False)

    with patch.object(dictate.subprocess, 'run') as run:
        run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        assert dictate.paste_text_clipboard_key("hello") is True

    mock_clipboard_ok.assert_called_once_with("hello")
    run.assert_called_once()
    args, kwargs = run.call_args
    assert args[0] == ["xdotool", "key", "--clearmodifiers", "ctrl+v"]
    assert kwargs.get('check') is True


def test_paste_text_clipboard_key_clears_modifiers_before_keystroke(mock_clipboard_ok, monkeypatch):
    """With clear_modifiers=True, a keyup burst must precede the paste key."""
    monkeypatch.setitem(dictate.CONFIG, 'paste_key', 'ctrl+v')
    monkeypatch.setitem(dictate.CONFIG, 'clear_modifiers', True)

    with patch.object(dictate.subprocess, 'run') as run, \
         patch.object(dictate.time, 'sleep'):
        run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        assert dictate.paste_text_clipboard_key("hello") is True

    # First call clears modifiers, second sends the paste key.
    assert run.call_args_list[0].args[0][:2] == ["xdotool", "keyup"]
    assert run.call_args_list[0].args[0][2:] == [
        "Control_L", "Control_R", "Shift_L", "Shift_R",
        "Alt_L", "Alt_R", "Super_L", "Super_R",
    ]
    assert run.call_args_list[1].args[0] == ["xdotool", "key", "--clearmodifiers", "ctrl+v"]


def test_paste_text_clipboard_key_auto_delegates_to_detect(mock_clipboard_ok, monkeypatch):
    """paste_key='auto' must consult _detect_paste_combo."""
    monkeypatch.setitem(dictate.CONFIG, 'paste_key', 'auto')
    monkeypatch.setitem(dictate.CONFIG, 'clear_modifiers', False)

    with patch.object(dictate, '_detect_paste_combo', return_value='shift+Insert') as detect, \
         patch.object(dictate.subprocess, 'run') as run:
        run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        assert dictate.paste_text_clipboard_key("hi") is True

    detect.assert_called_once()
    assert run.call_args.args[0] == ["xdotool", "key", "--clearmodifiers", "shift+Insert"]


def test_paste_text_clipboard_key_returns_false_on_timeout(mock_clipboard_ok, monkeypatch):
    monkeypatch.setitem(dictate.CONFIG, 'paste_key', 'ctrl+v')
    monkeypatch.setitem(dictate.CONFIG, 'clear_modifiers', False)
    with patch.object(dictate.subprocess, 'run',
                      side_effect=subprocess.TimeoutExpired(cmd="xdotool", timeout=5)), \
         patch.object(dictate, '_send_notification_static'):
        assert dictate.paste_text_clipboard_key("hi") is False


def test_paste_text_clipboard_key_returns_false_when_xdotool_missing(mock_clipboard_ok, monkeypatch):
    monkeypatch.setitem(dictate.CONFIG, 'paste_key', 'ctrl+v')
    monkeypatch.setitem(dictate.CONFIG, 'clear_modifiers', False)
    with patch.object(dictate.subprocess, 'run', side_effect=FileNotFoundError), \
         patch.object(dictate, '_send_notification_static'):
        assert dictate.paste_text_clipboard_key("hi") is False


def test_paste_text_clipboard_key_returns_false_on_called_process_error(mock_clipboard_ok, monkeypatch):
    monkeypatch.setitem(dictate.CONFIG, 'paste_key', 'ctrl+v')
    monkeypatch.setitem(dictate.CONFIG, 'clear_modifiers', False)
    err = subprocess.CalledProcessError(1, "xdotool", output=b"", stderr=b"no key named: bogus")
    with patch.object(dictate.subprocess, 'run', side_effect=err), \
         patch.object(dictate, '_send_notification_static'):
        assert dictate.paste_text_clipboard_key("hi") is False


# ---------------------------------------------------------------------------
# copy_to_clipboard — regression test for the xclip hang
# ---------------------------------------------------------------------------

def test_copy_to_clipboard_routes_xclip_output_to_devnull():
    """
    xclip/xsel fork a daemon that inherits the parent's open fds. If we pass
    capture_output=True, the daemon keeps the pipe ends alive and
    subprocess.run blocks until the timeout. Regression guard: the call must
    use DEVNULL for both stdout and stderr.
    """
    with patch.object(dictate.subprocess, 'run') as run:
        run.return_value = MagicMock(returncode=0)
        assert dictate.copy_to_clipboard("hi") is True

    args, kwargs = run.call_args
    assert args[0][0] == "xclip"
    assert kwargs.get('stdout') is subprocess.DEVNULL
    assert kwargs.get('stderr') is subprocess.DEVNULL
    # capture_output=True would re-enable the hang; must be absent/false.
    assert not kwargs.get('capture_output', False)


def test_copy_to_clipboard_falls_back_to_xsel():
    """If xclip is missing, xsel must be tried (and also with DEVNULL)."""
    def side_effect(cmd, **kwargs):
        if cmd[0] == "xclip":
            raise FileNotFoundError
        return MagicMock(returncode=0)

    with patch.object(dictate.subprocess, 'run', side_effect=side_effect) as run:
        assert dictate.copy_to_clipboard("hi") is True

    xsel_call = run.call_args_list[-1]
    assert xsel_call.args[0][0] == "xsel"
    assert xsel_call.kwargs.get('stdout') is subprocess.DEVNULL
    assert xsel_call.kwargs.get('stderr') is subprocess.DEVNULL


def test_copy_to_clipboard_returns_false_when_both_tools_missing():
    with patch.object(dictate.subprocess, 'run', side_effect=FileNotFoundError):
        assert dictate.copy_to_clipboard("hi") is False


def test_copy_to_clipboard_returns_false_on_timeout():
    with patch.object(dictate.subprocess, 'run',
                      side_effect=subprocess.TimeoutExpired(cmd="xclip", timeout=5)):
        assert dictate.copy_to_clipboard("hi") is False


def test_copy_to_clipboard_empty_text_returns_false():
    assert dictate.copy_to_clipboard("") is False

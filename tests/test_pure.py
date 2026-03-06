"""Tests for pure functions (no system dependencies)."""

from apple_mcp.applescript import escape
from apple_mcp.contacts import _label_constant, _normalize_phone


class TestEscape:
    def test_plain_text(self):
        assert escape("hello world") == "hello world"

    def test_double_quotes(self):
        assert escape('say "hi"') == 'say \\"hi\\"'

    def test_backslashes(self):
        assert escape("path\\to\\file") == "path\\\\to\\\\file"

    def test_both(self):
        assert escape('"\\') == '\\"\\\\'

    def test_empty(self):
        assert escape("") == ""


class TestNormalizePhone:
    def test_e164(self):
        assert _normalize_phone("+15551234567") == "+15551234567"

    def test_us_local(self):
        assert _normalize_phone("9255862537") == "+19255862537"

    def test_with_dashes(self):
        assert _normalize_phone("925-586-2537") == "+19255862537"

    def test_invalid_returns_original(self):
        assert _normalize_phone("abc") == "abc"


class TestLabelConstant:
    def test_mobile(self):
        assert _label_constant("mobile") == "_$!<Mobile>!$_"

    def test_case_insensitive(self):
        assert _label_constant("Home") == "_$!<Home>!$_"

    def test_unknown_passthrough(self):
        assert _label_constant("custom_label") == "custom_label"

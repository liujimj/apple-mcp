"""Read-only smoke tests against live macOS data.

These tests verify the AppleScript and PyObjC plumbing works on this machine.
They only read — no notes/contacts/reminders are created, modified, or deleted.

Skip with: pytest -m "not smoke"
"""

import pytest

pytestmark = pytest.mark.smoke


class TestNotes:
    def test_list_folders_returns_data(self):
        from apple_mcp.notes import list_folders

        result = list_folders()
        assert result
        assert "notes)" in result  # e.g. "Notes (220 notes)"

    def test_list_notes_returns_data(self):
        from apple_mcp.notes import list_notes

        result = list_notes(limit=3)
        assert result != "No notes found."
        assert "ID:" in result
        assert "Title:" in result

    def test_list_notes_with_folder(self):
        from apple_mcp.notes import list_notes

        result = list_notes(folder="Notes", limit=3)
        assert result != "No notes found."
        assert "ID:" in result

    def test_search_notes(self):
        from apple_mcp.notes import search_notes

        # Search for something likely to exist
        result = search_notes("the", limit=3)
        assert "No notes found" not in result or "ID:" in result

    def test_get_note_not_found(self):
        from apple_mcp.notes import get_note

        result = get_note("nonexistent_note_id_xyz_12345")
        assert "not found" in result.lower() or "NOT_FOUND" in result


class TestContacts:
    def test_search_contacts_returns_data(self):
        from apple_mcp.contacts import search_contacts

        result = search_contacts("Liu", limit=5)
        assert result
        assert "No contacts found" not in result

    def test_search_contacts_no_match(self):
        from apple_mcp.contacts import search_contacts

        result = search_contacts("zzzznonexistent99999", limit=5)
        assert "No contacts found" in result

    def test_get_contact_by_name(self):
        from apple_mcp.contacts import get_contact

        result = get_contact("Jian Liu")
        assert "Name:" in result
        assert "Identifier:" in result

    def test_get_contact_not_found(self):
        from apple_mcp.contacts import get_contact

        result = get_contact("Nonexistent Person ZZZZZ")
        assert "not found" in result.lower()


class TestReminders:
    def test_list_lists_returns_data(self):
        from apple_mcp.reminders import list_lists

        result = list_lists()
        assert result
        assert "incomplete)" in result  # e.g. "Reminders (3 incomplete)"

    def test_list_reminders(self):
        from apple_mcp.reminders import list_reminders

        result = list_reminders("Reminders", include_completed=True, limit=5)
        # May or may not have reminders, just verify it doesn't crash
        assert isinstance(result, str)

    def test_search_reminders_no_match(self):
        from apple_mcp.reminders import search_reminders

        result = search_reminders("zzzznonexistent99999")
        assert "No reminders found" in result


class TestServerRegistration:
    def test_all_tools_registered(self):
        from apple_mcp.server import mcp

        tools = mcp._tool_manager._tools
        expected = {
            "notes_list_folders", "notes_list", "notes_get",
            "notes_search", "notes_create", "notes_update",
            "contacts_search", "contacts_get",
            "contacts_create", "contacts_update",
            "reminders_list_lists", "reminders_list",
            "reminders_search", "reminders_create", "reminders_complete",
        }
        assert set(tools.keys()) == expected

    def test_tool_count(self):
        from apple_mcp.server import mcp

        tools = mcp._tool_manager._tools
        assert len(tools) == 15

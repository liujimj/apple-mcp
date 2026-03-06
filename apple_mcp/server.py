"""Apple MCP server — Notes, Contacts, Reminders via AppleScript + PyObjC."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from apple_mcp import contacts, notes, reminders

mcp = FastMCP("apple-mcp")

# ── Notes ────────────────────────────────────────────────────────────────────


@mcp.tool()
def notes_list_folders() -> str:
    """List all Apple Notes folders with note counts."""
    return notes.list_folders()


@mcp.tool()
def notes_list(folder: str | None = None, limit: int = 50) -> str:
    """List notes (title, id, dates), optionally by folder.

    Args:
        folder: Filter to a specific folder (optional)
        limit: Max notes to return (default 50)
    """
    return notes.list_notes(folder=folder, limit=limit)


@mcp.tool()
def notes_get(note_id: str) -> str:
    """Get full note content (HTML body) by ID or title.

    Args:
        note_id: Note ID (e.g. "x-coredata://...") or exact title
    """
    return notes.get_note(note_id)


@mcp.tool()
def notes_search(query: str, folder: str | None = None, limit: int = 20) -> str:
    """Search notes by title and plaintext content.

    Args:
        query: Search query (case-insensitive substring match)
        folder: Scope search to a specific folder (optional)
        limit: Max results (default 20)
    """
    return notes.search_notes(query, folder=folder, limit=limit)


@mcp.tool()
def notes_create(title: str, body: str, folder: str | None = None) -> str:
    """Create a new note in Apple Notes.

    Args:
        title: Note title
        body: Note body (HTML supported)
        folder: Target folder (optional, uses default if omitted)
    """
    return notes.create_note(title, body, folder=folder)


@mcp.tool()
def notes_update(note_id: str, body: str) -> str:
    """Update a note's body. Use notes_get first for read-then-write append.

    Args:
        note_id: Note ID or exact title
        body: New body content (HTML supported, replaces existing body)
    """
    return notes.update_note(note_id, body)


# ── Contacts ─────────────────────────────────────────────────────────────────


@mcp.tool()
def contacts_search(query: str, limit: int = 20) -> str:
    """Search contacts by name, phone number, or email address.

    Args:
        query: Name, phone number, or email to search for
        limit: Max results (default 20)
    """
    return contacts.search_contacts(query, limit=limit)


@mcp.tool()
def contacts_get(identifier: str) -> str:
    """Get complete contact details by identifier, name, phone, or email.

    Returns all available fields: name, phones, emails, addresses, organization, etc.

    Args:
        identifier: Contact identifier, full name, phone number, or email
    """
    return contacts.get_contact(identifier)


@mcp.tool()
def contacts_create(
    given_name: str,
    family_name: str = "",
    phones: list[dict[str, str]] | None = None,
    emails: list[dict[str, str]] | None = None,
    organization: str = "",
    job_title: str = "",
    note: str = "",
) -> str:
    """Create a new contact in macOS Contacts.

    Args:
        given_name: First name
        family_name: Last name
        phones: List of phone entries, e.g. [{"label": "mobile", "number": "+15551234567"}]
        emails: List of email entries, e.g. [{"label": "work", "address": "foo@bar.com"}]
        organization: Company name
        job_title: Job title
        note: Notes field
    """
    return contacts.create_contact(
        given_name=given_name,
        family_name=family_name,
        phones=phones,
        emails=emails,
        organization=organization,
        job_title=job_title,
        note=note,
    )


@mcp.tool()
def contacts_update(
    identifier: str,
    given_name: str | None = None,
    family_name: str | None = None,
    phones: list[dict[str, str]] | None = None,
    emails: list[dict[str, str]] | None = None,
    organization: str | None = None,
    job_title: str | None = None,
    note: str | None = None,
) -> str:
    """Update an existing contact's fields. Only specified fields are changed.

    Args:
        identifier: Contact identifier, full name, phone, or email
        given_name: New first name (omit to keep existing)
        family_name: New last name (omit to keep existing)
        phones: Replace all phones (omit to keep existing)
        emails: Replace all emails (omit to keep existing)
        organization: New organization (omit to keep existing)
        job_title: New job title (omit to keep existing)
        note: New note (omit to keep existing)
    """
    return contacts.update_contact(
        identifier=identifier,
        given_name=given_name,
        family_name=family_name,
        phones=phones,
        emails=emails,
        organization=organization,
        job_title=job_title,
        note=note,
    )


# ── Reminders ────────────────────────────────────────────────────────────────


@mcp.tool()
def reminders_list_lists() -> str:
    """List all reminder lists with incomplete reminder counts."""
    return reminders.list_lists()


@mcp.tool()
def reminders_list(
    list_name: str, include_completed: bool = False, limit: int = 50
) -> str:
    """List reminders in a specific list.

    Args:
        list_name: Name of the reminder list
        include_completed: Include completed reminders (default False)
        limit: Max reminders to return (default 50)
    """
    return reminders.list_reminders(list_name, include_completed=include_completed, limit=limit)


@mcp.tool()
def reminders_search(query: str, limit: int = 20) -> str:
    """Search reminders by title across all lists.

    Args:
        query: Search query (case-insensitive substring match on title)
        limit: Max results (default 20)
    """
    return reminders.search_reminders(query, limit=limit)


@mcp.tool()
def reminders_create(
    title: str,
    list_name: str | None = None,
    due_date: str | None = None,
    priority: int | None = None,
    notes: str | None = None,
) -> str:
    """Create a new reminder.

    Args:
        title: Reminder title
        list_name: Target list (uses default list if omitted)
        due_date: Due date as "YYYY-MM-DD" or "YYYY-MM-DD HH:MM"
        priority: 0 (none), 1 (high), 5 (medium), 9 (low)
        notes: Body/notes text
    """
    return reminders.create_reminder(
        title, list_name=list_name, due_date=due_date, priority=priority, notes=notes
    )


@mcp.tool()
def reminders_complete(title: str, list_name: str) -> str:
    """Mark a reminder as complete.

    Args:
        title: Exact title of the reminder
        list_name: Name of the list containing the reminder
    """
    return reminders.complete_reminder(title, list_name)


# ── Entry point ──────────────────────────────────────────────────────────────


def main():
    """Run the Apple MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

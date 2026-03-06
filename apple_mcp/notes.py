"""Apple Notes access via AppleScript."""

from __future__ import annotations

from apple_mcp.applescript import escape, run


def list_folders() -> str:
    """List all Notes folders with note counts."""
    script = '''
        tell application "Notes"
            set output to ""
            repeat with f in folders
                set fName to name of f
                set nCount to count of notes of f
                set output to output & fName & "\t" & nCount & "\n"
            end repeat
            return output
        end tell
    '''
    raw = run(script)
    if not raw:
        return "No folders found."

    lines = []
    for line in raw.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) == 2:
            lines.append(f"{parts[0]} ({parts[1]} notes)")
    return "\n".join(lines) if lines else "No folders found."


def list_notes(folder: str | None = None, limit: int = 50) -> str:
    """List notes (title, id, dates), optionally filtered by folder."""
    if folder:
        script = f'''
            tell application "Notes"
                set f to folder "{escape(folder)}"
                set output to ""
                set i to 0
                repeat with n in notes of f
                    if i >= {limit} then exit repeat
                    set nId to id of n
                    set nTitle to name of n
                    set nCreated to creation date of n as text
                    set nModified to modification date of n as text
                    set output to output & nId & "\t" & nTitle & "\t" & nCreated & "\t" & nModified & "\n"
                    set i to i + 1
                end repeat
                return output
            end tell
        '''
    else:
        script = f'''
            tell application "Notes"
                set output to ""
                set i to 0
                repeat with n in notes
                    if i >= {limit} then exit repeat
                    set nId to id of n
                    set nTitle to name of n
                    set nCreated to creation date of n as text
                    set nModified to modification date of n as text
                    set output to output & nId & "\t" & nTitle & "\t" & nCreated & "\t" & nModified & "\n"
                    set i to i + 1
                end repeat
                return output
            end tell
        '''
    raw = run(script, timeout=60)
    if not raw:
        return "No notes found."

    lines = []
    for line in raw.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) == 4:
            lines.append(f"ID: {parts[0]}\nTitle: {parts[1]}\nCreated: {parts[2]}\nModified: {parts[3]}")
    return "\n\n".join(lines) if lines else "No notes found."


def get_note(note_id: str) -> str:
    """Get full note content (HTML body) by ID or title.

    Tries ID match first, falls back to title match.
    """
    # Try by ID first
    script = f'''
        tell application "Notes"
            try
                set n to note id "{escape(note_id)}"
                set nTitle to name of n
                set nBody to body of n
                set nCreated to creation date of n as text
                set nModified to modification date of n as text
                try
                    set nFolder to name of container of n
                on error
                    set nFolder to "(unknown)"
                end try
                return nTitle & "\t" & nFolder & "\t" & nCreated & "\t" & nModified & "\t" & nBody
            end try
            -- Fall back to title match
            repeat with n in notes
                if name of n is "{escape(note_id)}" then
                    set nTitle to name of n
                    set nBody to body of n
                    set nId to id of n
                    set nCreated to creation date of n as text
                    set nModified to modification date of n as text
                    try
                        set nFolder to name of container of n
                    on error
                        set nFolder to "(unknown)"
                    end try
                    return nId & "\t" & nTitle & "\t" & nFolder & "\t" & nCreated & "\t" & nModified & "\t" & nBody
                end if
            end repeat
            return "NOT_FOUND"
        end tell
    '''
    raw = run(script, timeout=60)
    if raw == "NOT_FOUND":
        return f"Note not found: {note_id}"

    parts = raw.split("\t")
    if len(parts) >= 5:
        # ID lookup: title, folder, created, modified, body
        return (
            f"Title: {parts[0]}\n"
            f"Folder: {parts[1]}\n"
            f"Created: {parts[2]}\n"
            f"Modified: {parts[3]}\n"
            f"---\n{'\t'.join(parts[4:])}"
        )
    return raw


def search_notes(query: str, folder: str | None = None, limit: int = 20) -> str:
    """Search notes by title + plaintext content."""
    escaped_query = escape(query).lower()

    if folder:
        scope = f'notes of folder "{escape(folder)}"'
    else:
        scope = "notes"

    script = f'''
        tell application "Notes"
            set output to ""
            set i to 0
            repeat with n in {scope}
                if i >= {limit} then exit repeat
                set nTitle to name of n
                set nPlain to plaintext of n
                if (nTitle as text) contains "{escaped_query}" or (nPlain as text) contains "{escaped_query}" then
                    set nId to id of n
                    try
                        set nFolder to name of container of n
                    on error
                        set nFolder to "(unknown)"
                    end try
                    set nModified to modification date of n as text
                    -- Grab first 200 chars of plaintext as snippet
                    if length of nPlain > 200 then
                        set snippet to text 1 thru 200 of nPlain
                    else
                        set snippet to nPlain
                    end if
                    set output to output & nId & "\t" & nTitle & "\t" & nFolder & "\t" & nModified & "\t" & snippet & "\n"
                    set i to i + 1
                end if
            end repeat
            return output
        end tell
    '''
    raw = run(script, timeout=120)
    if not raw:
        return f'No notes found matching "{query}".'

    lines = []
    for line in raw.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) >= 5:
            lines.append(
                f"ID: {parts[0]}\n"
                f"Title: {parts[1]}\n"
                f"Folder: {parts[2]}\n"
                f"Modified: {parts[3]}\n"
                f"Snippet: {parts[4][:200]}"
            )
    return "\n\n".join(lines) if lines else f'No notes found matching "{query}".'


def create_note(title: str, body: str, folder: str | None = None) -> str:
    """Create a note with HTML body."""
    escaped_title = escape(title)
    escaped_body = escape(body)

    if folder:
        script = f'''
            tell application "Notes"
                set f to folder "{escape(folder)}"
                set n to make new note at f with properties {{name:"{escaped_title}", body:"{escaped_body}"}}
                return id of n
            end tell
        '''
    else:
        script = f'''
            tell application "Notes"
                set n to make new note with properties {{name:"{escaped_title}", body:"{escaped_body}"}}
                return id of n
            end tell
        '''
    note_id = run(script)
    return f"Created note '{title}' (ID: {note_id})"


def update_note(note_id: str, body: str) -> str:
    """Update note body (HTML). Use get_note first to read-then-write for append."""
    escaped_body = escape(body)

    script = f'''
        tell application "Notes"
            try
                set n to note id "{escape(note_id)}"
                set body of n to "{escaped_body}"
                return "OK"
            end try
            -- Fall back to title match
            repeat with n in notes
                if name of n is "{escape(note_id)}" then
                    set body of n to "{escaped_body}"
                    return "OK"
                end if
            end repeat
            return "NOT_FOUND"
        end tell
    '''
    result = run(script, timeout=30)
    if result == "NOT_FOUND":
        return f"Note not found: {note_id}"
    return f"Updated note {note_id}"

"""Apple Reminders access via AppleScript."""

from __future__ import annotations

from apple_mcp.applescript import escape, run


def list_lists() -> str:
    """List all reminder lists with counts."""
    script = '''
        tell application "Reminders"
            set output to ""
            repeat with l in lists
                set lName to name of l
                set rCount to count of (reminders of l whose completed is false)
                set output to output & lName & "\t" & rCount & "\n"
            end repeat
            return output
        end tell
    '''
    raw = run(script)
    if not raw:
        return "No reminder lists found."

    lines = []
    for line in raw.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) == 2:
            lines.append(f"{parts[0]} ({parts[1]} incomplete)")
    return "\n".join(lines) if lines else "No reminder lists found."


def list_reminders(
    list_name: str, include_completed: bool = False, limit: int = 50
) -> str:
    """List reminders in a specific list."""
    escaped_list = escape(list_name)

    # Avoid "whose completed is false" — it's extremely slow with many reminders.
    # Instead iterate all and filter in the loop.
    if include_completed:
        skip_check = "false"
    else:
        skip_check = "true"

    script = f'''
        tell application "Reminders"
            set l to list "{escaped_list}"
            set output to ""
            set i to 0
            repeat with r in reminders of l
                if i >= {limit} then exit repeat
                set rDone to completed of r
                if {skip_check} and rDone then
                    -- skip completed
                else
                    set rName to name of r
                    set rPri to priority of r
                    set rNotes to body of r
                    if rNotes is missing value then set rNotes to ""
                    try
                        set rDue to due date of r as text
                    on error
                        set rDue to ""
                    end try
                    set doneText to "[ ]"
                    if rDone then set doneText to "[x]"
                    set output to output & doneText & "\t" & rName & "\t" & rDue & "\t" & rPri & "\t" & rNotes & "\n"
                    set i to i + 1
                end if
            end repeat
            return output
        end tell
    '''
    raw = run(script, timeout=60)
    if not raw:
        return f"No reminders found in '{list_name}'."

    lines = []
    for line in raw.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) >= 4:
            status = parts[0]
            name = parts[1]
            due = parts[2]
            priority = parts[3]
            notes = parts[4] if len(parts) > 4 else ""

            entry = f"{status} {name}"
            if due:
                entry += f" (due: {due})"
            if priority and priority != "0":
                entry += f" [priority: {priority}]"
            if notes:
                entry += f"\n   Notes: {notes}"
            lines.append(entry)
    return "\n".join(lines) if lines else f"No reminders found in '{list_name}'."


def search_reminders(query: str, limit: int = 20) -> str:
    """Search reminders by title across all lists."""
    escaped_query = escape(query).lower()

    script = f'''
        tell application "Reminders"
            set output to ""
            set i to 0
            repeat with l in lists
                set lName to name of l
                repeat with r in reminders of l
                    if i >= {limit} then exit repeat
                    set rName to name of r
                    if (rName as text) contains "{escaped_query}" then
                        set rDone to completed of r
                        try
                            set rDue to due date of r as text
                        on error
                            set rDue to ""
                        end try
                        set doneText to "[ ]"
                        if rDone then set doneText to "[x]"
                        set output to output & doneText & "\t" & rName & "\t" & lName & "\t" & rDue & "\n"
                        set i to i + 1
                    end if
                end repeat
            end repeat
            return output
        end tell
    '''
    raw = run(script, timeout=120)
    if not raw:
        return f'No reminders found matching "{query}".'

    lines = []
    for line in raw.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) >= 3:
            status = parts[0]
            name = parts[1]
            list_name = parts[2]
            due = parts[3] if len(parts) > 3 else ""

            entry = f"{status} {name} [{list_name}]"
            if due:
                entry += f" (due: {due})"
            lines.append(entry)
    return "\n".join(lines) if lines else f'No reminders found matching "{query}".'


def create_reminder(
    title: str,
    list_name: str | None = None,
    due_date: str | None = None,
    priority: int | None = None,
    notes: str | None = None,
) -> str:
    """Create a reminder.

    Args:
        title: Reminder title
        list_name: Target list (default: default list)
        due_date: Due date as "YYYY-MM-DD" or "YYYY-MM-DD HH:MM"
        priority: 0 (none), 1 (high), 5 (medium), 9 (low)
        notes: Body/notes text
    """
    escaped_title = escape(title)

    props = [f'name:"{escaped_title}"']
    if notes:
        props.append(f'body:"{escape(notes)}"')
    if priority is not None:
        props.append(f"priority:{priority}")

    props_str = "{" + ", ".join(props) + "}"

    if due_date:
        # Parse date and set it separately since AppleScript date parsing is fragile
        date_script = f'set rDue to date "{escape(due_date)}"'
        set_due = "set due date of r to rDue"
    else:
        date_script = ""
        set_due = ""

    if list_name:
        target = f'list "{escape(list_name)}"'
    else:
        target = "default list"

    script = f'''
        tell application "Reminders"
            {date_script}
            set r to make new reminder at {target} with properties {props_str}
            {set_due}
            return name of r
        end tell
    '''
    result = run(script)
    return f"Created reminder: {result}"


def complete_reminder(title: str, list_name: str) -> str:
    """Mark a reminder as complete."""
    escaped_title = escape(title)
    escaped_list = escape(list_name)

    script = f'''
        tell application "Reminders"
            set l to list "{escaped_list}"
            repeat with r in (reminders of l whose completed is false)
                if name of r is "{escaped_title}" then
                    set completed of r to true
                    return "OK"
                end if
            end repeat
            return "NOT_FOUND"
        end tell
    '''
    result = run(script)
    if result == "NOT_FOUND":
        return f"Reminder not found: {title} in {list_name}"
    return f"Completed reminder: {title}"

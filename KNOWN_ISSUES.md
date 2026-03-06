# Apple MCP — Known Issues & Workarounds

## 1. `notes_get` fails on notes with unresolvable containers

**Symptom**: `notes_get` returns "Note not found" for notes that clearly exist (confirmed by `notes_search` and `notes_list`). Or throws: `execution error: Notes got an error: Can't get name of container of item 1 of every note. (-1728)`

**Root Cause**: Some Apple Notes have containers (folders) that AppleScript cannot resolve — typically notes in the default "Notes" account folder, orphaned notes, or Recently Deleted notes. The original `get_note()` had a broad `try` block around the ID lookup that caught the container error along with genuine "not found" errors, making it silently fall through to the title-matching loop. The title loop also lacked container error handling and would crash.

**Fix (2026-03-06)**: Wrapped `name of container of n` in its own `try/on error` block in both the ID-lookup and title-fallback paths of `get_note()`, matching the pattern already used in `search_notes()`. Falls back to `"(unknown)"` for folder name.

**Workaround** (if using old server): Use direct AppleScript via Bash:
```bash
osascript -e '
tell application "Notes"
    set theNotes to every note whose name contains "Note Title"
    if (count of theNotes) > 0 then
        return plaintext of item 1 of theNotes
    end if
end tell
'
```

**Note**: MCP servers are long-lived stdio processes. Code changes require session restart to take effect.

## 2. AppleScript `whose` clause is slow on Reminders

**Symptom**: `reminders_list` with filter (e.g., `whose completed is false`) times out on lists with many items.

**Root Cause**: AppleScript's `whose` clause performs poorly on Reminders — it's essentially O(n) with high constant overhead.

**Fix**: Use iterate-and-filter pattern instead of `whose` clause. Already applied in `reminders.py`.

## 3. Multiple MCP server instances accumulate

**Symptom**: `ps aux | grep apple_mcp` shows many instances across Claude Code sessions.

**Root Cause**: Each Claude Code session spawns its own MCP server process. Old sessions that weren't cleanly terminated leave orphan processes.

**Workaround**: Periodically clean up stale processes:
```bash
# Kill all apple-mcp instances (will restart on next MCP call)
pkill -f "apple_mcp.server"
```

## General Patterns

- **Container access** on Apple Notes is unreliable — always wrap `name of container of n` in `try/on error`
- **Error messages** should be clean and actionable — the `AppleScriptError` class strips raw script source
- **Timeouts**: Default 30s for most operations, 60s for list/get operations, 120s for search
- **Case sensitivity**: AppleScript string comparison (`is`) is case-insensitive by default, but `contains` respects case in some contexts — use `.lower()` on the Python side for search queries

"""`roadgram agent install`: teach coding assistants (Claude Code, Codex, Cline, Cursor, Gemini CLI) to use roadgram.

One shared instruction text is written in each tool's own format. Files that roadgram owns are overwritten;
shared files (AGENTS.md, GEMINI.md) only get a marked block that is replaced on re-install and removed by --uninstall.
"""
import os
import re
from pathlib import Path

BEGIN, END = "<!-- roadgram:begin -->", "<!-- roadgram:end -->"

DESCRIPTION = ("Keep the project roadmap in sync with the Telegram group using the roadgram CLI. "
               "Use when the user asks to update/sync the roadmap, tick tasks, post a weekly plan, "
               "or announce something to the project Telegram group.")

BODY = """# roadgram: roadmap and plan in Telegram

`roadgram` publishes `ROADMAP.md` (a Markdown checklist) to a Telegram group. Messages are edited in place.

## When to use
- A task from `ROADMAP.md` is finished: change its `- [ ]` to `- [x]`, then run `roadgram sync`.
- The user asks for progress: run `roadgram status` (sends nothing).
- The user wants an announcement or a file sent to the group: run `roadgram post --text "..."` or `--document <file>`.
- First use in a project (no `roadgram.json`): run `roadgram init --name "<name>"`, then ask the user to fill `.env`, then `roadgram check`.

## Commands
| Command | Effect |
|---|---|
| `roadgram status` | progress per week, sends nothing |
| `roadgram sync` | edits every posted message; posts the next week when the current one is fully ticked |
| `roadgram week N [--dry-run]` | post/edit the roadmap message of week N |
| `roadgram plan N [--dry-run]` | post/edit the plan message of week N |
| `roadgram post --text "..." [--topic updates] [--pin]` | send a NEW message (explicit announcement) |
| `roadgram check` | verify token, group, topics and bot rights |

## Rules
- Never open, print, copy or commit `.env`. It holds the bot token. Never put the token in a command line.
- `roadgram post`, `roadgram week` and `roadgram plan` send to real people: use `--dry-run` first and send only what the user asked for.
- `roadgram sync` is safe to run after every `ROADMAP.md` change; it only edits existing messages (and advances a finished week).
- Only tick a task `[x]` when the work is really done and verified.
- Headings must look like `## Week 1: Title` (or `## هفته ۱: عنوان`); tasks are `- [ ]` / `- [x]` lines.
- If the command is not found, tell the user to install it: `pipx install git+https://github.com/alipyth/roadgram`.
"""

SYNC_COMMAND = """---
description: Sync ROADMAP.md progress to the Telegram group (roadgram sync)
allowed-tools: Bash(roadgram status:*), Bash(roadgram sync:*)
---
Run `roadgram status`, then `roadgram sync`, and report the result in one or two lines. Do not read `.env`.
"""

PLUGIN_JSON = """{
  "name": "roadgram",
  "version": "0.1.0",
  "description": "Roadmap, weekly plan and announcements in a Telegram group, driven by the roadgram CLI.",
  "license": "MIT"
}
"""


def skill_md() -> str:
    return f"---\nname: roadgram\ndescription: {DESCRIPTION}\n---\n\n{BODY}"


def cursor_mdc() -> str:
    return f"---\ndescription: {DESCRIPTION}\nalwaysApply: false\n---\n\n{BODY}"


def cline_md() -> str:
    return BODY


# tool -> (project files, global files); each file is (path relative to base, content, mode)
# mode "file" = roadgram owns the file, "block" = marked block inside a shared file.
def targets(tool: str, base: Path, home: Path, is_global: bool):
    if tool == "claude":
        root = home / ".claude" if is_global else base / ".claude"
        files = [(root / "skills" / "roadgram" / "SKILL.md", skill_md(), "file"),
                 (root / "commands" / "roadgram-sync.md", SYNC_COMMAND, "file")]
        if not is_global:  # also make the project installable as a plugin
            files += [(base / ".claude-plugin" / "plugin.json", PLUGIN_JSON, "file"),
                      (base / "skills" / "roadgram" / "SKILL.md", skill_md(), "file")]
        return files
    if tool == "codex":
        return [((home / ".codex" if is_global else base) / "AGENTS.md", BODY, "block")]
    if tool == "cline":
        if is_global:
            docs = Path(os.environ.get("CLINE_RULES_DIR") or home / "Documents" / "Cline" / "Rules")
            return [(docs / "roadgram.md", cline_md(), "file")]
        return [(base / ".clinerules" / "roadgram.md", cline_md(), "file")]
    if tool == "cursor":
        if is_global:
            return []  # Cursor user rules live in its settings UI, not in files
        return [(base / ".cursor" / "rules" / "roadgram.mdc", cursor_mdc(), "file")]
    if tool == "gemini":
        return [((home / ".gemini" if is_global else base) / "GEMINI.md", BODY, "block")]
    raise ValueError(tool)


TOOLS = ("claude", "codex", "cline", "cursor", "gemini")
BLOCK_RE = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", re.S)


def _write_block(path: Path, body: str) -> str:
    block = f"{BEGIN}\n{body.rstrip()}\n{END}\n"
    text = path.read_text(encoding="utf-8-sig") if path.exists() else ""
    if BLOCK_RE.search(text):
        new, action = BLOCK_RE.sub(lambda _: block, text, count=1), "updated"
    else:
        new, action = (text.rstrip("\n") + "\n\n" if text.strip() else "") + block, "added block to"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(new, encoding="utf-8")
    return action


def _remove(path: Path, mode: str) -> str:
    if not path.exists():
        return ""
    if mode == "file":
        path.unlink()
        for parent in (path.parent, path.parent.parent):  # drop now-empty dirs we created
            try:
                parent.rmdir()
            except OSError:
                break
        return "removed"
    text = path.read_text(encoding="utf-8-sig")
    if not BLOCK_RE.search(text):
        return ""
    new = BLOCK_RE.sub("", text).strip("\n")
    if new:
        path.write_text(new + "\n", encoding="utf-8")
    else:
        path.unlink()
    return "removed block from"


def detect(base: Path, home: Path):
    """Tools that look installed or already used in this project."""
    import shutil
    marks = {"claude": [home / ".claude", base / ".claude"], "codex": [home / ".codex", base / "AGENTS.md"],
             "cline": [base / ".clinerules", home / "Documents" / "Cline"],
             "cursor": [base / ".cursor"], "gemini": [home / ".gemini", base / "GEMINI.md"]}
    return [t for t in TOOLS if shutil.which(t) or any(m.exists() for m in marks[t])]


def run(tools, base: Path, home: Path, is_global=False, uninstall=False, dry_run=False):
    """Returns a list of human-readable result lines."""
    lines = []
    for tool in tools:
        files = targets(tool, base, home, is_global)
        if not files:
            lines.append(f"- {tool}: nothing to install {'globally' if is_global else 'in the project'} "
                         f"(Cursor user rules are set in its settings UI; use the project install)")
            continue
        for path, content, mode in files:
            if dry_run:
                lines.append(f"- {tool}: would {'remove' if uninstall else 'write'} {path}")
            elif uninstall:
                done = _remove(path, mode)
                if done:
                    lines.append(f"- {tool}: {done} {path}")
            else:
                if mode == "file":
                    path.parent.mkdir(parents=True, exist_ok=True)
                    existed = path.exists()
                    path.write_text(content, encoding="utf-8")
                    lines.append(f"- {tool}: {'updated' if existed else 'created'} {path}")
                else:
                    lines.append(f"- {tool}: {_write_block(path, content)} {path}")
    return lines

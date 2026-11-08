"""Command line: roadgram init | check | status | week N | plan N | sync | post."""
import argparse
import html
import sys
from datetime import date
from pathlib import Path

from roadgram import __version__, agents
from roadgram.i18n import SAMPLE_ROADMAP
from roadgram.manager import CONFIG_NAME, Manager, State, default_config, find_root, load_config
from roadgram.roadmap import parse_roadmap, render_plan, render_week
from roadgram.telegram import Bot, credentials

ENV_TEMPLATE = """# Keep this file private. Never commit it.
# Token: talk to @BotFather -> /newbot (or /token for an existing bot).
TELEGRAM_BOT_TOKEN=
# Group id: add the bot to your group, then forward a group message to @RawDataBot to read the chat id.
# Supergroup ids look like -1001234567890.
TELEGRAM_CHAT_ID=
"""
GITIGNORE_LINES = [".env", ".roadgram/"]


def out(msg: str = ""):
    print(msg)


def cmd_init(a) -> int:
    root = Path(a.dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    cfg_path = root / CONFIG_NAME
    if cfg_path.exists() and not a.force:
        out(f"{CONFIG_NAME} already exists here (use --force to overwrite).")
        return 1
    import json
    cfg = default_config(a.name or root.name, a.lang, a.calendar)
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    created = [CONFIG_NAME]
    for name, content in ((".env", ENV_TEMPLATE), (cfg["roadmap_file"], SAMPLE_ROADMAP[a.lang])):
        p = root / name
        if not p.exists():
            p.write_text(content, encoding="utf-8")
            created.append(name)
    gi = root / ".gitignore"
    existing = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    missing = [line for line in GITIGNORE_LINES if line not in existing]
    if missing:
        gi.write_text("\n".join(existing + missing) + "\n", encoding="utf-8")
        created.append(".gitignore")
    out("Created/updated: " + ", ".join(created))
    out("Next: fill TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env, then run: roadgram check")
    return 0


def cmd_agent(a) -> int:
    base, home = Path(a.dir).resolve(), Path.home()
    names = a.tools or ["auto"]
    if "all" in names:
        tools = list(agents.TOOLS)
    elif "auto" in names:
        tools = agents.detect(base, home)
        if not tools:
            out("No supported editor or terminal tool detected. Name one: " + ", ".join(agents.TOOLS) + " (or: all).")
            return 1
        out("Detected: " + ", ".join(tools))
    else:
        tools = names
    lines = agents.run(tools, base, home, a.is_global, a.uninstall, a.dry_run)
    out(chr(10).join(lines) if lines else "Nothing to do.")
    if not a.uninstall and not a.dry_run:
        out("Done. Restart the agent (or open a new session) so it picks the instructions up.")
    return 0


def project(a):
    root = find_root(Path(a.dir).resolve())
    if root is None:
        out(f"No {CONFIG_NAME} found. Run `roadgram init` in your project folder first.")
        return None
    return root, load_config(root)


def load_weeks(root: Path, cfg: dict):
    p = root / cfg["roadmap_file"]
    if not p.exists():
        out(f"Roadmap file not found: {cfg['roadmap_file']}")
        return None
    weeks = parse_roadmap(p.read_text(encoding="utf-8-sig"))
    if not weeks:
        out("No weeks found. Headings must look like '## Week 1: Title' (or '## هفته ۱: عنوان').")
        return None
    return weeks


def make_manager(root: Path, cfg: dict):
    token, chat = credentials(root)
    if not token or not chat:
        out("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env (or the environment).")
        return None
    return Manager(cfg, Bot(token, chat), State(root))


def cmd_check(a) -> int:
    p = project(a)
    if not p:
        return 2
    root, cfg = p
    mgr = make_manager(root, cfg)
    if not mgr:
        return 2
    bot, ok = mgr.bot, True
    me = bot.me()
    if not me.get("ok"):
        out(f"✗ token rejected: {me.get('description')}")
        return 1
    out(f"✓ bot: @{me['result'].get('username')}")
    chat = bot.chat_info()
    if not chat.get("ok"):
        out(f"✗ cannot see the group: {chat.get('description')} (is the bot added to it? is the chat id right?)")
        return 1
    c = chat["result"]
    out(f"✓ group: {c.get('title')} ({c.get('type')})")
    forum = bool(c.get("is_forum"))
    out("✓ topics are enabled" if forum else "! topics are OFF: messages go to the main chat "
        "(enable Topics in the group settings for one topic per section)")
    member = bot.my_member(me["result"]["id"])
    m = member.get("result", {}) if member.get("ok") else {}
    if m.get("status") not in ("administrator", "creator"):
        out("✗ the bot is not an admin: make it admin (pin messages" + (", manage topics" if forum else "") + ")")
        ok = False
    else:
        out("✓ the bot is an admin")
        if not m.get("can_pin_messages", True):
            out("✗ missing right: Pin messages")
            ok = False
        if forum and not m.get("can_manage_topics", True):
            out("✗ missing right: Manage topics")
            ok = False
    return 0 if ok else 1


def cmd_status(a) -> int:
    p = project(a)
    if not p:
        return 2
    root, cfg = p
    weeks = load_weeks(root, cfg)
    if not weeks:
        return 2
    for n, w in sorted(weeks.items()):
        done = sum(1 for d, _ in w["items"] if d)
        out(f"week {n}: {done}/{len(w['items'])}  {w['title']}")
    return 0


def week_arg(weeks: dict, n: int) -> bool:
    if n not in weeks:
        out(f"week {n} not found in the roadmap (found: {', '.join(str(k) for k in sorted(weeks))})")
        return False
    return True


def cmd_week_or_plan(a) -> int:
    p = project(a)
    if not p:
        return 2
    root, cfg = p
    weeks = load_weeks(root, cfg)
    if not weeks or not week_arg(weeks, a.n):
        return 2
    today = date.today()
    if a.dry_run:
        text = render_week(cfg, a.n, weeks[a.n], today) if a.cmd == "week" else \
            render_plan(cfg, a.n, weeks[a.n], weeks.get(a.n - 1), today)
        out(text)
        return 0
    mgr = make_manager(root, cfg)
    if not mgr:
        return 2
    result = mgr.week(weeks, a.n, today) if a.cmd == "week" else mgr.plan(weeks, a.n, today)
    out(result)
    return 1 if "failed" in result else 0


def cmd_sync(a) -> int:
    p = project(a)
    if not p:
        return 2
    root, cfg = p
    weeks = load_weeks(root, cfg)
    if not weeks:
        return 2
    mgr = make_manager(root, cfg)
    if not mgr:
        return 2
    results = mgr.sync(weeks, date.today())
    out("\n".join(results) if results else "Nothing posted yet. Start with: roadgram week 1  and  roadgram plan 2")
    return 1 if any("failed" in r for r in results) else 0


def cmd_post(a) -> int:
    p = project(a)
    if not p:
        return 2
    root, cfg = p
    text = a.text if a.text is not None else (Path(a.file).read_text(encoding="utf-8-sig") if a.file else "")
    document = Path(a.document) if a.document else None
    if not text and not document:
        out("Give --text, --file or --document.")
        return 2
    if document and not document.exists():
        out(f"File not found: {document}")
        return 2
    if not a.raw_html:
        text = html.escape(text, quote=False)
    if a.dry_run:
        out(text or f"(document: {document.name})")
        return 0
    mgr = make_manager(root, cfg)
    if not mgr:
        return 2
    try:
        thread = mgr.thread(a.topic)
    except RuntimeError as e:
        out(f"failed: {e}")
        return 1
    if document:
        r = mgr.bot.send_document(document, text[:1000], thread)
    else:
        r = mgr.bot.send(text, thread)
    if not r.get("ok"):
        out(f"failed: {r.get('description')}")
        return 1
    mid = r["result"]["message_id"]
    if a.pin:
        mgr.bot.pin(mid)
    out(f"posted message {mid}" + (" and pinned" if a.pin else ""))
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="roadgram", description="Manage a project's roadmap, plan and updates in a Telegram group.")
    ap.add_argument("--version", action="version", version=f"roadgram {__version__}")
    ap.add_argument("--dir", default=".", help="project folder (default: current; roadgram.json is searched upwards)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="create roadgram.json, .env and a sample roadmap in this folder")
    s.add_argument("--name", help="project name (default: folder name)")
    s.add_argument("--lang", choices=["en", "fa"], default="en", help="language of the messages")
    s.add_argument("--calendar", choices=["gregorian", "jalali", "both"], default="gregorian")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("agent", help="install/remove roadgram instructions for Claude Code, Codex, Cline, Cursor, Gemini CLI")
    s.add_argument("action", choices=["install"], help="install (add --uninstall to remove)")
    s.add_argument("tools", nargs="*", choices=[*agents.TOOLS, "all", "auto"],
                   help="which tools (default: auto-detect)")
    s.add_argument("--global", dest="is_global", action="store_true", help="install for your user, not just this project")
    s.add_argument("--uninstall", action="store_true")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(fn=cmd_agent)

    sub.add_parser("check", help="verify the token, the group, topics and the bot's rights").set_defaults(fn=cmd_check)
    sub.add_parser("status", help="print progress from the roadmap file (sends nothing)").set_defaults(fn=cmd_status)

    for name, helptext in (("week", "post or edit the roadmap message of a week"),
                           ("plan", "post or edit the plan message of a week")):
        s = sub.add_parser(name, help=helptext)
        s.add_argument("n", type=int, help="week number")
        s.add_argument("--dry-run", action="store_true", help="print the message, send nothing")
        s.set_defaults(fn=cmd_week_or_plan)

    sub.add_parser("sync", help="edit every posted message; post the next week when the current one is done"
                   ).set_defaults(fn=cmd_sync)

    s = sub.add_parser("post", help="send a NEW message or file to a topic (explicit announcement)")
    s.add_argument("--topic", default="updates", help="topic key from roadgram.json (default: updates)")
    s.add_argument("--text")
    s.add_argument("--file", help="text file whose content is the message")
    s.add_argument("--document", help="attach this file (text becomes the caption)")
    s.add_argument("--pin", action="store_true")
    s.add_argument("--raw-html", action="store_true", help="send the text as Telegram HTML (b, i, code, a)")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(fn=cmd_post)
    return ap


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = build_parser().parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())

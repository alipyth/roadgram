"""Command line: roadgram init | check | status | week N | plan N | sync | watch | approve N | paid N | post | hook."""
import argparse
import html
import sys
import time
from datetime import date, datetime
from pathlib import Path

from roadgram import __version__, agents
from roadgram.i18n import SAMPLE_ROADMAP
from roadgram.dates import date_text
from roadgram.inbox import Inbox
from roadgram.manager import CONFIG_NAME, STATE_DIR, Manager, State, default_config, find_root, load_config
from roadgram.roadmap import parse_roadmap, render_plan, render_week, set_meta
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
    out("Next: fill TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env, run `roadgram check`, then `roadgram watch`.")
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
    hook = bot.request("getWebhookInfo")
    if hook.get("ok") and hook["result"].get("url"):
        out("! a webhook is set on this bot: the buttons need it removed "
            "(open https://api.telegram.org/bot<TOKEN>/deleteWebhook once)")
    if cfg.get("approval", True):
        out("✓ client approval buttons are on" + ("" if cfg.get("owners") else
            '  (tip: put your Telegram id in "owners" in roadgram.json; send /whoami to the bot to see it)'))
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


WATCH_BEAT = "watch.alive"


def watcher_alive(root: Path) -> bool:
    beat = root / STATE_DIR / WATCH_BEAT
    return beat.exists() and time.time() - beat.stat().st_mtime < 90


def cmd_sync(a) -> int:
    p = project(a)
    if not p:
        return 2
    root, cfg = p
    if not load_weeks(root, cfg):
        return 2
    mgr = make_manager(root, cfg)
    if not mgr:
        return 2
    results = []
    if cfg.get("approval", True) and not watcher_alive(root):  # pick up button presses made since the last run
        log, _, _ = Inbox(mgr, root / cfg["roadmap_file"]).poll(0)
        results += log
    weeks = load_weeks(root, cfg)
    results += mgr.sync(weeks, date.today()) if weeks else []
    out("\n".join(results) if results else "Nothing to do.")
    return 1 if any("failed" in r for r in results) else 0


def stamp(msg: str):
    out(f"[{datetime.now():%H:%M:%S}] {msg}")


def sync_quiet(mgr: Manager, root: Path, cfg: dict):
    weeks = load_weeks(root, cfg)
    for line in mgr.sync(weeks, date.today()) if weeks else []:
        if not line.endswith("up to date"):
            stamp(line)


def cmd_watch(a) -> int:
    """Keep running: sync on every save of the roadmap, handle the client's buttons, send payment reminders."""
    p = project(a)
    if not p:
        return 2
    root, cfg = p
    mgr = make_manager(root, cfg)
    if not mgr or not load_weeks(root, cfg):
        return 2
    path, beat = root / cfg["roadmap_file"], root / STATE_DIR / WATCH_BEAT
    buttons = cfg.get("approval", True)
    stamp(f"watching {cfg['roadmap_file']}" + (" and the Telegram group" if buttons else "") + " (Ctrl+C to stop)")
    last, day, force, errors = None, None, True, 0
    try:
        while True:
            try:
                beat.parent.mkdir(exist_ok=True)
                beat.touch()
                mgr.state = State(root)  # pick up changes made by other roadgram commands
                mtime = path.stat().st_mtime_ns if path.exists() else None
                if force or mtime != last or day != date.today():
                    sync_quiet(mgr, root, cfg)
                    last = path.stat().st_mtime_ns if path.exists() else None
                    day, force = date.today(), False
                if buttons:
                    log, changed, ok = Inbox(mgr, path).poll(0 if a.once else a.interval)
                    for line in log:
                        stamp(line)
                    force = force or changed
                    errors = 0 if ok else errors + 1
                    if not ok and not a.once:
                        time.sleep(min(60, 5 * errors))
                elif not a.once:
                    time.sleep(a.interval)
                if a.once:
                    if force:
                        sync_quiet(mgr, root, cfg)
                    break
            except KeyboardInterrupt:
                raise
            except Exception as e:  # keep running: a network blip or a half-saved file must not stop the watcher
                stamp(f"error: {type(e).__name__}: {e}")
                if a.once:
                    return 1
                time.sleep(5)
    except KeyboardInterrupt:
        stamp("stopped")
    finally:
        beat.unlink(missing_ok=True)
    return 0


def cmd_mark(a) -> int:
    """`roadgram approve N` / `roadgram paid N` from the terminal (e.g. the client approved by phone)."""
    p = project(a)
    if not p:
        return 2
    root, cfg = p
    weeks = load_weeks(root, cfg)
    if not weeks or not week_arg(weeks, a.n):
        return 2
    path = root / cfg["roadmap_file"]
    when = date_text(date.today(), cfg["language"], cfg["calendar"])
    key = "approved" if a.cmd == "approve" else "paid"
    value = None if a.undo else (f"{a.by} · {when}" if key == "approved" and a.by else when)
    path.write_bytes(set_meta(path.read_bytes().decode("utf-8-sig"), a.n, key, value, cfg["language"]).encode("utf-8"))
    out(f"week {a.n}: {key} " + ("removed from " if a.undo else "written to ") + cfg["roadmap_file"])
    if a.no_sync:
        return 0
    mgr = make_manager(root, cfg)
    if mgr:
        weeks = load_weeks(root, cfg)
        out("\n".join(mgr.sync(weeks, date.today()) if weeks else []))
    return 0


HOOK_BEGIN, HOOK_END = "# roadgram:begin", "# roadgram:end"


def cmd_hook(a) -> int:
    """Git post-commit hook that runs `roadgram sync` in the background after every commit."""
    p = project(a)
    if not p:
        return 2
    root, _ = p
    git = next((d / ".git" for d in [root, *root.parents] if (d / ".git").is_dir()), None)
    if git is None:
        out("No git repository found (a .git folder at or above the project).")
        return 2
    hook = git / "hooks" / "post-commit"
    text = hook.read_text(encoding="utf-8") if hook.exists() else ""
    if HOOK_BEGIN in text and HOOK_END in text:
        start, end = text.index(HOOK_BEGIN), text.index(HOOK_END) + len(HOOK_END)
        text = text[:start].rstrip("\n") + "\n" + text[end:].lstrip("\n")
    if a.uninstall:
        if text.strip() in ("", "#!/bin/sh"):
            hook.unlink(missing_ok=True)
        else:
            hook.write_text(text, encoding="utf-8", newline="\n")
        out("Removed the roadgram post-commit hook.")
        return 0
    d = root.as_posix()
    block = (f"{HOOK_BEGIN}\n(roadgram --dir \"{d}\" sync >/dev/null 2>&1 || "
             f"python -m roadgram --dir \"{d}\" sync >/dev/null 2>&1) &\n{HOOK_END}\n")
    if not text.strip():
        text = "#!/bin/sh\n"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(text.rstrip("\n") + "\n" + block, encoding="utf-8", newline="\n")
    hook.chmod(0o755)
    out(f"Installed {hook}: every commit now runs `roadgram sync` in the background.")
    return 0


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

    sub.add_parser("sync", help="handle button presses, edit every posted message, advance when a week is done"
                   ).set_defaults(fn=cmd_sync)

    s = sub.add_parser("watch", help="keep running: auto-sync on every save, handle the client's buttons, send reminders")
    s.add_argument("--interval", type=int, default=3, help="seconds between checks (default: 3)")
    s.add_argument("--once", action="store_true", help="run one round and exit (for cron / Task Scheduler)")
    s.set_defaults(fn=cmd_watch)

    for name, helptext in (("approve", "mark a week as approved by the client (writes **Approved:** into the roadmap)"),
                           ("paid", "mark the milestone payment of a week as received (writes **Paid:**)")):
        s = sub.add_parser(name, help=helptext)
        s.add_argument("n", type=int, help="week number")
        if name == "approve":
            s.add_argument("--by", help="who approved (default: no name)")
        s.add_argument("--undo", action="store_true", help="remove the line again")
        s.add_argument("--no-sync", action="store_true", help="only edit the roadmap file")
        s.set_defaults(fn=cmd_mark, by=None)

    s = sub.add_parser("hook", help="install a git post-commit hook that runs `roadgram sync` after every commit")
    s.add_argument("action", choices=["install"])
    s.add_argument("--uninstall", action="store_true")
    s.set_defaults(fn=cmd_hook)

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

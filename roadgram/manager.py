"""Config, state and the sync logic: one Telegram message per (section, week), edited in place."""
import json
from datetime import date
from pathlib import Path

from roadgram.dates import date_text, digits
from roadgram.i18n import DEFAULT_TOPICS, STRINGS
from roadgram.roadmap import clean, hashtags, render_plan, render_week, week_done
from roadgram.telegram import Bot

CONFIG_NAME = "roadgram.json"
STATE_DIR = ".roadgram"
STATE_NAME = "state.json"


def default_config(project: str, language: str = "en", calendar: str = "gregorian") -> dict:
    return {
        "project": project,
        "hashtag": "".join(c for c in project if c.isalnum()) or "",
        "language": language,
        "calendar": calendar,
        "roadmap_file": "ROADMAP.md",
        "topics": dict(DEFAULT_TOPICS[language]),
        "max_item_len": 120,
        "advance": True,
        "auto_start": True,
        # client approval and milestone payments
        "approval": True,
        "require_approval": False,
        "approvers": [],
        "owners": [],
        "payment_details": "",
        "payment_reminder_days": 3,
    }


def find_root(start: Path) -> Path | None:
    """Nearest folder at or above `start` that holds roadgram.json."""
    for p in [start, *start.parents]:
        if (p / CONFIG_NAME).exists():
            return p
    return None


def load_config(root: Path) -> dict:
    cfg = json.loads((root / CONFIG_NAME).read_text(encoding="utf-8-sig"))
    base = default_config(cfg.get("project", "project"), cfg.get("language", "en"), cfg.get("calendar", "gregorian"))
    topics = {**base["topics"], **cfg.get("topics", {})}  # configs from 0.1 have no "payments" topic yet
    base.update(cfg)
    base["topics"] = topics
    if base["language"] not in ("en", "fa") or base["calendar"] not in ("gregorian", "jalali", "both"):
        raise ValueError("language must be en or fa; calendar must be gregorian, jalali or both")
    return base


class State:
    """Message ids, topic ids, invoices and the update offset, kept in <root>/.roadgram/state.json (keep it out of git)."""

    def __init__(self, root: Path):
        self.root = root
        self.path = root / STATE_DIR / STATE_NAME
        self.data = json.loads(self.path.read_text(encoding="utf-8-sig")) if self.path.exists() else {}

    def save(self):
        self.path.parent.mkdir(exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")


def week_markup(cfg: dict, week: int, data: dict) -> dict | None:
    """Inline buttons under a week: approve / request changes. None = leave the keyboard alone (approvals off)."""
    if not cfg.get("approval", True):
        return None
    if data.get("approved"):
        return {"inline_keyboard": []}
    s = STRINGS[cfg["language"]]
    return {"inline_keyboard": [[{"text": s["btn_approve"], "callback_data": f"rg:a:{week}"},
                                 {"text": s["btn_change"], "callback_data": f"rg:c:{week}"}]]}


def render_invoice(cfg: dict, week: int, data: dict, today: date) -> str:
    lang = cfg["language"]
    s, fa = STRINGS[lang], lang == "fa"
    lines = [f"<b>{s['invoice_title'].format(n=digits(week, fa), title=clean(data['title'], 200))}</b>", "",
             f"<b>{s['amount']}:</b> {clean(data['payment'], 120)}"]
    if data.get("approved"):
        lines.append(f"<b>{s['approved_by']}:</b> {clean(data['approved'], 120)}")
    if cfg.get("payment_details"):
        lines.append(f"<b>{s['pay_to']}:</b> {clean(cfg['payment_details'], 300)}")
    lines.append("")
    if data.get("paid"):
        lines.append(s["invoice_paid"].format(date=clean(data["paid"], 60) if data["paid"] != "✓"
                                              else date_text(today, lang, cfg["calendar"])))
    else:
        lines.append(s["invoice_open"])
    lines += ["", hashtags(cfg, "tag_invoice", week)]
    return "\n".join(lines)


class Manager:
    def __init__(self, cfg: dict, bot: Bot, state: State):
        self.cfg, self.bot, self.state = cfg, bot, state

    def thread(self, key: str):
        """Topic id for `key` (roadmap | plan | updates | payments | ...); created on first use. None = main chat."""
        topics = self.state.data.setdefault("topics", {})
        if key in topics:
            return topics[key]
        if self.state.data.get("forum") is None:
            info = self.bot.chat_info()
            self.state.data["forum"] = bool(info.get("ok") and info["result"].get("is_forum"))
        if not self.state.data["forum"]:
            return None
        name = self.cfg["topics"].get(key, key)
        r = self.bot.create_topic(name)
        if not r.get("ok"):
            raise RuntimeError(f"could not create the topic '{name}': {r.get('description')}")
        topics[key] = r["result"]["message_thread_id"]
        self.state.save()
        return topics[key]

    def upsert(self, section: str, topic: str, week: int, text: str, unpin_older: bool = False,
               markup: dict | None = None) -> str:
        msgs = self.state.data.setdefault(section, {})
        key = str(week)
        if key in msgs:
            r = self.bot.edit(msgs[key], text, markup)
            if r.get("ok"):
                return "edited"
            return "up to date" if "not modified" in str(r.get("description")) else f"failed: {r.get('description')}"
        try:
            thread = self.thread(topic)
        except RuntimeError as e:
            return f"failed: {e}"
        r = self.bot.send(text, thread, markup or None)
        if not r.get("ok"):
            return f"failed: {r.get('description')}"
        msgs[key] = r["result"]["message_id"]
        self.bot.pin(msgs[key])
        if unpin_older:  # only the newest plan stays pinned
            for k, mid in msgs.items():
                if k != key:
                    self.bot.unpin(mid)
        self.state.save()
        return "posted and pinned"

    def week(self, weeks: dict, n: int, today: date) -> str:
        return f"roadmap week {n}: " + self.upsert("weeks", "roadmap", n, render_week(self.cfg, n, weeks[n], today),
                                                   markup=week_markup(self.cfg, n, weeks[n]))

    def plan(self, weeks: dict, n: int, today: date) -> str:
        return f"plan week {n}: " + self.upsert("plans", "plan", n, render_plan(self.cfg, n, weeks[n], weeks.get(n - 1), today), True)

    def finished(self, data: dict) -> bool:
        """A week counts as finished when every task is ticked (and, with require_approval, the client approved it)."""
        return week_done(data) and (not self.cfg.get("require_approval") or bool(data.get("approved")))

    def sync(self, weeks: dict, today: date) -> list[str]:
        """Edit every posted message from the current roadmap; advance to the next week when the current one is done."""
        out = []
        if not self.state.data.get("weeks") and self.cfg.get("auto_start", True) and weeks:
            def pending(d):  # a ticked week still waits for the client's approval when the buttons are on
                return not self.finished(d) or (self.cfg.get("approval", True) and not d.get("approved"))
            first = next((n for n in sorted(weeks) if pending(weeks[n])), min(weeks))
            out.append(self.week(weeks, first, today))
            if first + 1 in weeks and not self.state.data.get("plans", {}).get(str(first + 1)):
                out.append(self.plan(weeks, first + 1, today))
            out += self.payments(weeks, today)
            return out
        for key in sorted(self.state.data.get("weeks", {}), key=int):
            if int(key) in weeks:
                out.append(self.week(weeks, int(key), today))
        for key in sorted(self.state.data.get("plans", {}), key=int):
            if int(key) in weeks:
                out.append(self.plan(weeks, int(key), today))
        posted = [int(k) for k in self.state.data.get("weeks", {})]
        cur = max(posted) if posted else None
        if self.cfg.get("advance", True) and cur in weeks and self.finished(weeks[cur]) and cur + 1 in weeks:
            out.append(self.week(weeks, cur + 1, today))
            if cur + 2 in weeks:
                out.append(self.plan(weeks, cur + 2, today))
        out += self.payments(weeks, today)
        return out

    # ---- milestone payments -------------------------------------------------------------------------------------

    def payments(self, weeks: dict, today: date) -> list[str]:
        """Send an invoice when a week with a **Payment:** line is approved; keep it in step; remind while unpaid."""
        out = []
        invoices = self.state.data.setdefault("invoices", {})
        for n, data in sorted(weeks.items()):
            if not data.get("payment") or not data.get("approved"):
                continue
            key, inv = str(n), invoices.get(str(n))
            text = render_invoice(self.cfg, n, data, today)
            markup = None
            if self.cfg.get("owners"):
                markup = {"inline_keyboard": [] if data.get("paid") else
                          [[{"text": STRINGS[self.cfg["language"]]["btn_paid"], "callback_data": f"rg:p:{n}"}]]}
            if inv is None:
                try:
                    thread = self.thread("payments")
                except RuntimeError as e:
                    out.append(f"invoice week {n}: failed: {e}")
                    continue
                r = self.bot.send(text, thread, markup)
                if not r.get("ok"):
                    out.append(f"invoice week {n}: failed: {r.get('description')}")
                    continue
                invoices[key] = {"message_id": r["result"]["message_id"], "thread": thread, "sent": today.isoformat(),
                                 "last": today.isoformat(), "reminders": 0, "paid": bool(data.get("paid"))}
                self.state.save()
                out.append(f"invoice week {n}: sent")
                continue
            if bool(data.get("paid")) != inv.get("paid"):
                r = self.bot.edit(inv["message_id"], text, markup)
                inv["paid"] = bool(data.get("paid"))
                self.state.save()
                out.append(f"invoice week {n}: " + ("marked paid" if inv["paid"] else "reopened")
                           + ("" if r.get("ok") else f" (edit failed: {r.get('description')})"))
                continue
            days = int(self.cfg.get("payment_reminder_days") or 0)
            if not inv.get("paid") and days > 0 and (today - date.fromisoformat(inv["last"])).days >= days:
                s, fa = STRINGS[self.cfg["language"]], self.cfg["language"] == "fa"
                r = self.bot.send(s["reminder"].format(n=digits(n, fa), amount=clean(data["payment"], 80)),
                                  inv.get("thread"), reply_to=inv["message_id"])
                if r.get("ok"):
                    inv["last"], inv["reminders"] = today.isoformat(), inv.get("reminders", 0) + 1
                    self.state.save()
                    out.append(f"invoice week {n}: reminder {inv['reminders']} sent")
        return out

    def notify_owners(self, text: str):
        """Private message to every numeric id in `owners` (each owner must have pressed Start in the bot once)."""
        for owner in self.cfg.get("owners", []):
            if str(owner).lstrip("-").isdigit():
                self.bot.send(text, chat=int(owner))

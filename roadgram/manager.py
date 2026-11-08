"""Config, state and the sync logic: one Telegram message per (section, week), edited in place."""
import json
from datetime import date
from pathlib import Path

from roadgram.i18n import DEFAULT_TOPICS
from roadgram.roadmap import render_plan, render_week, week_done
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
        "topics": DEFAULT_TOPICS[language],
        "max_item_len": 120,
        "advance": True,
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
    base.update(cfg)
    if base["language"] not in ("en", "fa") or base["calendar"] not in ("gregorian", "jalali", "both"):
        raise ValueError("language must be en or fa; calendar must be gregorian, jalali or both")
    return base


class State:
    """Message ids and topic ids, kept in <root>/.roadgram/state.json (keep it out of git)."""

    def __init__(self, root: Path):
        self.path = root / STATE_DIR / STATE_NAME
        self.data = json.loads(self.path.read_text(encoding="utf-8-sig")) if self.path.exists() else {}

    def save(self):
        self.path.parent.mkdir(exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")


class Manager:
    def __init__(self, cfg: dict, bot: Bot, state: State):
        self.cfg, self.bot, self.state = cfg, bot, state

    def thread(self, key: str):
        """Topic id for `key` (roadmap | plan | updates | ...); created on first use. None = post in the main chat."""
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

    def upsert(self, section: str, topic: str, week: int, text: str, unpin_older: bool = False) -> str:
        msgs = self.state.data.setdefault(section, {})
        key = str(week)
        if key in msgs:
            r = self.bot.edit(msgs[key], text)
            if r.get("ok"):
                return "edited"
            return "up to date" if "not modified" in str(r.get("description")) else f"failed: {r.get('description')}"
        try:
            thread = self.thread(topic)
        except RuntimeError as e:
            return f"failed: {e}"
        r = self.bot.send(text, thread)
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
        return f"roadmap week {n}: " + self.upsert("weeks", "roadmap", n, render_week(self.cfg, n, weeks[n], today))

    def plan(self, weeks: dict, n: int, today: date) -> str:
        return f"plan week {n}: " + self.upsert("plans", "plan", n, render_plan(self.cfg, n, weeks[n], weeks.get(n - 1), today), True)

    def sync(self, weeks: dict, today: date) -> list[str]:
        """Edit every posted message from the current roadmap; advance to the next week when the current one is done."""
        out = []
        for key in sorted(self.state.data.get("weeks", {}), key=int):
            if int(key) in weeks:
                out.append(self.week(weeks, int(key), today))
        for key in sorted(self.state.data.get("plans", {}), key=int):
            if int(key) in weeks:
                out.append(self.plan(weeks, int(key), today))
        posted = [int(k) for k in self.state.data.get("weeks", {})]
        cur = max(posted) if posted else None
        if self.cfg.get("advance", True) and cur in weeks and week_done(weeks[cur]) and cur + 1 in weeks:
            out.append(self.week(weeks, cur + 1, today))
            if cur + 2 in weeks:
                out.append(self.plan(weeks, cur + 2, today))
        return out

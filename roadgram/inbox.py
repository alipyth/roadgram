"""Incoming Telegram updates: the client's approval buttons, change-request replies and the owner's "paid" button.

Everything that matters ends up in ROADMAP.md (the single source of truth):
  ✅ Approve delivery  ->  `- **Approved:** @client · date` under the week
  ✏️ Request changes   ->  the client's reply becomes a new open task `- [ ] ✏️ ...` in that week
  💰 Mark as paid      ->  `- **Paid:** date` under the week
The caller runs a sync afterwards, so the Telegram messages, invoices and owners' DMs follow automatically.
"""
import html
from datetime import date
from pathlib import Path

from roadgram.dates import date_text, digits
from roadgram.i18n import STRINGS
from roadgram.manager import Manager
from roadgram.roadmap import add_task, parse_roadmap, set_meta


def user_label(user: dict) -> str:
    if user.get("username"):
        return "@" + user["username"]
    return " ".join(x for x in (user.get("first_name"), user.get("last_name")) if x) or str(user.get("id"))


def mention(user: dict) -> str:
    return f'<a href="tg://user?id={user["id"]}">{html.escape(user_label(user), quote=False)}</a>'


def listed(entries, user: dict) -> bool:
    """True when the user's id or @username is in `entries` (ids may be numbers or strings)."""
    names = {str(user.get("id")), (user.get("username") or "").lower()}
    return any(str(e).lstrip("@").lower() in names for e in entries or [])


def is_owner(cfg: dict, user: dict) -> bool:
    return listed(cfg.get("owners"), user)


def is_client(cfg: dict, user: dict) -> bool:
    """With `approvers` set only they count; otherwise anyone in the group who is not an owner and not a bot."""
    if user.get("is_bot"):
        return False
    if cfg.get("approvers"):
        return listed(cfg["approvers"], user)
    return not is_owner(cfg, user)


def one_line(text: str, limit: int = 300) -> str:
    s = " ".join(text.split())
    return s if len(s) <= limit else s[: limit - 1] + "…"


class Inbox:
    def __init__(self, mgr: Manager, roadmap: Path, today=date.today):
        self.mgr, self.path, self.today = mgr, roadmap, today

    @property
    def cfg(self) -> dict:
        return self.mgr.cfg

    @property
    def s(self) -> dict:
        return STRINGS[self.cfg["language"]]

    def fa(self, n) -> str:
        return digits(n, self.cfg["language"] == "fa")

    def read(self) -> str:
        return self.path.read_bytes().decode("utf-8-sig")

    def write(self, text: str):
        self.path.write_bytes(text.encode("utf-8"))

    def stamp(self, user: dict | None = None) -> str:
        d = date_text(self.today(), self.cfg["language"], self.cfg["calendar"])
        return f"{user_label(user)} · {d}" if user else d

    def same_chat(self, chat: dict) -> bool:
        want = str(self.mgr.bot.chat)
        return str(chat.get("id")) == want or ("@" + str(chat.get("username") or "")).lower() == want.lower()

    # ---- polling ------------------------------------------------------------------------------------------------

    def poll(self, timeout: int = 0) -> tuple[list[str], bool, bool]:
        """Fetch and handle pending updates. Returns (log lines, roadmap changed, request ok)."""
        state = self.mgr.state.data
        r = self.mgr.bot.updates(state.get("update_offset"), timeout)
        if not r.get("ok"):
            return [f"updates failed: {r.get('description')}"], False, False
        log, changed = [], False
        for upd in r.get("result", []):
            state["update_offset"] = upd["update_id"] + 1
            try:
                if "callback_query" in upd:
                    line, ch = self.on_button(upd["callback_query"])
                elif "message" in upd:
                    line, ch = self.on_message(upd["message"])
                else:
                    line, ch = "", False
            except Exception as e:  # one bad update must not stop the bot
                line, ch = f"update {upd.get('update_id')} skipped ({type(e).__name__}: {e})", False
            if line:
                log.append(line)
            changed = changed or ch
            self.mgr.state.save()
        return log, changed, True

    # ---- buttons ------------------------------------------------------------------------------------------------

    def on_button(self, cq: dict) -> tuple[str, bool]:
        parts = (cq.get("data") or "").split(":")
        if len(parts) != 3 or parts[0] != "rg" or not parts[2].isdigit():
            return "", False
        action, n, user, msg = parts[1], int(parts[2]), cq.get("from", {}), cq.get("message") or {}
        bot, s = self.mgr.bot, self.s
        if not self.same_chat(msg.get("chat", {})):
            bot.answer(cq["id"])
            return "", False
        if action in ("a", "c") and not is_client(self.cfg, user):
            bot.answer(cq["id"], s["only_client"], alert=True)
            return f"week {n}: button ignored, {user_label(user)} is not the client", False
        if action == "p" and not is_owner(self.cfg, user):
            bot.answer(cq["id"], s["only_owner"], alert=True)
            return f"week {n}: paid button ignored, {user_label(user)} is not an owner", False
        text = self.read()
        weeks = parse_roadmap(text)
        if n not in weeks:
            bot.answer(cq["id"], s["unknown_week"], alert=True)
            return "", False
        if action == "a":
            if weeks[n]["approved"]:
                bot.answer(cq["id"], s["already_approved"])
                return "", False
            self.write(set_meta(text, n, "approved", self.stamp(user), self.cfg["language"]))
            bot.answer(cq["id"], s["approved_ok"].format(n=self.fa(n)), alert=True)
            self.mgr.notify_owners(s["dm_approved"].format(user=html.escape(user_label(user)), n=self.fa(n),
                                                           title=html.escape(weeks[n]["title"])))
            return f"week {n}: delivery approved by {user_label(user)}", True
        if action == "c":
            prompt = s["change_prompt"].format(user=mention(user), n=self.fa(n))
            r = bot.send(prompt, msg.get("message_thread_id"), {"force_reply": True, "selective": True},
                         reply_to=msg.get("message_id"))
            if r.get("ok"):
                self.mgr.state.data.setdefault("prompts", {})[str(r["result"]["message_id"])] = \
                    {"week": n, "user": user.get("id")}
            bot.answer(cq["id"], s["change_hint"])
            return f"week {n}: {user_label(user)} is writing a change request", False
        if action == "p":
            if not weeks[n]["paid"]:
                self.write(set_meta(text, n, "paid", self.stamp(), self.cfg["language"]))
            bot.answer(cq["id"], s["dm_paid"].format(n=self.fa(n)))
            return f"week {n}: payment marked as received by {user_label(user)}", True
        return "", False

    # ---- messages -----------------------------------------------------------------------------------------------

    def on_message(self, msg: dict) -> tuple[str, bool]:
        text, user, chat = msg.get("text") or "", msg.get("from", {}), msg.get("chat", {})
        bot, s = self.mgr.bot, self.s
        if text.split("@")[0].strip() in ("/whoami", "/id", "/start"):
            bot.send(s["whoami"].format(id=user.get("id"), chat=chat.get("id")), msg.get("message_thread_id"),
                     reply_to=msg.get("message_id"), chat=chat.get("id"))
            return f"whoami: {user_label(user)}", False
        reply = msg.get("reply_to_message") or {}
        prompts = self.mgr.state.data.get("prompts", {})
        p = prompts.get(str(reply.get("message_id")))
        if not p or not text.strip() or not self.same_chat(chat) or user.get("id") != p["user"]:
            return "", False
        n = p["week"]
        roadmap = self.read()
        if n not in parse_roadmap(roadmap):
            return "", False
        task = f"✏️ {one_line(text)} ({user_label(user)}, {self.stamp()})"
        roadmap = add_task(roadmap, n, task)
        roadmap = set_meta(roadmap, n, "approved", None, self.cfg["language"])  # new work: approval starts again
        self.write(roadmap)
        del prompts[str(reply["message_id"])]
        bot.send(s["change_saved"].format(n=self.fa(n)), msg.get("message_thread_id"), reply_to=msg.get("message_id"))
        self.mgr.notify_owners(s["dm_change"].format(user=html.escape(user_label(user)), n=self.fa(n),
                                                     text=html.escape(one_line(text))))
        return f"week {n}: change request from {user_label(user)} added to the roadmap", True

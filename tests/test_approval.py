"""Client approval buttons, change requests, milestone payments, watch and the git hook (no network)."""
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from unittest import mock

from roadgram import cli
from roadgram.inbox import Inbox, is_client
from roadgram.manager import Manager, State, default_config, load_config
from roadgram.roadmap import add_task, parse_roadmap, render_week, set_meta
from roadgram.telegram import Bot

TODAY = date(2026, 11, 8)
ROADMAP = """# Roadmap

## Week 1: Foundation
- [x] Set up the repo
- [x] Core feature
- **Output:** working core
- **Payment:** 500 USD

## Week 2: Launch
- [ ] Release
<!--
- **Payment:** 900 USD
-->

## Notes
free text
"""
CLIENT = {"id": 42, "username": "client", "first_name": "Sara"}
OWNER = {"id": 7, "username": "dev", "first_name": "Ali"}
CHAT = {"id": -100, "type": "supergroup"}


class FakeTelegram:
    def __init__(self):
        self.calls, self.next_id, self.queue = [], 500, []

    def __call__(self, token, method, payload, files=None):
        self.calls.append((method, payload))
        self.next_id += 1
        if method == "getChat":
            return {"ok": True, "result": {"is_forum": True}}
        if method == "createForumTopic":
            return {"ok": True, "result": {"message_thread_id": self.next_id}}
        if method == "sendMessage":
            return {"ok": True, "result": {"message_id": self.next_id}}
        if method == "getUpdates":
            q, self.queue = self.queue, []
            return {"ok": True, "result": q}
        return {"ok": True, "result": True}

    def sent(self, method):
        return [p for m, p in self.calls if m == method]


def setup(tmp, **cfg_over):
    root = Path(tmp)
    (root / "ROADMAP.md").write_text(ROADMAP, encoding="utf-8")
    cfg = {**default_config("Demo"), "owners": [7], **cfg_over}
    fake = FakeTelegram()
    mgr = Manager(cfg, Bot("T", "-100", fake), State(root))
    return root, mgr, fake, Inbox(mgr, root / "ROADMAP.md", today=lambda: TODAY)


def button(uid, user, data, mid=1000):
    return {"update_id": uid, "callback_query": {"id": f"cb{uid}", "from": user, "data": data,
                                                 "message": {"message_id": mid, "chat": CHAT}}}


class RoadmapEdits(unittest.TestCase):
    def test_meta_lines_and_comments(self):
        w = parse_roadmap(ROADMAP)
        self.assertEqual(w[1]["payment"], "500 USD")
        self.assertEqual(w[2]["payment"], "")  # inside <!-- --> is ignored
        self.assertEqual(w[1]["approved"], "")

    def test_set_meta_insert_replace_remove_keeps_other_weeks(self):
        t = set_meta(ROADMAP, 1, "approved", "@client · today", "en")
        self.assertEqual(parse_roadmap(t)[1]["approved"], "@client · today")
        t = set_meta(t, 1, "approved", "@x · later", "en")
        self.assertEqual(t.count("**Approved:**"), 1)
        t = set_meta(t, 1, "approved", None, "en")
        self.assertEqual(t, ROADMAP)

    def test_persian_labels_and_crlf(self):
        t = set_meta(ROADMAP.replace("\n", "\r\n"), 2, "approved", "@c", "fa")
        self.assertIn("- **تأیید تحویل:** @c\r\n", t)
        self.assertEqual(parse_roadmap(t)[2]["approved"], "@c")

    def test_add_task_goes_after_the_last_task(self):
        t = add_task(ROADMAP, 1, "✏️ bigger logo")
        w = parse_roadmap(t)
        self.assertEqual(w[1]["items"][-1], (False, "✏️ bigger logo"))
        self.assertLess(t.index("bigger logo"), t.index("**Output:**"))

    def test_render_status_lines(self):
        cfg = default_config("Demo")
        w = parse_roadmap(ROADMAP)
        self.assertIn("waiting for the client", render_week(cfg, 1, w[1], TODAY))
        w = parse_roadmap(set_meta(ROADMAP, 1, "approved", "@client", "en"))
        text = render_week(cfg, 1, w[1], TODAY)
        self.assertIn("Delivery approved", text)
        self.assertIn("500 USD · ⏳ open", text)


class Buttons(unittest.TestCase):
    def test_week_message_has_buttons_until_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, mgr, fake, _ = setup(tmp)
            mgr.week(parse_roadmap(ROADMAP), 1, TODAY)
            kb = fake.sent("sendMessage")[0]["reply_markup"]["inline_keyboard"][0]
            self.assertEqual([b["callback_data"] for b in kb], ["rg:a:1", "rg:c:1"])

    def test_approve_writes_roadmap_invoices_and_notifies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, mgr, fake, inbox = setup(tmp, payment_details="IBAN 123")
            mgr.week(parse_roadmap(ROADMAP), 1, TODAY)
            fake.calls.clear()
            fake.queue = [button(1, CLIENT, "rg:a:1")]
            log, changed, ok = inbox.poll()
            self.assertTrue(ok and changed)
            self.assertIn("approved by @client", log[0])
            text = (root / "ROADMAP.md").read_text(encoding="utf-8")
            self.assertIn("- **Approved:** @client · 8 November 2026", text)
            self.assertEqual(fake.sent("sendMessage")[0]["chat_id"], 7)  # DM to the owner
            self.assertEqual(mgr.state.data["update_offset"], 2)
            fake.calls.clear()
            res = mgr.sync(parse_roadmap(text), TODAY)
            self.assertIn("invoice week 1: sent", res)
            inv = fake.sent("sendMessage")[-1]
            self.assertIn("500 USD", inv["text"])
            self.assertIn("IBAN 123", inv["text"])
            self.assertEqual(inv["reply_markup"]["inline_keyboard"][0][0]["callback_data"], "rg:p:1")
            week_msg = fake.sent("editMessageText")[0]
            self.assertEqual(week_msg["reply_markup"], {"inline_keyboard": []})  # buttons removed
            # the invoice is not sent twice
            self.assertNotIn("invoice week 1: sent", mgr.sync(parse_roadmap(text), TODAY))

    def test_only_the_client_can_approve_only_owner_marks_paid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, mgr, fake, inbox = setup(tmp)
            fake.queue = [button(1, OWNER, "rg:a:1"), button(2, CLIENT, "rg:p:1")]
            _, changed, _ = inbox.poll()
            self.assertFalse(changed)
            alerts = fake.sent("answerCallbackQuery")
            self.assertTrue(all(a["show_alert"] for a in alerts))
            self.assertNotIn("Approved", (root / "ROADMAP.md").read_text(encoding="utf-8"))
        cfg = {**default_config("D"), "approvers": ["@Client"]}
        self.assertTrue(is_client(cfg, CLIENT))
        self.assertFalse(is_client(cfg, {"id": 9, "username": "other"}))
        self.assertFalse(is_client(default_config("D"), {"id": 1, "is_bot": True}))

    def test_buttons_from_another_chat_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, mgr, fake, inbox = setup(tmp)
            upd = button(1, CLIENT, "rg:a:1")
            upd["callback_query"]["message"]["chat"] = {"id": -999}
            fake.queue = [upd]
            self.assertFalse(inbox.poll()[1])

    def test_change_request_becomes_a_task_and_resets_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, mgr, fake, inbox = setup(tmp)
            (root / "ROADMAP.md").write_text(set_meta(ROADMAP, 1, "approved", "@client", "en"), encoding="utf-8")
            fake.queue = [button(1, CLIENT, "rg:c:1")]
            inbox.poll()
            prompt = fake.sent("sendMessage")[-1]
            self.assertTrue(prompt["reply_markup"]["force_reply"])
            self.assertIn("tg://user?id=42", prompt["text"])
            pid = next(iter(mgr.state.data["prompts"]))
            stranger = {"update_id": 2, "message": {"message_id": 1, "from": OWNER, "chat": CHAT, "text": "no",
                                                    "reply_to_message": {"message_id": int(pid)}}}
            reply = {"update_id": 3, "message": {"message_id": 2, "from": CLIENT, "chat": CHAT,
                                                 "text": "Make the\nlogo bigger",
                                                 "reply_to_message": {"message_id": int(pid)}}}
            fake.queue = [stranger, reply]
            log, changed, _ = inbox.poll()
            self.assertTrue(changed)
            w = parse_roadmap((root / "ROADMAP.md").read_text(encoding="utf-8"))
            self.assertEqual(w[1]["items"][-1][1], "✏️ Make the logo bigger (@client, 8 November 2026)")
            self.assertEqual(w[1]["approved"], "")
            self.assertEqual(mgr.state.data["prompts"], {})

    def test_paid_button_and_reminders(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, mgr, fake, inbox = setup(tmp, payment_reminder_days=3)
            path = root / "ROADMAP.md"
            path.write_text(set_meta(ROADMAP, 1, "approved", "@client", "en"), encoding="utf-8")
            mgr.sync(parse_roadmap(path.read_text(encoding="utf-8")), TODAY)
            fake.calls.clear()
            later = date(2026, 11, 11)
            self.assertIn("invoice week 1: reminder 1 sent", mgr.sync(parse_roadmap(path.read_text("utf-8")), later))
            self.assertIn("reply_parameters", fake.sent("sendMessage")[-1])
            self.assertNotIn("invoice week 1: reminder 2 sent", mgr.sync(parse_roadmap(path.read_text("utf-8")), later))
            fake.queue = [button(1, OWNER, "rg:p:1")]
            self.assertTrue(inbox.poll()[1])
            self.assertIn("- **Paid:** 8 November 2026", path.read_text(encoding="utf-8"))
            self.assertIn("invoice week 1: marked paid", mgr.sync(parse_roadmap(path.read_text("utf-8")), later))
            self.assertNotIn("reminder", " ".join(mgr.sync(parse_roadmap(path.read_text("utf-8")), date(2027, 1, 1))))

    def test_require_approval_blocks_advance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, mgr, fake, inbox = setup(tmp, require_approval=True)
            w = parse_roadmap(ROADMAP)
            mgr.week(w, 1, TODAY)
            self.assertEqual(mgr.sync(w, TODAY), ["roadmap week 1: edited"])
            w = parse_roadmap(set_meta(ROADMAP, 1, "approved", "@c", "en"))
            self.assertIn("roadmap week 2: posted and pinned", mgr.sync(w, TODAY))

    def test_auto_start_posts_the_first_open_week(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, mgr, fake, inbox = setup(tmp)
            res = mgr.sync(parse_roadmap(ROADMAP.replace("- [x] Core", "- [ ] Core")), TODAY)
            self.assertEqual(res, ["roadmap week 1: posted and pinned", "plan week 2: posted and pinned"])

    def test_whoami(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, mgr, fake, inbox = setup(tmp)
            fake.queue = [{"update_id": 1, "message": {"message_id": 3, "from": CLIENT,
                                                        "chat": {"id": 42, "type": "private"}, "text": "/whoami"}}]
            inbox.poll()
            msg = fake.sent("sendMessage")[-1]
            self.assertEqual(msg["chat_id"], 42)
            self.assertIn("<code>42</code>", msg["text"])

    def test_a_broken_update_does_not_stop_the_rest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, mgr, fake, inbox = setup(tmp)
            fake.queue = [{"update_id": 1, "callback_query": {"data": "rg:a:1"}}, button(2, CLIENT, "rg:a:1")]
            log, changed, _ = inbox.poll()
            self.assertTrue(changed)
            self.assertIn("skipped", log[0])


class CliNew(unittest.TestCase):
    def run_cli(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cli.main(list(args))
        return code, buf.getvalue()

    def test_old_config_gets_the_payments_topic(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "roadgram.json").write_text('{"project": "x", "topics": {"roadmap": "R"}}', encoding="utf-8")
            cfg = load_config(Path(tmp))
            self.assertEqual(cfg["topics"]["roadmap"], "R")
            self.assertIn("payments", cfg["topics"])

    def test_approve_and_paid_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.run_cli("--dir", tmp, "init")
            code, text = self.run_cli("--dir", tmp, "approve", "1", "--by", "Sara", "--no-sync")
            self.assertEqual(code, 0)
            road = Path(tmp, "ROADMAP.md").read_text(encoding="utf-8")
            self.assertIn("- **Approved:** Sara · ", road)
            self.run_cli("--dir", tmp, "approve", "1", "--undo", "--no-sync")
            self.assertNotIn("Approved", Path(tmp, "ROADMAP.md").read_text(encoding="utf-8"))
            code, _ = self.run_cli("--dir", tmp, "paid", "9", "--no-sync")
            self.assertEqual(code, 2)

    def test_watch_once_syncs_and_reads_buttons(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.run_cli("--dir", tmp, "init")
            Path(tmp, "ROADMAP.md").write_text(ROADMAP, encoding="utf-8")
            fake = FakeTelegram()
            fake.queue = [button(1, CLIENT, "rg:a:1")]
            env = {"TELEGRAM_BOT_TOKEN": "T", "TELEGRAM_CHAT_ID": "-100"}
            with mock.patch.dict("os.environ", env), mock.patch("roadgram.telegram.api", fake), \
                    mock.patch.object(Bot.__init__, "__defaults__", (fake,)):
                code, text = self.run_cli("--dir", tmp, "watch", "--once")
            self.assertEqual(code, 0)
            self.assertIn("roadmap week 1: posted and pinned", text)
            self.assertIn("delivery approved by @client", text)
            self.assertIn("invoice week 1: sent", text)
            self.assertFalse(Path(tmp, ".roadgram", "watch.alive").exists())

    def test_hook_install_is_idempotent_and_uninstalls(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.run_cli("--dir", tmp, "init")
            hooks = Path(tmp, ".git", "hooks")
            hooks.mkdir(parents=True)
            (hooks / "post-commit").write_text("#!/bin/sh\necho mine\n", encoding="utf-8")
            self.run_cli("--dir", tmp, "hook", "install")
            self.run_cli("--dir", tmp, "hook", "install")
            text = (hooks / "post-commit").read_text(encoding="utf-8")
            self.assertEqual(text.count("# roadgram:begin"), 1)
            self.assertIn("echo mine", text)
            self.run_cli("--dir", tmp, "hook", "install", "--uninstall")
            self.assertEqual((hooks / "post-commit").read_text(encoding="utf-8"), "#!/bin/sh\necho mine\n")


if __name__ == "__main__":
    unittest.main()

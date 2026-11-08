import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from unittest import mock

from roadgram import cli
from roadgram.dates import date_text, gregorian_to_jalali
from roadgram.manager import Manager, State, default_config, find_root
from roadgram.roadmap import parse_roadmap, render_plan, render_week
from roadgram.telegram import Bot, api

EN = """# Roadmap

## Week 1: Foundation <core>
- [x] Set up the repo
- [x] Write `core` & tests
- **Output:** working core

## Week 2: Launch
- **Checkpoint 1: Friday**
- [ ] Add feature B
- [ ] Release notes
- **Output:** first release

## Week 3: Later
- [ ] Something
"""
FA = "## هفته ۱: پایه\n- [x] کار اول\n- [ ] کار دوم\n- **خروجی:** نسخه‌ی اول\n"
TODAY = date(2026, 11, 7)


class FakeTelegram:
    """Records calls; behaves like a forum group where every call succeeds."""

    def __init__(self, forum=True):
        self.calls, self.forum, self.next_id = [], forum, 100

    def __call__(self, token, method, payload, files=None):
        self.calls.append((method, payload))
        self.next_id += 1
        if method == "getChat":
            return {"ok": True, "result": {"is_forum": self.forum, "title": "G", "type": "supergroup"}}
        if method == "createForumTopic":
            return {"ok": True, "result": {"message_thread_id": self.next_id}}
        if method == "sendMessage":
            return {"ok": True, "result": {"message_id": self.next_id}}
        return {"ok": True, "result": True}

    def methods(self):
        return [m for m, _ in self.calls]


def make(tmp, forum=True, **cfg_over):
    root = Path(tmp)
    cfg = {**default_config("Demo App"), **cfg_over}
    fake = FakeTelegram(forum)
    return Manager(cfg, Bot("TOKEN-SECRET", "-100", fake), State(root)), fake


class Dates(unittest.TestCase):
    def test_known_jalali_date(self):
        self.assertEqual(gregorian_to_jalali(2026, 11, 7), (1405, 8, 16))

    def test_texts(self):
        self.assertEqual(date_text(TODAY, "en", "gregorian"), "7 November 2026")
        self.assertEqual(date_text(TODAY, "fa", "jalali"), "۱۶ آبان ۱۴۰۵")
        self.assertIn("(۷ نوامبر ۲۰۲۶)", date_text(TODAY, "fa", "both"))


class Parse(unittest.TestCase):
    def test_english_and_persian(self):
        w = parse_roadmap(EN)
        self.assertEqual(sorted(w), [1, 2, 3])
        self.assertEqual(w[1]["items"], [(True, "Set up the repo"), (True, "Write `core` & tests")])
        self.assertEqual(w[2]["output"], "first release")
        self.assertTrue(w[2]["checkpoint"].startswith("Checkpoint 1"))
        f = parse_roadmap(FA)
        self.assertEqual(f[1]["output"], "نسخه‌ی اول")
        self.assertEqual(len(f[1]["items"]), 2)

    def test_other_headings_end_a_week(self):
        w = parse_roadmap("## Week 1: A\n- [ ] x\n## Notes\n- [ ] not a task\n")
        self.assertEqual(len(w[1]["items"]), 1)


class Render(unittest.TestCase):
    def test_html_is_escaped_and_marks_done(self):
        cfg = default_config("Demo App")
        text = render_week(cfg, 1, parse_roadmap(EN)[1], TODAY)
        self.assertIn("&lt;core&gt;", text)
        self.assertIn("Write core &amp; tests", text)
        self.assertIn("✅ Set up the repo", text)
        self.assertIn("2 of 2 tasks (100%)", text)
        self.assertIn("#roadmap #week1 #DemoApp", text)

    def test_persian_digits(self):
        cfg = default_config("Demo", "fa", "jalali")
        text = render_week(cfg, 1, parse_roadmap(FA)[1], TODAY)
        self.assertIn("هفته ۱", text)
        self.assertIn("۱ از ۲ کار (۵۰٪)", text)
        self.assertIn("۱۶ آبان ۱۴۰۵", text)

    def test_plan_lists_carried_over(self):
        cfg = default_config("Demo")
        w = parse_roadmap(EN)
        self.assertIn("Last week is complete", render_plan(cfg, 2, w[2], w[1], TODAY))
        self.assertIn("Carried over from last week: 2", render_plan(cfg, 3, w[3], w[2], TODAY))

    def test_long_roadmap_fits_telegram_limit(self):
        items = "\n".join(f"- [ ] task number {i} " + "x" * 100 for i in range(200))
        w = parse_roadmap("## Week 1: Big\n" + items + "\n- **Output:** done\n")
        text = render_week(default_config("Demo"), 1, w[1], TODAY)
        self.assertLessEqual(len(text), 4096)
        self.assertIn("and", text)
        self.assertIn("#roadmap", text)


class Sync(unittest.TestCase):
    def test_post_pin_then_edit(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr, fake = make(tmp)
            w = parse_roadmap(EN)
            self.assertEqual(mgr.week(w, 1, TODAY), "roadmap week 1: posted and pinned")
            self.assertEqual(fake.methods(), ["getChat", "createForumTopic", "sendMessage", "pinChatMessage"])
            fake.calls.clear()
            self.assertEqual(mgr.week(w, 1, TODAY), "roadmap week 1: edited")
            self.assertEqual(fake.methods(), ["editMessageText"])
            # state survives a restart
            mgr2 = Manager(mgr.cfg, mgr.bot, State(Path(tmp)))
            fake.calls.clear()
            mgr2.week(w, 1, TODAY)
            self.assertEqual(fake.methods(), ["editMessageText"])

    def test_advances_when_the_week_is_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr, fake = make(tmp)
            w = parse_roadmap(EN)
            mgr.week(w, 1, TODAY)
            fake.calls.clear()
            res = mgr.sync(w, TODAY)
            self.assertEqual(res, ["roadmap week 1: edited", "roadmap week 2: posted and pinned",
                                   "plan week 3: posted and pinned"])

    def test_no_advance_when_a_task_is_open_or_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr, _ = make(tmp)
            w = parse_roadmap(EN)
            mgr.week(w, 2, TODAY)
            self.assertEqual(mgr.sync(w, TODAY), ["roadmap week 2: edited"])
        with tempfile.TemporaryDirectory() as tmp:
            mgr, _ = make(tmp, advance=False)
            w = parse_roadmap(EN)
            mgr.week(w, 1, TODAY)
            self.assertEqual(mgr.sync(w, TODAY), ["roadmap week 1: edited"])

    def test_newest_plan_stays_pinned(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr, fake = make(tmp)
            w = parse_roadmap(EN)
            mgr.plan(w, 2, TODAY)
            fake.calls.clear()
            mgr.plan(w, 3, TODAY)
            self.assertIn("unpinChatMessage", fake.methods())

    def test_group_without_topics_posts_in_main_chat(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr, fake = make(tmp, forum=False)
            mgr.week(parse_roadmap(EN), 1, TODAY)
            self.assertNotIn("createForumTopic", fake.methods())
            send = next(p for m, p in fake.calls if m == "sendMessage")
            self.assertNotIn("message_thread_id", send)

    def test_topic_failure_is_reported_not_raised(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr, fake = make(tmp)
            real = fake.__call__
            fake_fail = lambda t, m, p, files=None: ({"ok": False, "description": "not enough rights"}  # noqa: E731
                                                     if m == "createForumTopic" else real(t, m, p, files))
            mgr.bot._call = fake_fail
            self.assertIn("failed: could not create the topic", mgr.week(parse_roadmap(EN), 1, TODAY))


class Network(unittest.TestCase):
    def test_token_never_appears_in_a_network_error(self):
        with mock.patch("urllib.request.urlopen", side_effect=OSError("boom https://api.telegram.org/botTOKEN-SECRET/x")):
            r = api("TOKEN-SECRET", "getMe", {})
        self.assertFalse(r["ok"])
        self.assertNotIn("TOKEN-SECRET", json.dumps(r))


class Cli(unittest.TestCase):
    def run_cli(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cli.main(list(args))
        return code, buf.getvalue()

    def test_init_then_dry_run_and_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _ = self.run_cli("--dir", tmp, "init", "--name", "Demo", "--lang", "fa", "--calendar", "jalali")
            self.assertEqual(code, 0)
            root = Path(tmp)
            self.assertTrue((root / "roadgram.json").exists() and (root / ".env").exists())
            gi = (root / ".gitignore").read_text()
            self.assertIn(".env", gi)
            self.assertIn(".roadgram/", gi)
            code, text = self.run_cli("--dir", tmp, "week", "1", "--dry-run")
            self.assertEqual(code, 0)
            self.assertIn("هفته ۱", text)
            code, text = self.run_cli("--dir", tmp, "status")
            self.assertEqual(code, 0)
            self.assertIn("week 1: 0/3", text)
            code, _ = self.run_cli("--dir", tmp, "init")
            self.assertEqual(code, 1)  # does not overwrite

    def test_missing_credentials_and_missing_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, text = self.run_cli("--dir", tmp, "sync")
            self.assertEqual(code, 2)
            self.assertIn("roadgram init", text)
            self.run_cli("--dir", tmp, "init")
            with mock.patch.dict("os.environ", {}, clear=True):
                code, text = self.run_cli("--dir", tmp, "sync")
            self.assertEqual(code, 2)
            self.assertIn("TELEGRAM_BOT_TOKEN", text)

    def test_env_and_config_with_a_windows_bom_are_read(self):
        from roadgram.telegram import credentials
        with tempfile.TemporaryDirectory() as tmp:
            self.run_cli("--dir", tmp, "init")
            root = Path(tmp)
            (root / ".env").write_text("TELEGRAM_BOT_TOKEN=abc\nTELEGRAM_CHAT_ID=-1\n", encoding="utf-8-sig")
            cfg = root / "roadgram.json"
            cfg.write_text(cfg.read_text(encoding="utf-8"), encoding="utf-8-sig")
            with mock.patch.dict("os.environ", {}, clear=True):
                self.assertEqual(credentials(root), ("abc", "-1"))
            code, _ = self.run_cli("--dir", tmp, "status")
            self.assertEqual(code, 0)

    def test_find_root_searches_upwards(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.run_cli("--dir", tmp, "init")
            sub = Path(tmp) / "a" / "b"
            sub.mkdir(parents=True)
            self.assertEqual(find_root(sub), Path(tmp))

    def test_post_dry_run_escapes_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.run_cli("--dir", tmp, "init")
            code, text = self.run_cli("--dir", tmp, "post", "--text", "a <b> & c", "--dry-run")
            self.assertEqual(code, 0)
            self.assertIn("a &lt;b&gt; &amp; c", text)


class AgentInstallTests(unittest.TestCase):
    def test_install_is_idempotent_and_keeps_user_content(self):
        from roadgram import agents
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as h:
            base, home = Path(d), Path(h)
            (base / "AGENTS.md").write_text("# mine" + chr(10), encoding="utf-8")
            agents.run(list(agents.TOOLS), base, home)
            agents.run(list(agents.TOOLS), base, home)
            text = (base / "AGENTS.md").read_text(encoding="utf-8")
            self.assertEqual(text.count(agents.BEGIN), 1)
            self.assertTrue(text.startswith("# mine"))
            self.assertTrue((base / ".claude/skills/roadgram/SKILL.md").exists())
            self.assertTrue((base / ".clinerules/roadgram.md").exists())
            agents.run(list(agents.TOOLS), base, home, uninstall=True)
            self.assertEqual((base / "AGENTS.md").read_text(encoding="utf-8").strip(), "# mine")
            self.assertFalse((base / "GEMINI.md").exists())
            self.assertFalse((base / ".clinerules").exists())


if __name__ == "__main__":
    unittest.main()

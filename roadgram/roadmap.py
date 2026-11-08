"""Parse a Markdown roadmap and render the Telegram messages (HTML parse mode).

Roadmap format (English or Persian headings):

    ## Week 1: Title          (or: ## هفته ۱: عنوان;  Sprint / Phase / Milestone also work)
    - [x] a finished task
    - [ ] an open task
    - **Checkpoint:** optional line (shown in the plan)
    - **Output:** what the week delivers
"""
import html
import re
from datetime import date

from roadgram.dates import FA_TO_EN, date_text, digits
from roadgram.i18n import STRINGS

TELEGRAM_LIMIT = 4096

WEEK_RE = re.compile(r"^##\s+(?:Week|Sprint|Phase|Milestone|هفته)\s+([0-9۰-۹]+)\s*[:：\-–—]\s*(.+)$", re.IGNORECASE)
ITEM_RE = re.compile(r"^[-*]\s+\[([ xX])\]\s+(.+)$")
OUTPUT_RE = re.compile(r"^[-*]\s+\*\*(?:Output|Deliverable|خروجی)\s*:?\s*\*\*\s*:?\s*(.*)$", re.IGNORECASE)
CHECKPOINT_RE = re.compile(r"^[-*]\s+\*\*(?:Checkpoint|چک‌پوینت)", re.IGNORECASE)


def parse_roadmap(text: str) -> dict[int, dict]:
    """{week: {"title", "items": [(done, text)], "output", "checkpoint"}}"""
    weeks: dict[int, dict] = {}
    cur = None
    for line in text.splitlines():
        m = WEEK_RE.match(line.strip())
        if m:
            cur = int(m.group(1).translate(FA_TO_EN))
            weeks[cur] = {"title": m.group(2).strip(), "items": [], "output": "", "checkpoint": ""}
            continue
        if line.startswith("#"):
            cur = None
            continue
        if cur is None:
            continue
        m = ITEM_RE.match(line)
        if m:
            weeks[cur]["items"].append((m.group(1).lower() == "x", m.group(2).strip()))
        elif CHECKPOINT_RE.match(line):
            weeks[cur]["checkpoint"] = re.sub(r"\*\*", "", line.lstrip("-* ").strip())
        else:
            m = OUTPUT_RE.match(line)
            if m:
                weeks[cur]["output"] = m.group(1).strip()
    return weeks


def week_done(data: dict) -> bool:
    return bool(data["items"]) and all(done for done, _ in data["items"])


def clean(text: str, limit: int) -> str:
    """Plain text of a Markdown item, shortened and HTML-escaped."""
    s = re.sub(r"[`*~]|\[([^\]]*)\]\([^)]*\)", lambda m: m.group(1) or "", text).strip()
    if len(s) > limit:
        s = s[: limit - 1].rstrip() + "…"
        if s.count("(") > s.count(")"):
            s = s[: s.rfind("(")].rstrip(" ،,…") + "…"
    return html.escape(s, quote=False)


def bar(done: int, total: int, width: int = 10) -> str:
    n = round(width * done / total) if total else 0
    return "▰" * n + "▱" * (width - n)


def hashtags(cfg: dict, kind: str, week: int) -> str:
    s = STRINGS[cfg["language"]]
    tags = [s[kind], s["tag_week"].format(n=digits(week, cfg["language"] == "fa"))]
    if cfg.get("hashtag"):
        tags.append(cfg["hashtag"])
    return " ".join("#" + t.replace(" ", "_") for t in tags)


def fit(lines: list[str], tail: list[str], more_text) -> str:
    """Join lines + tail and, if over the Telegram limit, drop lines from the end of the body (not the tail)."""
    body = list(lines)
    dropped = 0
    while len("\n".join(body + tail)) > TELEGRAM_LIMIT and len(body) > 3:
        body.pop()
        dropped += 1
    if dropped:
        body.append(more_text(dropped))
    return "\n".join(body + tail)


def render_week(cfg: dict, week: int, data: dict, today: date) -> str:
    lang = cfg["language"]
    s, fa = STRINGS[lang], lang == "fa"
    items = data["items"]
    done, total = sum(1 for d, _ in items if d), len(items)
    pct = round(100 * done / total) if total else 0
    limit = cfg.get("max_item_len", 120)
    head = [f"<b>🗺 {s['week']} {digits(week, fa)}: {clean(data['title'], 200)}</b>",
            s["progress"].format(done=digits(done, fa), total=digits(total, fa), pct=digits(pct, fa)),
            bar(done, total), ""]
    body = head + [f"{'✅' if d else '⬜'} {clean(t, limit)}" for d, t in items]
    tail = []
    if data["output"]:
        tail += ["", f"<b>{s['output']}:</b> {clean(data['output'], 200)}"]
    tail += ["", f"📅 {s['updated']}: {date_text(today, lang, cfg['calendar'])}", "", hashtags(cfg, "tag_roadmap", week)]
    return fit(body, tail, lambda n: s["more"].format(n=digits(n, fa)))


def render_plan(cfg: dict, week: int, data: dict, prev: dict | None, today: date) -> str:
    """The plan for `week`: its goals, checkpoint/output, and what is still open from the previous week."""
    lang = cfg["language"]
    s, fa = STRINGS[lang], lang == "fa"
    limit = cfg.get("max_item_len", 120)
    body = [f"<b>📅 {s['plan']} {digits(week, fa)}: {clean(data['title'], 200)}</b>",
            s["goals"].format(n=digits(len(data["items"]), fa)), ""]
    body += [f"{digits(i, fa)}. {clean(t, limit)}" for i, (_, t) in enumerate(data["items"], 1)]
    tail = []
    if data["checkpoint"]:
        tail += ["", f"<b>{clean(data['checkpoint'], 200)}</b>"]
    if data["output"]:
        tail += ["", f"<b>{s['output']}:</b> {clean(data['output'], 200)}"]
    if prev is not None:
        open_prev = [t for d, t in prev["items"] if not d]
        if open_prev:
            tail += ["", f"<b>{s['carried'].format(n=digits(len(open_prev), fa))}</b>"]
            tail += [f"• {clean(t, 70)}" for t in open_prev[:10]]
        else:
            tail += ["", f"<b>{s['prev_done']}</b>"]
    tail += ["", s["advance_note"], f"📅 {s['updated']}: {date_text(today, lang, cfg['calendar'])}", "",
             hashtags(cfg, "tag_plan", week)]
    return fit(body, tail, lambda n: s["more"].format(n=digits(n, fa)))

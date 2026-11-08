"""Parse a Markdown roadmap and render the Telegram messages (HTML parse mode).

Roadmap format (English or Persian headings):

    ## Week 1: Title          (or: ## هفته ۱: عنوان;  Sprint / Phase / Milestone also work)
    - [x] a finished task
    - [ ] an open task
    - **Checkpoint:** optional line (shown in the plan)
    - **Output:** what the week delivers
    - **Payment:** 500 USD           (optional milestone payment, invoiced when the client approves)
    - **Approved:** @client · date   (written by roadgram when the client taps "Approve delivery")
    - **Paid:** date                 (written by roadgram when the payment is marked as received)
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
META_RE = re.compile(r"^[-*]\s+\*\*([^*:]+?)\s*:?\s*\*\*\s*:?\s*(.*)$")
HEADING_RE = re.compile(r"^#")

# Label (any language) -> key. These lines are written back by roadgram, so both languages are always understood.
META_KEYS = {"approved": "approved", "تأیید تحویل": "approved", "تایید تحویل": "approved",
             "payment": "payment", "پرداخت": "payment", "paid": "paid", "پرداخت شد": "paid"}
META_LABELS = {"en": {"approved": "Approved", "payment": "Payment", "paid": "Paid"},
               "fa": {"approved": "تأیید تحویل", "payment": "پرداخت", "paid": "پرداخت شد"}}


def meta_key(line: str) -> str | None:
    m = META_RE.match(line.strip())
    return META_KEYS.get(m.group(1).strip().lower()) if m else None


def parse_roadmap(text: str) -> dict[int, dict]:
    """{week: {"title", "items": [(done, text)], "output", "checkpoint"}}"""
    weeks: dict[int, dict] = {}
    cur = None
    in_comment = False
    for line in text.splitlines():
        if in_comment or line.strip().startswith("<!--"):  # skip <!-- ... --> blocks
            in_comment = "-->" not in line
            continue
        m = WEEK_RE.match(line.strip())
        if m:
            cur = int(m.group(1).translate(FA_TO_EN))
            weeks[cur] = {"title": m.group(2).strip(), "items": [], "output": "", "checkpoint": "",
                          "approved": "", "payment": "", "paid": ""}
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
        elif meta_key(line):
            weeks[cur][meta_key(line)] = META_RE.match(line.strip()).group(2).strip() or "✓"
        else:
            m = OUTPUT_RE.match(line)
            if m:
                weeks[cur]["output"] = m.group(1).strip()
    return weeks


def _split(text: str) -> tuple[list[str], str]:
    nl = "\r\n" if "\r\n" in text else "\n"
    return text.replace("\r\n", "\n").split("\n"), nl


def _section(lines: list[str], week: int) -> tuple[int, int]:
    """(heading index, end index) of a week in the file; raises KeyError if the week is missing."""
    start = None
    for i, line in enumerate(lines):
        m = WEEK_RE.match(line.strip())
        if start is None:
            if m and int(m.group(1).translate(FA_TO_EN)) == week:
                start = i
        elif HEADING_RE.match(line):
            return start, i
    if start is None:
        raise KeyError(week)
    return start, len(lines)


def _last_content(lines: list[str], start: int, end: int) -> int:
    i = end - 1
    while i > start and not lines[i].strip():
        i -= 1
    return i


def set_meta(text: str, week: int, key: str, value: str | None, language: str) -> str:
    """Write (or with value=None remove) the `- **Approved:** ...` style line of a week. Returns the new file text."""
    lines, nl = _split(text)
    start, end = _section(lines, week)
    kept = [line for line in lines[start:end] if meta_key(line) != key]
    lines[start:end] = kept
    if value is not None:
        at = _last_content(lines, start, start + len(kept)) + 1
        lines.insert(at, f"- **{META_LABELS[language][key]}:** {value}")
    return nl.join(lines)


def add_task(text: str, week: int, task: str) -> str:
    """Add an open task `- [ ] task` after the week's last task (or right under its heading)."""
    lines, nl = _split(text)
    start, end = _section(lines, week)
    at = start + 1
    for i in range(start + 1, end):
        if ITEM_RE.match(lines[i]):
            at = i + 1
    lines.insert(at, f"- [ ] {task}")
    return nl.join(lines)


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
    tail += approval_lines(cfg, data)
    tail += ["", f"📅 {s['updated']}: {date_text(today, lang, cfg['calendar'])}", "", hashtags(cfg, "tag_roadmap", week)]
    return fit(body, tail, lambda n: s["more"].format(n=digits(n, fa)))


def approval_lines(cfg: dict, data: dict) -> list[str]:
    """Delivery and payment status shown under a week (empty when approvals are off and no payment is set)."""
    s = STRINGS[cfg["language"]]
    out = []
    if data.get("approved"):
        out.append(f"✅ <b>{s['approved']}</b>: {clean(data['approved'], 120)}")
    elif cfg.get("approval", True) and week_done(data):
        out.append(f"⏳ {s['awaiting_approval']}")
    if data.get("payment"):
        state = (f"✅ {s['paid']}" + (f" ({clean(data['paid'], 60)})" if data["paid"] != "✓" else "")
                 if data.get("paid") else f"⏳ {s['payment_open']}")
        out.append(f"💳 <b>{s['payment']}:</b> {clean(data['payment'], 80)} · {state}")
    return [""] + out if out else []


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

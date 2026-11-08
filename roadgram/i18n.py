"""User-facing strings of the Telegram messages (English and Persian)."""

STRINGS = {
    "en": {
        "week": "Week", "progress": "Progress: {done} of {total} tasks ({pct}%)", "output": "Week output",
        "updated": "Last updated", "plan": "Plan for week", "goals": "{n} goals this week",
        "carried": "Carried over from last week: {n}", "prev_done": "Last week is complete ✅",
        "advance_note": "When every goal of a week is ticked, the next week's roadmap and plan are posted automatically.",
        "more": "… and {n} more", "tag_roadmap": "roadmap", "tag_plan": "plan", "tag_week": "week{n}",
    },
    "fa": {
        "week": "هفته", "progress": "پیشرفت: {done} از {total} کار ({pct}٪)", "output": "خروجی هفته",
        "updated": "آخرین به‌روزرسانی", "plan": "پلن هفته", "goals": "{n} هدف برای این هفته",
        "carried": "مانده از هفته قبل: {n} کار", "prev_done": "هفته قبل کامل شد ✅",
        "advance_note": "هر هفته که همه‌ی اهدافش تیک بخورد، رودمپ و پلن هفته بعد خودکار پست می‌شود.",
        "more": "… و {n} مورد دیگر", "tag_roadmap": "رودمپ", "tag_plan": "پلن", "tag_week": "هفته{n}",
    },
}

DEFAULT_TOPICS = {
    "en": {"roadmap": "🗺 Roadmap", "plan": "📅 Next week plan", "updates": "📣 Updates"},
    "fa": {"roadmap": "🗺 رودمپ", "plan": "📅 پلن هفته آینده", "updates": "📣 به‌روزرسانی‌ها"},
}

SAMPLE_ROADMAP = {
    "en": """# Roadmap

## Week 1: Foundation
- [ ] Set up the repository and CI
- [ ] Write the first working version of the core feature
- [ ] Write tests for the core feature
- **Output:** a working core feature with tests

## Week 2: Launch
- [ ] Add the second feature
- [ ] Prepare the release notes
- **Output:** the first release
""",
    "fa": """# رودمپ

## هفته ۱: پایه‌گذاری
- [ ] راه‌اندازی مخزن و CI
- [ ] نسخه‌ی اول کارکرد اصلی
- [ ] نوشتن تست برای کارکرد اصلی
- **خروجی:** کارکرد اصلی همراه با تست

## هفته ۲: انتشار
- [ ] افزودن قابلیت دوم
- [ ] آماده‌کردن یادداشت انتشار
- **خروجی:** نسخه‌ی اول
""",
}

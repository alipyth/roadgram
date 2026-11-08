"""User-facing strings of the Telegram messages (English and Persian)."""

STRINGS = {
    "en": {
        "week": "Week", "progress": "Progress: {done} of {total} tasks ({pct}%)", "output": "Week output",
        "updated": "Last updated", "plan": "Plan for week", "goals": "{n} goals this week",
        "carried": "Carried over from last week: {n}", "prev_done": "Last week is complete ✅",
        "advance_note": "When every goal of a week is ticked, the next week's roadmap and plan are posted automatically.",
        "more": "… and {n} more", "tag_roadmap": "roadmap", "tag_plan": "plan", "tag_week": "week{n}",
        # client approval
        "btn_approve": "✅ Approve delivery", "btn_change": "✏️ Request changes", "btn_paid": "💰 Mark as paid",
        "approved": "Delivery approved", "awaiting_approval": "All tasks done: waiting for the client to approve delivery",
        "payment": "Payment", "paid": "paid", "payment_open": "open",
        "only_client": "Only the client can approve or request changes for this project.",
        "only_owner": "Only the project owner can mark a payment as received.",
        "already_approved": "This week is already approved ✅", "approved_ok": "Thanks! Delivery of week {n} is approved ✅",
        "unknown_week": "This week is no longer in the roadmap.",
        "change_prompt": "✏️ {user}, reply to this message with the changes you need for week {n}.",
        "change_hint": "Reply to the bot's message with your change request.",
        "change_saved": "✏️ Recorded. Your request was added to week {n} as a new task.",
        "dm_approved": "✅ {user} approved delivery of week {n}: {title}",
        "dm_change": "✏️ {user} requested a change in week {n}: {text}",
        "dm_paid": "💰 Payment of week {n} marked as received.",
        "whoami": "Your Telegram id: <code>{id}</code>\nThis chat id: <code>{chat}</code>",
        # invoices
        "invoice_title": "💳 Invoice · week {n}: {title}", "amount": "Amount", "approved_by": "Delivery approved by",
        "pay_to": "Payment details", "invoice_paid": "✅ Paid on {date}", "invoice_open": "⏳ Waiting for payment",
        "reminder": "⏰ Payment reminder: week {n} ({amount}) is still open.", "tag_invoice": "invoice",
    },
    "fa": {
        "week": "هفته", "progress": "پیشرفت: {done} از {total} کار ({pct}٪)", "output": "خروجی هفته",
        "updated": "آخرین به‌روزرسانی", "plan": "پلن هفته", "goals": "{n} هدف برای این هفته",
        "carried": "مانده از هفته قبل: {n} کار", "prev_done": "هفته قبل کامل شد ✅",
        "advance_note": "هر هفته که همه‌ی اهدافش تیک بخورد، رودمپ و پلن هفته بعد خودکار پست می‌شود.",
        "more": "… و {n} مورد دیگر", "tag_roadmap": "رودمپ", "tag_plan": "پلن", "tag_week": "هفته{n}",
        # تأیید مشتری
        "btn_approve": "✅ تأیید تحویل", "btn_change": "✏️ درخواست تغییر", "btn_paid": "💰 پرداخت شد",
        "approved": "تحویل تأیید شد", "awaiting_approval": "همه‌ی کارها انجام شد: منتظر تأیید تحویل از طرف مشتری",
        "payment": "پرداخت", "paid": "پرداخت شد", "payment_open": "باز",
        "only_client": "فقط مشتری می‌تواند تحویل را تأیید کند یا درخواست تغییر بدهد.",
        "only_owner": "فقط صاحب پروژه می‌تواند دریافت پرداخت را ثبت کند.",
        "already_approved": "این هفته قبلاً تأیید شده ✅", "approved_ok": "ممنون! تحویل هفته {n} تأیید شد ✅",
        "unknown_week": "این هفته دیگر در رودمپ نیست.",
        "change_prompt": "✏️ {user}، لطفاً تغییرات لازم برای هفته {n} را در پاسخ (Reply) به همین پیام بنویسید.",
        "change_hint": "درخواست تغییر را در پاسخ به پیام ربات بنویسید.",
        "change_saved": "✏️ ثبت شد. درخواست شما به‌عنوان یک کار جدید به هفته {n} اضافه شد.",
        "dm_approved": "✅ {user} تحویل هفته {n} را تأیید کرد: {title}",
        "dm_change": "✏️ {user} برای هفته {n} درخواست تغییر داد: {text}",
        "dm_paid": "💰 پرداخت هفته {n} دریافت‌شده ثبت شد.",
        "whoami": "شناسه‌ی تلگرام شما: <code>{id}</code>\nشناسه‌ی این چت: <code>{chat}</code>",
        # فاکتور
        "invoice_title": "💳 فاکتور · هفته {n}: {title}", "amount": "مبلغ", "approved_by": "تحویل تأییدشده توسط",
        "pay_to": "اطلاعات پرداخت", "invoice_paid": "✅ پرداخت شد در {date}", "invoice_open": "⏳ در انتظار پرداخت",
        "reminder": "⏰ یادآوری پرداخت: هفته {n} ({amount}) هنوز پرداخت نشده است.", "tag_invoice": "فاکتور",
    },
}

DEFAULT_TOPICS = {
    "en": {"roadmap": "🗺 Roadmap", "plan": "📅 Next week plan", "updates": "📣 Updates", "payments": "💳 Payments"},
    "fa": {"roadmap": "🗺 رودمپ", "plan": "📅 پلن هفته آینده", "updates": "📣 به‌روزرسانی‌ها", "payments": "💳 پرداخت‌ها"},
}

SAMPLE_ROADMAP = {
    "en": """# Roadmap

## Week 1: Foundation
- [ ] Set up the repository and CI
- [ ] Write the first working version of the core feature
- [ ] Write tests for the core feature
- **Output:** a working core feature with tests
<!-- Optional milestone payment, invoiced when the client approves this week:
- **Payment:** 500 USD
-->

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
<!-- پرداخت مرحله‌ای (اختیاری)؛ با تأیید این هفته توسط مشتری فاکتورش ارسال می‌شود:
- **پرداخت:** ۱۰ میلیون تومان
-->

## هفته ۲: انتشار
- [ ] افزودن قابلیت دوم
- [ ] آماده‌کردن یادداشت انتشار
- **خروجی:** نسخه‌ی اول
""",
}

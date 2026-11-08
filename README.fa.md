<div align="center">

<img src="assets/banner.svg" alt="roadgram" width="100%">

<br>

[English](README.md) · **فارسی**

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-26A5E4?logo=telegram&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

[🌐 وبسایت](https://jahaniwww.com) · [📣 کانال تلگرام](https://t.me/tarfandoonchannel)

</div>

---

<div dir="rtl">

## ✨ roadgram چیست؟

**roadgram** رودمپ، پلن هفتگی و اطلاعیه‌های یک پروژه را داخل یک گروه تلگرام نگه می‌دارد. توسعه‌دهنده و مدیر پروژه (یا کارفرما) بدون هیچ ابزار دیگری، پیشرفت کار را یک‌جا می‌بینند.

</div>

<div align="center">
<img src="assets/flow.svg" alt="ROADMAP.md → roadgram sync → Telegram" width="90%">
</div>

<div dir="rtl">

رودمپ را مثل یک چک‌لیست ساده‌ی Markdown در مخزن پروژه می‌نویسید. بعد از هر تغییر یک دستور می‌زنید و پیام‌های تلگرام خودشان به‌روز می‌شوند.

## 🚀 امکانات

| | امکان | توضیح |
|---|---|---|
| 🗺 | **تاپیک رودمپ** | برای هر هفته یک پیام با نوار پیشرفت و ✅/⬜ برای هر کار. همان‌جا ویرایش می‌شود و پین است. |
| 📅 | **پلن هفته‌ی آینده** | اهداف هفته‌ی بعد و کارهای مانده. فقط جدیدترین پلن پین می‌ماند. |
| ⏭ | **پیشروی خودکار** | وقتی همه‌ی کارهای هفته تیک بخورد، رودمپ و پلن هفته‌ی بعد خودکار پست و پین می‌شود. |
| 📣 | **تاپیک اطلاعیه‌ها** | اطلاعیه و فایل با `roadgram post`، فقط وقتی خودتان بفرستید. |
| 🌍 | **دو زبانه** | پیام‌ها فارسی یا انگلیسی، با تاریخ میلادی، شمسی یا هر دو. |
| 🤖 | **سازگار با ابزارهای هوش مصنوعی** | `roadgram agent install` کار با Claude Code، Codex، Cline، Cursor و Gemini CLI را یادشان می‌دهد. |
| 📦 | **بدون وابستگی** | فقط کتابخانه‌ی استاندارد پایتون، و یک فایل اجرایی تک‌فایلی `roadgram.exe` برای ویندوز. |

## 📥 نصب از صفر

roadgram به **پایتون ۳٫۱۰ یا بالاتر** و **git** نیاز دارد و وابستگی دیگری ندارد. برای ربات هم یک حساب تلگرام لازم است (بخش [شروع سریع](#-شروع-سریع)).

### ویندوز

</div>

```powershell
# ۱. نصب پایتون و git (آنچه دارید را رد کنید)
winget install Python.Python.3.12
winget install Git.Git
# PowerShell را ببندید و دوباره باز کنید، بعد بررسی کنید:
python --version

# ۲. نصب roadgram
python -m pip install git+https://github.com/alipyth/roadgram.git

# ۳. بررسی کارکرد
roadgram --version
```

<div dir="rtl">

اگر `roadgram` شناخته نشد، به‌جایش `python -m roadgram --version` را بزنید، یا پوشه‌ی `Scripts` پایتون را به `PATH` اضافه کنید.

### مک (macOS)

</div>

```bash
# ۱. نصب پایتون و git (با Homebrew: https://brew.sh)
brew install python git
python3 --version

# ۲. نصب roadgram (pipx آن را جدا نگه می‌دارد و دستور roadgram را در PATH می‌گذارد)
brew install pipx && pipx ensurepath
pipx install git+https://github.com/alipyth/roadgram.git

# ۳. بررسی کارکرد (اول یک ترمینال تازه باز کنید)
roadgram --version
```

<div dir="rtl">

### لینوکس (دبیان / اوبونتو؛ توزیع‌های دیگر مدیر بسته‌ی خودشان را دارند)

</div>

```bash
# ۱. نصب پایتون، pip و git
sudo apt update
sudo apt install -y python3 python3-pip pipx git
python3 --version        # باید ۳٫۱۰ یا بالاتر باشد

# ۲. نصب roadgram
pipx ensurepath
pipx install git+https://github.com/alipyth/roadgram.git

# ۳. بررسی کارکرد (اول یک ترمینال تازه باز کنید)
roadgram --version
```

<div dir="rtl">

در فدورا: `sudo dnf install python3 pipx git` و در آرچ: `sudo pacman -S python python-pipx git`.

### از روی clone (هر سیستم‌عامل، برای توسعه)

</div>

```bash
git clone https://github.com/alipyth/roadgram.git
cd roadgram
python -m pip install .            # یا: python -m pip install -e .   (حالت ویرایشی)
python -m unittest discover -s tests -t .      # اختیاری: اجرای تست‌ها
```

<div dir="rtl">

بدون نصب هم می‌توانید مستقیم از داخل clone اجرا کنید: `python -m roadgram --version`.

### به‌روزرسانی و حذف

</div>

```bash
pipx upgrade roadgram          # یا: python -m pip install --upgrade git+https://github.com/alipyth/roadgram.git
pipx uninstall roadgram        # یا: python -m pip uninstall roadgram
```

<div dir="rtl">

### ویندوز: یک فایل `roadgram.exe` (بدون پایتون روی سیستم مقصد)

روی یک سیستم که پایتون دارد یک بار بسازید و `dist\roadgram.exe` را هرجا خواستید کپی کنید:

</div>

```powershell
git clone https://github.com/alipyth/roadgram.git
cd roadgram
powershell -File build_exe.ps1     # تست‌ها را اجرا می‌کند، PyInstaller را نصب می‌کند و dist\roadgram.exe را می‌سازد
.\dist\roadgram.exe --version
```

<div dir="rtl">

## 🧭 اولین اجرا، قدم‌به‌قدم

۱. [آماده‌سازی تلگرام](#۱-آماده‌سازی-تلگرام-یک-بار-حدود-۵-دقیقه) را انجام دهید و **توکن ربات** و **شناسه‌ی گروه** را کنار دستتان داشته باشید.
۲. ترمینال را **داخل پوشه‌ی پروژه** (همان مخزنی که می‌خواهید دنبال کنید) باز کنید.
۳. `roadgram init --name "My App"` فایل‌های `roadgram.json`، `.env` و `ROADMAP.md` را می‌سازد و `.gitignore` را به‌روز می‌کند.
۴. `.env` را باز کنید و مقدارها را بگذارید (مثال زیر):
۵. `ROADMAP.md` را با هفته‌ها و کارهای واقعی خودتان ویرایش کنید.
۶. `roadgram check` باید بگوید توکن، گروه و دسترسی‌ها درست‌اند.
۷. `roadgram week 1 --dry-run` پیام را بدون ارسال نشان می‌دهد.
۸. `roadgram week 1` و `roadgram plan 2` پیام‌های واقعی را پست و پین می‌کنند.
۹. از این به بعد: در `ROADMAP.md` تیک بزنید و `roadgram sync` را اجرا کنید.

</div>

```ini
# .env
TELEGRAM_BOT_TOKEN=123456:ABC-your-token
TELEGRAM_CHAT_ID=-1001234567890
```

<div dir="rtl">

## 👀 خروجی چه شکلی است؟

نتیجه‌ی `roadgram week 1` (پیامی که در تاپیک تلگرام می‌بینید):

</div>

```text
🗺 هفته ۱: پایه‌گذاری
پیشرفت: ۱ از ۳ کار (۳۳٪)
▰▰▰▱▱▱▱▱▱▱

✅ راه‌اندازی مخزن و CI
⬜ نسخه‌ی اول کارکرد اصلی
⬜ نوشتن تست برای کارکرد اصلی

خروجی هفته: کارکرد اصلی همراه با تست

📅 آخرین به‌روزرسانی: ۱۶ آبان ۱۴۰۵

#roadmap #week1 #MyApp
```

<div dir="rtl">

## ⚡ شروع سریع

### ۱. آماده‌سازی تلگرام (یک بار، حدود ۵ دقیقه)

۱. به **@BotFather** بروید ← `/newbot` ← **توکن** را کپی کنید.
۲. یک گروه بسازید (یا از گروه موجود استفاده کنید) و ربات را اضافه کنید.
۳. برای داشتن یک تاپیک به‌ازای هر بخش، در تنظیمات گروه **Topics** را روشن کنید. بدون تاپیک هم کار می‌کند و پیام‌ها در چت اصلی می‌روند.
۴. ربات را **ادمین** کنید با دسترسی **Pin messages** و (اگر تاپیک روشن است) **Manage topics**.
۵. شناسه‌ی گروه را پیدا کنید (شکلش `-1001234567890` است): یک پیام گروه را برای **@RawDataBot** فوروارد کنید.

> [!IMPORTANT]
> **توکن را محرمانه نگه دارید.** فقط در `.env` می‌ماند و `roadgram init` آن را به `.gitignore` اضافه می‌کند. roadgram هرگز توکن را چاپ، لاگ یا داخل پیام نمی‌گذارد. اگر لو رفت، در @BotFather دستور `/revoke` را بزنید.

### ۲. اجرا

</div>

```powershell
# داخل پوشه‌ی پروژه (roadgram.exe، یا: python -m roadgram ...)
roadgram init --name "My App" --lang fa --calendar jalali   # roadgram.json، .env، ROADMAP.md و .gitignore
# TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID را در .env بگذارید، بعد:
roadgram check                 # توکن، گروه، تاپیک‌ها و دسترسی‌های ربات را بررسی می‌کند
roadgram week 1 --dry-run      # پیش‌نمایش پیام (چیزی نمی‌فرستد)
roadgram week 1                # رودمپ هفته ۱ را پست و پین می‌کند
roadgram plan 2                # پلن هفته ۲ را پست و پین می‌کند
# ... کار کنید و در ROADMAP.md تیک بزنید ...
roadgram sync                  # همه‌ی پیام‌ها را ویرایش می‌کند؛ اگر هفته کامل شد هفته‌ی بعد را پست می‌کند
roadgram post --text "نسخه‌ی آزمایشی آماده است" --pin
roadgram post --document report.pdf --text "گزارش هفتگی"
roadgram status                # پیشرفت را در ترمینال نشان می‌دهد، چیزی نمی‌فرستد
```

<div dir="rtl">

> [!TIP]
> بعد از هر تغییر `ROADMAP.md` دستور `roadgram sync` را اجرا کنید. hook گیت یا یک مرحله‌ی CI هم مناسب است.

### ۳. فایل رودمپ

</div>

```markdown
## هفته ۱: پایه‌گذاری
- [x] راه‌اندازی مخزن و CI
- [ ] نسخه‌ی اول کارکرد اصلی
- **چک‌پوینت ۱: جمعه**          (اختیاری، در پلن نشان داده می‌شود)
- **خروجی:** کارکرد اصلی آماده     (اختیاری)

## هفته ۲: انتشار
- [ ] ...
```

<div dir="rtl">

عنوان `## هفته N: ...` (یا `Week` / `Sprint` / `Phase` / `Milestone` انگلیسی) یک هفته را شروع می‌کند و خط‌های `- [ ]` و `- [x]` کارهای آن هستند.

## 🤖 استفاده از داخل ابزارهای هوش مصنوعی

</div>

```powershell
roadgram agent install            # ابزارهای نصب‌شده را خودکار پیدا و نصب می‌کند
roadgram agent install all        # یا نام ببرید: claude codex cline cursor gemini
roadgram agent install --global   # برای کل کاربر، نه فقط همین پروژه
roadgram agent install --uninstall
```

<div dir="rtl">

برای هر ابزار فرمت خودش نوشته می‌شود: skill و دستور `/roadgram-sync` برای Claude Code (با `.claude-plugin`)، یک بلوک علامت‌دار در `AGENTS.md` (Codex) و `GEMINI.md`، فایل `.clinerules/roadgram.md` (Cline) و `.cursor/rules/roadgram.mdc` (Cursor). اجرای دوباره فقط به‌روز می‌کند و متن خودتان دست‌نخورده می‌ماند. به agent گفته شده هرگز `.env` را نخواند.

## 📖 دستورها

| دستور | کار |
|---|---|
| `roadgram init` | `roadgram.json`، الگوی `.env`، یک `ROADMAP.md` نمونه و ورودی‌های `.gitignore` را می‌سازد. بدون `--force` چیزی را بازنویسی نمی‌کند. |
| `roadgram check` | توکن، گروه، تاپیک‌ها و دسترسی ادمین ربات را بررسی می‌کند. |
| `roadgram week N [--dry-run]` | پیام رودمپ هفته‌ی N را پست یا ویرایش می‌کند (بار اول پین می‌شود). |
| `roadgram plan N [--dry-run]` | پیام پلن هفته‌ی N را پست یا ویرایش می‌کند؛ پلن‌های قدیمی از پین درمی‌آیند. |
| `roadgram sync` | همه‌ی پیام‌های پست‌شده را ویرایش می‌کند؛ وقتی هفته‌ی جاری کامل شد، هفته‌ی بعد را پست می‌کند. |
| `roadgram post` | پیام یا فایل **جدید** به یک تاپیک می‌فرستد (`--topic`، `--text`، `--file`، `--document`، `--pin`، `--raw-html`، `--dry-run`). |
| `roadgram status` | پیشرفت را از فایل رودمپ چاپ می‌کند. |
| `roadgram agent install` | دستورالعمل roadgram را برای ابزارهای هوش مصنوعی نصب می‌کند. |

گزینه‌ی کلی: `--dir <پوشه>` (پیش‌فرض پوشه‌ی جاری؛ `roadgram.json` به سمت بالا جست‌وجو می‌شود).

## ⚙️ تنظیمات (`roadgram.json`)

| کلید | معنی | پیش‌فرض |
|---|---|---|
| `project` | نام پروژه | نام پوشه |
| `hashtag` | هشتگ پیام‌ها (`""` یعنی هیچ) | نام بدون فاصله |
| `language` | `en` یا `fa` | `en` |
| `calendar` | `gregorian`، `jalali` یا `both` | `gregorian` |
| `roadmap_file` | مسیر فایل رودمپ | `ROADMAP.md` |
| `topics` | نام تاپیک‌ها بر اساس کلید: `roadmap`، `plan`، `updates` (برای `roadgram post --topic` کلید خودتان را اضافه کنید) | بسته به زبان |
| `max_item_len` | بیشینه‌ی طول متن هر کار در پیام | `120` |
| `advance` | با کامل شدن هفته‌ی جاری، هفته‌ی بعد خودکار پست شود | `true` |

شناسه‌ی پیام‌ها و تاپیک‌ها در `.roadgram/state.json` می‌ماند. اگر پیامی را در تلگرام پاک کردید، شناسه‌اش را از این فایل بردارید تا اجرای بعد پیام تازه بفرستد.

## 🛠 ساخت فایل اجرایی

</div>

```powershell
powershell -File build_exe.ps1     # اول تست‌ها را اجرا می‌کند، بعد dist\roadgram.exe را با PyInstaller می‌سازد
```

<div dir="rtl">

فقط تست‌ها: `python -m unittest discover -s tests -t .`

## 🔒 نکته‌ها و محدودیت‌ها

- roadgram فقط همان چیزی را می‌فرستد که شما بخواهید (`week`، `plan`، `sync`، `post`) و پیام‌های گروه را نمی‌خواند.
- توکن هیچ‌وقت در خروجی و خطاها نمی‌آید؛ در خطای شبکه فقط نوع خطا نشان داده می‌شود.
- پیام تلگرام حداکثر ۴۰۹۶ نویسه دارد. هفته‌های طولانی با «… و N مورد دیگر» کوتاه می‌شوند.
- ویرایشگرهای ویندوز ممکن است به `.env` و `roadgram.json` یک BOM اضافه کنند؛ roadgram هر دو را درست می‌خواند.

</div>

---

<div align="center">

مجوز MIT · ساخته‌ی [علی جهانی](https://jahaniwww.com)

</div>

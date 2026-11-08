"""Date helpers: Gregorian -> Jalali (Persian calendar) and display text in English or Persian."""
from datetime import date

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
FA_TO_EN = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

GREG_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
           "November", "December"]
GREG_FA = ["ژانویه", "فوریه", "مارس", "آوریل", "مه", "ژوئن", "ژوئیه", "اوت", "سپتامبر", "اکتبر", "نوامبر", "دسامبر"]
JALALI_FA = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]


def digits(value, persian: bool) -> str:
    s = str(value)
    return s.translate(FA_DIGITS) if persian else s


def gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = 355666 + 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400 + gd + g_d_m[gm - 1]
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        return jy, 1 + days // 31, 1 + days % 31
    return jy, 7 + (days - 186) // 30, 1 + (days - 186) % 30


def date_text(d: date, language: str, calendar: str) -> str:
    """calendar: gregorian | jalali | both. Persian text uses Persian digits."""
    persian = language == "fa"
    months = GREG_FA if persian else GREG_EN
    greg = f"{digits(d.day, persian)} {months[d.month - 1]} {digits(d.year, persian)}"
    jy, jm, jd = gregorian_to_jalali(d.year, d.month, d.day)
    jal = f"{digits(jd, persian)} {JALALI_FA[jm - 1]} {digits(jy, persian)}"
    if calendar == "jalali":
        return jal
    if calendar == "both":
        return f"{jal} ({greg})"
    return greg

import calendar
import re
from datetime import date, timedelta

MONTHS: dict[str, int] = {}
for _i, _name in enumerate(calendar.month_name):
    if _name:
        MONTHS[_name.lower()] = _i
        MONTHS[_name[:3].lower()] = _i
MONTHS["sept"] = 9

WEEKDAYS: dict[str, int] = {}
for _i, _name in enumerate(calendar.day_name):
    WEEKDAYS[_name.lower()] = _i
    WEEKDAYS[_name[:3].lower()] = _i
WEEKDAYS.update({"tues": 1, "weds": 2, "thur": 3, "thurs": 3})

_ONES = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
]
_TENS = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}
NUMBER_WORDS: dict[str, int] = {w: i for i, w in enumerate(_ONES)}
NUMBER_WORDS.update(_TENS)
NUMBER_WORDS.update({"a": 1, "an": 1, "the": 1, "couple": 2})

_ORD_ONES = [
    "",
    "first",
    "second",
    "third",
    "fourth",
    "fifth",
    "sixth",
    "seventh",
    "eighth",
    "ninth",
    "tenth",
    "eleventh",
    "twelfth",
    "thirteenth",
    "fourteenth",
    "fifteenth",
    "sixteenth",
    "seventeenth",
    "eighteenth",
    "nineteenth",
]
ORDINAL_WORDS: dict[str, int] = {w: i for i, w in enumerate(_ORD_ONES) if w}
ORDINAL_WORDS["twentieth"] = 20
ORDINAL_WORDS["thirtieth"] = 30
for _i in range(1, 10):
    ORDINAL_WORDS[f"twenty-{_ORD_ONES[_i]}"] = 20 + _i
ORDINAL_WORDS["thirty-first"] = 31

UNITS: dict[str, tuple[int, int]] = {
    "day": (1, 0),
    "week": (7, 0),
    "fortnight": (14, 0),
    "month": (0, 1),
    "year": (0, 12),
    "decade": (0, 120),
}

_MONTH_RE = "|".join(sorted(MONTHS, key=len, reverse=True))
_WEEKDAY_RE = "|".join(sorted(WEEKDAYS, key=len, reverse=True))
_DAY_RE = r"(\d{1,2}(?:st|nd|rd|th)?|" + "|".join(ORDINAL_WORDS) + ")"
_YEAR_RE = r"(\d{4})"


def parse(s: str, today: date | None = None) -> date:
    if today is None:
        today = date.today()
    text = _normalize(s)
    if not text:
        raise ValueError("empty date string")
    return _parse(text, today)


def _normalize(s: str) -> str:
    text = s.strip().lower()
    text = re.sub(r"(?<=[a-z])\.", "", text)
    text = text.replace(",", " ")
    text = re.sub(r"[!?;]+$", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^on ", "", text)
    return text


def _parse(text: str, today: date) -> date:
    simple = {
        "today": 0,
        "now": 0,
        "tonight": 0,
        "tomorrow": 1,
        "yesterday": -1,
        "the day after tomorrow": 2,
        "day after tomorrow": 2,
        "the day before yesterday": -2,
        "day before yesterday": -2,
    }
    if text in simple:
        return today + timedelta(days=simple[text])

    m = re.fullmatch(
        r"(.+?) (before|after|from|prior to|past|since|until|till) (.+)", text
    )
    if m:
        offset, direction, anchor = m.groups()
        duration = _parse_duration(offset)
        if duration is not None:
            base = today if anchor == "now" else _parse(anchor, today)
            sign = -1 if direction in ("before", "prior to", "until", "till") else 1
            return _shift(base, duration, sign)

    m = re.fullmatch(r"in (.+)", text)
    if m and (duration := _parse_duration(m.group(1))) is not None:
        return _shift(today, duration, 1)
    m = re.fullmatch(r"(.+) (ago|earlier|back|later|hence|from now)", text)
    if m and (duration := _parse_duration(m.group(1))) is not None:
        sign = -1 if m.group(2) in ("ago", "earlier", "back") else 1
        return _shift(today, duration, sign)

    relative = _parse_relative(text, today)
    if relative is not None:
        return relative

    absolute = _parse_absolute(text, today)
    if absolute is not None:
        return absolute

    raise ValueError(f"unrecognized date: {text!r}")


def _parse_duration(text: str) -> tuple[int, int] | None:
    tokens = re.sub(r"\b(and|of)\b", " ", text).split()
    days = months = 0
    i = 0
    found = False
    while i < len(tokens):
        value, i = _read_number(tokens, i)
        if i >= len(tokens):
            return None
        unit = tokens[i].removesuffix("s")
        if unit not in UNITS:
            return None
        unit_days, unit_months = UNITS[unit]
        n = 1 if value is None else value
        days += n * unit_days
        months += n * unit_months
        i += 1
        found = True
    return (days, months) if found else None


def _read_number(tokens: list[str], i: int) -> tuple[int | None, int]:
    tok = tokens[i]
    if tok.isdigit():
        return int(tok), i + 1
    if (
        tok in ("a", "an", "the")
        and i + 1 < len(tokens)
        and tokens[i + 1] in ("couple", "few")
    ):
        i += 1
        tok = tokens[i]
    if tok == "few":
        return 3, i + 1
    parts = tok.split("-")
    if all(p in NUMBER_WORDS for p in parts):
        total = sum(NUMBER_WORDS[p] for p in parts)
        if (
            len(parts) == 1
            and tok in _TENS
            and i + 1 < len(tokens)
            and tokens[i + 1] in _ONES[1:10]
        ):
            return total + NUMBER_WORDS[tokens[i + 1]], i + 2
        return total, i + 1
    return None, i


def _shift(d: date, duration: tuple[int, int], sign: int) -> date:
    days, months = duration
    return _add_months(d, sign * months) + timedelta(days=sign * days)


def _add_months(d: date, n: int) -> date:
    years, month_index = divmod(d.month - 1 + n, 12)
    year = d.year + years
    month = month_index + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _parse_relative(text: str, today: date) -> date | None:
    m = re.fullmatch(
        r"(next|last|this|this coming|coming|this past|past|previous) "
        r"(week|month|year|day|" + _WEEKDAY_RE + ")",
        text,
    )
    if m:
        modifier, target = m.groups()
        if target in UNITS:
            if modifier in ("this", "this coming", "coming"):
                return today if modifier == "this" else None
            sign = 1 if modifier == "next" else -1
            return _shift(today, UNITS[target], sign)
        weekday = WEEKDAYS[target]
        if modifier in ("next", "this coming", "coming"):
            return _next_weekday(today, weekday, include_today=False)
        if modifier == "this":
            return _next_weekday(today, weekday, include_today=True)
        return _prev_weekday(today, weekday)

    if text in WEEKDAYS:
        return _next_weekday(today, WEEKDAYS[text], include_today=True)
    return None


def _next_weekday(today: date, weekday: int, include_today: bool) -> date:
    ahead = (weekday - today.weekday()) % 7
    if ahead == 0 and not include_today:
        ahead = 7
    return today + timedelta(days=ahead)


def _prev_weekday(today: date, weekday: int) -> date:
    behind = (today.weekday() - weekday) % 7 or 7
    return today - timedelta(days=behind)


def _parse_absolute(text: str, today: date) -> date | None:
    text = re.sub(r"^(?:" + _WEEKDAY_RE + r") (?=\S)", "", text)

    m = re.fullmatch(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", text)
    if m:
        return date(int(m[1]), int(m[2]), int(m[3]))

    m = re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4}|\d{2})", text)
    if m:
        year = int(m[3])
        if len(m[3]) == 2:
            year += 2000
        return date(year, int(m[1]), int(m[2]))

    m = re.fullmatch(rf"({_MONTH_RE}) (?:the )?{_DAY_RE}(?: (?:of )?{_YEAR_RE})?", text)
    if m:
        return _make_date(m[3], MONTHS[m[1]], m[2], today)

    m = re.fullmatch(
        rf"(?:the )?{_DAY_RE}(?: of)? ({_MONTH_RE})(?: (?:of )?{_YEAR_RE})?", text
    )
    if m:
        return _make_date(m[3], MONTHS[m[2]], m[1], today)

    m = re.fullmatch(rf"({_MONTH_RE}) (?:of )?{_YEAR_RE}", text)
    if m:
        return date(int(m[2]), MONTHS[m[1]], 1)

    m = re.fullmatch(rf"the {_DAY_RE}", text)
    if m:
        return _make_date(None, today.month, m[1], today)

    return None


def _make_date(year: str | None, month: int, day: str, today: date) -> date:
    if day in ORDINAL_WORDS:
        day_num = ORDINAL_WORDS[day]
    else:
        day_num = int(re.sub(r"(st|nd|rd|th)$", "", day))
    return date(int(year) if year else today.year, month, day_num)

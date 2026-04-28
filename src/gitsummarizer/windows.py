import re
from datetime import timedelta


_WINDOW_RE = re.compile(r"^(\d+)([dwm])$", re.IGNORECASE)


def parse_window(text: str) -> timedelta:
    """Parse a report window like '1w', '7d', '1m', '30d'.

    PRD §3.2 specifies 7-day and 30-day windows; we accept both the
    human-friendly '1w' / '1m' aliases and explicit day counts.
    """
    m = _WINDOW_RE.match(text.strip())
    if not m:
        raise ValueError(f"Invalid window {text!r}; expected forms like '1w', '7d', '1m', '30d'.")
    n, unit = int(m.group(1)), m.group(2).lower()
    if n <= 0:
        raise ValueError(f"Window must be positive, got {text!r}.")
    if unit == "d":
        return timedelta(days=n)
    if unit == "w":
        return timedelta(weeks=n)
    return timedelta(days=n * 30)

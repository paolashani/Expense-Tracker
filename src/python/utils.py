from __future__ import annotations
import re
import sys
from typing import Optional, Tuple
from datetime import datetime

ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def parse_iso_date(s: str) -> Optional[str]:
    """
    Validate YYYY-MM-DD and return the normalized string if valid, else None.
    """
    s = (s or "").strip()
    if not ISO_DATE_RE.match(s):
        return None
    try:
        datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        return None
    return s

def parse_amount(s: str) -> Optional[float]:
    """
    Parse a positive float amount using dot or comma as decimal separator.
    Returns float or None if invalid.
    """
    if s is None:
        return None
    s = s.strip().replace(",", ".")
    try:
        value = float(s)
        if value <= 0:
            return None
        return round(value, 2)
    except ValueError:
        return None

def ask(prompt: str) -> str:
    """
    Read a line from stdin safely.
    """
    try:
        return input(prompt)
    except EOFError:
        print()
        sys.exit(0)

def yn(prompt: str, default: bool = True) -> bool:
    """
    Yes/No prompt. Returns True/False. Default on empty input.
    """
    suffix = " [Y/n] " if default else " [y/N] "
    while True:
        ans = ask(prompt + suffix).strip().lower()
        if ans == "":
            return default
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        print("Please answer with 'y' or 'n'.")

def fmt_money(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_row(cols, widths, sep=" | "):
    padded = []
    for i, col in enumerate(cols):
        s = str(col)
        w = widths[i] if i < len(widths) else len(s)
        padded.append(s.ljust(w))
    return sep.join(padded)

"""
File: utils.py
Author: Farros Ramzy (you@domain.com)
Description: Description
Version: 0.1
Date: 2026-04-16

Copyright (c) 2026
"""

from datetime import datetime, timezone, timedelta

WIB = timezone(timedelta(hours=7))
WITA = timezone(timedelta(hours=8))
WIT = timezone(timedelta(hours=9))


def now_iso() -> str:
    """
    Get current UTC + 7 in ISO format.

    Returns:
        str: ISO timestamp string.
    """
    return datetime.now(WIB).isoformat()

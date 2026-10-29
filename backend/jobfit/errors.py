"""Errors that are safe to show to users.

Each carries a stable `code` (the frontend translates it into the user's language)
and an English `message` (shown as a fallback, and useful in logs and API clients).
"""

from __future__ import annotations


class AppError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

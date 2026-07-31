"""Shared in-process PTM identifier authority.

Ledger sequence and hash-chain fields remain authoritative ordering.  These
IDs provide uniqueness and approximate time sorting only.
"""

from __future__ import annotations

import secrets
import threading
import time

ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_LOCK = threading.Lock()
_LAST_TIMESTAMP = -1
_LAST_RANDOM = -1


def _encode(value: int, length: int) -> str:
    chars = []
    for _ in range(length):
        chars.append(ULID_ALPHABET[value & 31])
        value >>= 5
    return "".join(reversed(chars))


def new_ulid(*, now_ms: int | None = None) -> str:
    """Return a Crockford ULID with thread-safe monotonic same-process state."""
    global _LAST_TIMESTAMP, _LAST_RANDOM
    timestamp = time.time_ns() // 1_000_000 if now_ms is None else int(now_ms)
    if timestamp < 0 or timestamp >= 1 << 48:
        raise ValueError("ULID timestamp is outside the 48-bit range")
    with _LOCK:
        if timestamp <= _LAST_TIMESTAMP:
            timestamp = _LAST_TIMESTAMP
            random_part = _LAST_RANDOM + 1
            if random_part >= 1 << 80:
                timestamp += 1
                if timestamp >= 1 << 48:
                    raise ValueError("ULID timestamp overflow")
                random_part = secrets.randbits(80)
        else:
            random_part = secrets.randbits(80)
        _LAST_TIMESTAMP, _LAST_RANDOM = timestamp, random_part
    return _encode(timestamp, 10) + _encode(random_part, 16)


def new_ptm_id(prefix: str, *, now_ms: int | None = None) -> str:
    if not prefix or any(ch not in "abcdefghijklmnopqrstuvwxyz0123456789_.-" for ch in prefix):
        raise ValueError("invalid PTM identifier prefix")
    return f"{prefix}_{new_ulid(now_ms=now_ms)}"


def is_valid_ptm_id(value: object, prefix: str | None = None) -> bool:
    if not isinstance(value, str):
        return False
    if prefix is None:
        prefix, separator, suffix = value.rpartition("_")
        return bool(prefix) and separator == "_" and len(suffix) == 26 and all(ch in "abcdefghijklmnopqrstuvwxyz0123456789_.-" for ch in prefix) and all(ch in ULID_ALPHABET for ch in suffix)
    return bool(prefix) and value.startswith(prefix + "_") and len(value) == len(prefix) + 27 and all(ch in ULID_ALPHABET for ch in value[len(prefix) + 1:])

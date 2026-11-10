"""PNG written and read with ``zlib`` and ``struct`` alone: an RGB picture, and text carried inside it.

A table's state rides in an ``iTXt`` chunk (keyword ``blackjack-table``, compressed), so every file the agent writes
is a picture, and the picture is all a later call needs to play on.
"""

from __future__ import annotations

import struct
import zlib

SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def write(width: int, height: int, rgb: bytes | bytearray, text: dict[str, str] | None = None) -> bytes:
    """An 8-bit RGB PNG of ``rgb`` (rows top to bottom, three bytes a pixel), with ``text`` as compressed ``iTXt``."""
    if len(rgb) != width * height * 3:
        raise ValueError(f"{len(rgb)} bytes is not {width}x{height} RGB")
    stride = width * 3
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # no filter
        raw += rgb[y * stride:(y + 1) * stride]
    out = [SIGNATURE, _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))]
    for keyword, value in (text or {}).items():
        out.append(_chunk(b"iTXt", keyword.encode("latin-1") + b"\x00\x01\x00\x00\x00" +
                          zlib.compress(value.encode("utf-8"), 9)))
    out.append(_chunk(b"IDAT", zlib.compress(bytes(raw), 6)))
    out.append(_chunk(b"IEND", b""))
    return b"".join(out)


def chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    """Every chunk of a PNG, its kind and data; raises ``ValueError`` when it is not one."""
    if not data.startswith(SIGNATURE):
        raise ValueError("it is not a PNG")
    found, at = [], len(SIGNATURE)
    while at + 8 <= len(data):
        length, kind = struct.unpack(">I4s", data[at:at + 8])
        body = data[at + 8:at + 8 + length]
        if len(body) != length:
            raise ValueError("it ends inside a chunk")
        found.append((kind, body))
        at += 12 + length
        if kind == b"IEND":
            break
    return found


def size(data: bytes) -> tuple[int, int]:
    """A PNG's width and height."""
    for kind, body in chunks(data):
        if kind == b"IHDR":
            return struct.unpack(">II", body[:8])
    raise ValueError("it has no IHDR")


def text(data: bytes, keyword: str) -> str | None:
    """The ``iTXt`` (or ``tEXt``) text a PNG carries under ``keyword``, or None."""
    wanted = keyword.encode("latin-1")
    for kind, body in chunks(data):
        if kind == b"iTXt":
            name, _, rest = body.partition(b"\x00")
            if name != wanted or len(rest) < 2:
                continue
            compressed, rest = rest[0], rest[2:]
            _, _, rest = rest.partition(b"\x00")  # language
            _, _, value = rest.partition(b"\x00")  # translated keyword
            return (zlib.decompress(value) if compressed else value).decode("utf-8")
        if kind == b"tEXt":
            name, _, value = body.partition(b"\x00")
            if name == wanted:
                return value.decode("latin-1")
    return None

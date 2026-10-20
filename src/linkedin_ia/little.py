"""LinkedIn's `little` commentary format: reserved characters escaped, hashtags kept."""

import re

RESERVED = set("|{}@[]()<>#\\*_~")
HASHTAG = re.compile(r"(?<!\S)#([^\W_]+)")


def _escape(text: str) -> str:
    return "".join(f"\\{c}" if c in RESERVED else c for c in text)


def commentary(body: str) -> str:
    """The post body as the Posts API expects it, so it renders exactly as written."""
    parts, last = [], 0
    for match in HASHTAG.finditer(body):
        parts.append(_escape(body[last : match.start()]))
        parts.append(f"{{hashtag|\\#|{match.group(1)}}}")
        last = match.end()
    parts.append(_escape(body[last:]))
    return "".join(parts)

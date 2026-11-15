"""Text helpers: whitespace normalisation and sentence/passage splitting."""
import re

_BULLET = re.compile(r"^\s*(?:[•●▪◦‣⁃\-\*–—·]|\d+[.)])\s+")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(])")
_STOPWORDS = frozenset(
    "a an the and or of to in on for with at by from as is are was were be been being this that these those it its "
    "we you your our their they he she i my me us them will can may should must would could have has had do does did "
    "not no yes if then than such using use used ability experience strong knowledge understanding working work "
    "years year plus including etc related relevant good excellent skills skill".split()
)


def normalize_whitespace(text: str) -> str:
    """Collapse runs of spaces/tabs, trim lines and collapse 3+ newlines into a paragraph break."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    text = re.sub(r"[ \t ​]+", " ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_passages(text: str, min_words: int = 3, max_chars: int = 500) -> list[str]:
    """Split text into line- and sentence-level passages suitable for embedding."""
    passages: list[str] = []
    for raw_line in text.split("\n"):
        line = _BULLET.sub("", raw_line).strip()
        if not line:
            continue
        for sent in _SENT_SPLIT.split(line):
            sent = sent.strip()
            if len(sent.split()) < min_words:
                continue
            while len(sent) > max_chars:  # break overly long runs on a word boundary
                cut = sent.rfind(" ", 0, max_chars)
                cut = cut if cut > 0 else max_chars
                passages.append(sent[:cut].strip())
                sent = sent[cut:].strip()
            if sent:
                passages.append(sent)
    return passages


def content_tokens(text: str) -> set[str]:
    """Lower-cased content words with a light suffix stemmer, for lexical-overlap sanity checks."""
    out = set()
    for tok in re.findall(r"[a-zA-Z][a-zA-Z0-9+#]+", text.lower()):
        if tok in _STOPWORDS:
            continue
        for suf in ("ing", "ed", "es", "s", "ly"):
            if tok.endswith(suf) and len(tok) - len(suf) >= 4:
                tok = tok[: -len(suf)]
                break
        out.add(tok)
    return out


def truncate(text: str, n: int = 260) -> str:
    text = text.strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"

"""Arabic text normalisation for search and gharib lookup."""

import re

# Harakat, Quranic annotation marks, tatweel and invisible direction marks.
_MARKS = re.compile("[ً-ٰٟـۖ-ۭ‌-‏؜]")
_ALEF = re.compile("[آأإٱ]")
_NOT_WORD = re.compile(r"[^\w\s]", re.UNICODE)
_SPACES = re.compile(r"\s+")


def normalize_arabic(text: str) -> str:
    """Strip tashkeel, tatweel and punctuation; unify alef forms; lowercase Latin."""
    text = _MARKS.sub("", text)
    text = _ALEF.sub("ا", text)
    text = _NOT_WORD.sub(" ", text).replace("_", " ")
    return _SPACES.sub(" ", text).strip().lower()


def strip_clitics(word: str) -> list[str]:
    """Candidate stems of one normalised word, most specific first.

    Peels a leading conjunction (و/ف), then a preposition (ب/ل/ك), then the
    definite article, so «فبالنيات» yields «بالنيات», «النيات», «نيات».
    """
    candidates = [word]

    def add(stem: str) -> None:
        if len(stem) >= 2 and stem not in candidates:
            candidates.append(stem)

    stems = [word]
    if word[:1] in ("و", "ف") and len(word) > 3:
        stems.append(word[1:])
    for stem in list(stems):
        add(stem)
        if stem.startswith("لل") and len(stem) > 3:
            add("ال" + stem[2:])
            add(stem[2:])
        if stem[:1] in ("ب", "ل", "ك") and len(stem) > 3:
            add(stem[1:])
            stems.append(stem[1:])
    for stem in list(candidates):
        if stem.startswith("ال") and len(stem) > 3:
            add(stem[2:])
    return candidates

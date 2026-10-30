"""Normalise scholar grades. The app never assigns a grade of its own."""

from typing import Optional

RULING_TYPES = ("sahih", "hasan", "daif", "mawdu", "other")

DEFECT_CAUSES: dict[str, tuple[str, str]] = {
    "inqita": ("Broken chain", "انقطاع في السند"),
    "kadhdhab_matruk": ("Liar or abandoned narrator", "راوٍ كذاب أو متروك"),
    "su_al_hifz": ("Weak memory or precision", "سوء الحفظ"),
    "majhul": ("Unknown narrator", "جهالة الراوي"),
    "shudhudh": ("Contradicts more reliable narrators", "الشذوذ"),
    "illah": ("Hidden defect", "العلة القادحة"),
}

_SCHOLAR_NAMES = {
    "al-albani": "al-Albani",
    "shuaib al arnaut": "Shu'ayb al-Arna'ut",
    "ahmad muhammad shakir": "Ahmad Shakir",
    "zubair ali zai": "Zubair 'Ali Za'i",
    "bashar awad maarouf": "Bashshar 'Awwad Ma'ruf",
    "muhammad muhyi al-din abdul hamid": "Muhyi al-Din 'Abd al-Hamid",
}

# A hadith's place in a Sahih is the compiler's own judgement of authenticity.
INCLUSION_GRADES = {
    "bukhari": ("al-Bukhari", "al-Jami' al-Sahih"),
    "muslim": ("Muslim ibn al-Hajjaj", "al-Musnad al-Sahih"),
}


def ruling_type(grade: str) -> str:
    """Map a free-text dataset grade onto one ruling bucket.

    Checked from most to least severe, so «Daif Jiddan» is weak and
    «Hasan Sahih» / «Sahih Lighairihi» are sahih.
    """
    g = grade.lower().replace("'", "").replace("’", "")
    if not g.strip():
        return "other"
    if "mawdu" in g or "fabricat" in g:
        return "mawdu"
    if any(k in g for k in ("daif", "weak", "munkar", "shadh", "matruk")):
        return "daif"
    if "sahih" in g:
        return "sahih"
    if "hasan" in g:
        return "hasan"
    return "other"


def display_scholar(name: str) -> str:
    return _SCHOLAR_NAMES.get(name.strip().lower(), name.strip())


def dataset_grade(scholar: str, grade: str, source_dataset: Optional[str]) -> dict:
    return {
        "scholar": display_scholar(scholar),
        "source_book": None,
        "source_dataset": source_dataset,
        "grade": grade,
        "ruling_type": ruling_type(grade),
        "basis": "scholar_grading",
    }


def inclusion_grade(collection: str) -> Optional[dict]:
    hit = INCLUSION_GRADES.get(collection)
    if hit is None:
        return None
    scholar, book = hit
    return {
        "scholar": scholar,
        "source_book": book,
        "source_dataset": None,
        "grade": "Sahih",
        "ruling_type": "sahih",
        "basis": "inclusion_in_sahih",
    }

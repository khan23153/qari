"""Preserve published spoken transcripts at the PCD tokenizer boundary.

Matching keys deliberately discard distinctions such as hamza, final alif
maqsura and short vowels. They are unsuitable targets for a model trained to
emit those distinctions. Dataset provenance and held-out audio checks remain
the caller's responsibility; this module never invents a transcript.
"""

import unicodedata


_DISPLAY_MARKS = str.maketrans(
    "", "", "\ufeff\u0640\u06DD\u06DE" + "".join(chr(c) for c in range(0x06D6, 0x06DD))
)


def prepare_pcd_transcript(text: str) -> str:
    """Clean display annotations from verified Imla'i text, keeping vowels.

    This is not an Uthmani-to-Imla'i converter. Supply an independently
    verified Imla'i transcript, retaining its Arabic letters and diacritics.
    """
    if not isinstance(text, str):
        raise ValueError("A nonempty spoken transcript is required")
    # A dagger alif drawn over final ى is redundant in the Imla'i model text.
    # Elsewhere it can carry a long vowel, so do not delete it globally.
    text = text.translate(_DISPLAY_MARKS).replace("ىٰ", "ى")
    cleaned = " ".join(unicodedata.normalize("NFC", text).split())
    if not cleaned:
        raise ValueError("A nonempty spoken transcript is required")
    return cleaned


def tokenize_pcd_transcript(row, tokenizer) -> list[int]:
    """Tokenize an explicit training label; never fall back to a matching key."""
    if "training_text" not in row:
        raise ValueError("Explicit training_text is required; matching/reference keys are not labels")
    unknown_id = getattr(tokenizer, "unk_id", None)
    if not isinstance(unknown_id, int) or unknown_id < 0:
        raise ValueError("Tokenizer must declare its unknown token ID")
    tokens = tokenizer.text_to_ids(prepare_pcd_transcript(row["training_text"]))
    if unknown_id in tokens:
        raise ValueError("A published transcript contains an unknown token")
    if not tokens:
        raise ValueError("A spoken transcript must produce tokens")
    return tokens


def pcd_transcript_variants(published_text: str) -> tuple[str, ...]:
    """Represent optional PCD vowel marks without changing a published word.

    Both forms come from the verified transcript. Model predictions are never
    a source of labels, and hamza/madda letters and final alif maqsura remain.
    """
    full = prepare_pcd_transcript(published_text)
    plain = "".join(char for char in full if not 0x064B <= ord(char) <= 0x0652)
    return (full,) if plain == full else (full, plain)


def verified_imlai_transcript_variants(
    published_text: str, clean_published_text: str,
) -> tuple[str, ...]:
    """Add an Imla'i vowel spelling backed by a separate published edition.

    Some ordinary Imla'i words, such as هذا and ذلك, print a dagger alif
    as a vowel annotation. The PCD tokenizer cannot represent that mark.
    Omission is allowed only when the clean edition independently confirms
    exactly the same letters in every word. This is not a general conversion:
    هٰرون cannot become هرون when the clean edition spells it هارون.

    Other vowels, hamza/madda, final ى and small Arabic letters stay intact.
    Neither model predictions nor matcher/reference keys provide this proof.
    Callers must separately verify the editions' provenance and verse binding.
    """
    full = prepare_pcd_transcript(published_text)
    clean = prepare_pcd_transcript(clean_published_text)
    if any(not char.isspace() and not unicodedata.category(char).startswith("L")
           for char in clean):
        raise ValueError("An independently published clean edition is required")
    full_words, clean_words = full.split(), clean.split()
    if len(full_words) != len(clean_words):
        raise ValueError("Published editions must contain the same words")
    for word, clean_word in zip(full_words, clean_words):
        letters = "".join(char for char in word
                          if unicodedata.category(char).startswith("L"))
        if letters != clean_word:
            raise ValueError("Published editions must preserve every word's letters")
    variants = pcd_transcript_variants(full)
    verified_spelling = full.replace("\u0670", "")
    return tuple(dict.fromkeys(variants + pcd_transcript_variants(verified_spelling)))

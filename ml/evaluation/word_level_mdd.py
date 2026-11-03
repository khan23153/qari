"""Word-level mistake-detection metrics from per-phoneme model scores.

The live session marks a whole word when its worst phoneme passes the
threshold, so the model has to be judged on words, not phonemes. This turns a
dump of per-phoneme probabilities (one JSON line per recording: ``id``,
``ref`` and ``ann`` = reference and realised phonemes from the human labels,
``ours`` = the phonemes the model scored, ``probs``) plus the word split of
``ours`` into word records, then reports per error kind:

- detected / missed mistakes, false accusations on correct words;
- precision, recall, false-alarm rate with Wilson 95% intervals;
- precision at a realistic error rate (QuranMB.v2 is made of deliberate errors,
  so its precision overstates what users would see);
- spread across speakers (IDs ``SSSSS_xxxxx``; the prefix groups recordings,
  18 groups like the 18 speakers of the QuranMB paper, unconfirmed).

Usage: python -m ml.evaluation.word_level_mdd probs.jsonl ref_words.json [--threshold 0.5]
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict

VOWELS = {"a", "u", "i", "A", "U", "I", "aa", "uu", "ii", "AA", "UU", "II"}


def align(a, b):
    """Levenshtein alignment: for each index of ``a`` the matched index of ``b`` or None."""
    n, k = len(a), len(b)
    D = [[0] * (k + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        D[i][0] = i
    for j in range(k + 1):
        D[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, k + 1):
            D[i][j] = min(D[i - 1][j] + 1, D[i][j - 1] + 1, D[i - 1][j - 1] + (a[i - 1] != b[j - 1]))
    out, i, j = [None] * n, n, k
    while i > 0 and j > 0:
        if D[i][j] == D[i - 1][j - 1] + (a[i - 1] != b[j - 1]):
            out[i - 1] = j - 1
            i, j = i - 1, j - 1
        elif D[i][j] == D[i - 1][j] + 1:
            i -= 1
        else:
            j -= 1
    return out


def _geminate(p):
    return len(p) == 2 and p[0] == p[1]


def error_kind(ref_phone, heard):
    """vowel (incl. sukun: a vowel dropped or added), gemination (shadda), consonant."""
    if ref_phone in VOWELS or heard in VOWELS:
        return "vowel"
    if _geminate(ref_phone) or (heard and _geminate(heard)):
        return "gemination"
    return "consonant"


def word_records(rec, word_lens):
    """One dict per word of ``ours`` with its score and true error kinds."""
    ref, ann, ours, probs = rec["ref"], rec["ann"], rec["ours"], rec["probs"]
    a_ann = align(ref, ann)
    errors = {}  # ref position -> kind
    for i, r in enumerate(ref):
        heard = ann[a_ann[i]] if a_ann[i] is not None else None
        if heard != r:
            errors[i] = error_kind(r, heard)
    to_ours = align(ref, ours)
    word_of, k = [], 0
    for w, n in enumerate(word_lens):
        word_of += [w] * n
    assert len(word_of) == len(ours) == len(probs), rec["id"]
    kinds = defaultdict(set)
    for i, kind in errors.items():
        j = to_ours[i]
        if j is None:  # our phonemizer has no counterpart: nearest mapped neighbour
            left = next((to_ours[x] for x in range(i, -1, -1) if to_ours[x] is not None), None)
            right = next((to_ours[x] for x in range(i, len(ref)) if to_ours[x] is not None), None)
            j = left if left is not None else right
        if j is not None:
            kinds[word_of[j]].add(kind)
    out, start = [], 0
    for w, n in enumerate(word_lens):
        p = probs[start:start + n]
        start += n
        out.append({"id": rec["id"], "speaker": rec["id"].split("_")[0], "word": w,
                    "max": max(p) if p else 0.0, "mean": sum(p) / len(p) if p else 0.0,
                    "kinds": sorted(kinds.get(w, ()))})
    return out


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 4), round(c + h, 4))


def metrics(words, threshold, score="max", prevalence=0.03):
    flagged = [w[score] >= threshold for w in words]
    wrong = [bool(w["kinds"]) for w in words]
    tp = sum(f and t for f, t in zip(flagged, wrong))
    fp = sum(f and not t for f, t in zip(flagged, wrong))
    fn = sum(t and not f for f, t in zip(flagged, wrong))
    tn = len(words) - tp - fp - fn
    recall, far = (tp / (tp + fn) if tp + fn else 0.0), (fp / (fp + tn) if fp + tn else 0.0)
    real = prevalence * recall / (prevalence * recall + (1 - prevalence) * far) if recall or far else 0.0
    res = {"threshold": threshold, "score": score, "words": len(words), "wrong_words": tp + fn,
           "detected": tp, "missed": fn, "false_accusations": fp,
           "precision": round(tp / (tp + fp), 4) if tp + fp else None, "precision_ci": wilson(tp, tp + fp),
           "recall": round(recall, 4), "recall_ci": wilson(tp, tp + fn),
           "false_alarm_rate": round(far, 4), "false_alarm_ci": wilson(fp, fp + tn),
           f"precision_at_{prevalence:.0%}_wrong_words": round(real, 4), "per_kind_recall": {}}
    for kind in ("vowel", "gemination", "consonant"):
        sel = [f for f, w in zip(flagged, words) if kind in w["kinds"]]
        res["per_kind_recall"][kind] = {"wrong_words": len(sel), "detected": sum(sel),
                                        "recall": round(sum(sel) / len(sel), 4) if sel else None,
                                        "ci": wilson(sum(sel), len(sel))}
    by_spk = defaultdict(lambda: Counter())
    for f, t, w in zip(flagged, wrong, words):
        by_spk[w["speaker"]][(f, t)] += 1
    spk = []
    for s, c in sorted(by_spk.items()):
        tp_, fp_, fn_ = c[(True, True)], c[(True, False)], c[(False, True)]
        spk.append({"speaker": s, "precision": round(tp_ / (tp_ + fp_), 3) if tp_ + fp_ else None,
                    "recall": round(tp_ / (tp_ + fn_), 3) if tp_ + fn_ else None})
    res["per_speaker"] = spk
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("probs")
    ap.add_argument("ref_words")
    ap.add_argument("--thresholds", default="0.3,0.5,0.7,0.9,0.95,0.98")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    ref_words = json.load(open(a.ref_words))
    words = []
    for line in open(a.probs):
        rec = json.loads(line)
        words += word_records(rec, [len(w) for w in ref_words[" ".join(rec["ref"])]["words"]])
    kinds = Counter(k for w in words for k in w["kinds"])
    report = {"recordings": len({w["id"] for w in words}), "words": len(words),
              "wrong_words": sum(bool(w["kinds"]) for w in words), "error_kinds": dict(kinds),
              "results": [metrics(words, float(t), s) for s in ("max", "mean")
                          for t in a.thresholds.split(",")]}
    text = json.dumps(report, indent=1)
    if a.out:
        open(a.out, "w").write(text)
    print(text)


if __name__ == "__main__":
    main()

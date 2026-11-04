"""Stratified, deduplicated review sample from QuranMB.v2 (labels + v3 + GOP), written as a PRIVATE key file."""
import gzip, json, random, secrets, sys
from collections import Counter, defaultdict
sys.path.insert(0, "/home/claude/qari")
from ml.evaluation.word_level_mdd import word_records
rng = random.Random(20261105)
ref_words = json.load(open("/home/claude/kjobs/wordeval/ref_words.json"))
corpus = json.load(gzip.open("/home/claude/qari/mobile/assets/quran_corpus.json.gz"))
mushaf = {(s["surah_number"], a["ayah_number"]): [w["text"] for w in a["words"] if any(c.isalpha() for c in w["text"])]
          for s in corpus["surahs"] for a in s["ayahs"]}
W = []
for line in open("/home/claude/kjobs/gop/out/qmb_gop.jsonl"):
    r = json.loads(line)
    info = ref_words[" ".join(r["ref"])]; lens = [len(w) for w in info["words"]]
    base = word_records(r, lens); k = 0
    for w, n, ph in zip(base, lens, info["words"]):
        g = [x for x in r["gop"][k:k + n] if x is not None]; k += n
        w.update(gop=max(g) if g else None, phonemes=ph, surah=info["surah"], ayah=info["ayah"],
                 mushaf_index=info["word_start"] + w["word"], n=n)
        w["text"] = mushaf[(info["surah"], info["ayah"])][w["mushaf_index"]]
        W.append(w)
W = [w for w in W if not w["uncertain"] and w["gop"] is not None and w["n"] >= 2]
def flags(w): return w["max"] >= 0.5, w["gop"] > 0
strata = {
    "err_both_detect":   (20, lambda w: w["kinds"] and all(flags(w))),
    "err_both_miss_confident": (20, lambda w: w["kinds"] and w["max"] < 0.1 and w["gop"] < -5),
    "err_both_miss_other": (15, lambda w: w["kinds"] and not any(flags(w)) and not (w["max"] < 0.1 and w["gop"] < -5)),
    "err_v3_only":       (12, lambda w: w["kinds"] and flags(w) == (True, False)),
    "err_gop_only":      (13, lambda w: w["kinds"] and flags(w) == (False, True)),
    "ok_flagged":        (25, lambda w: not w["kinds"] and any(flags(w))),
    "ok_both_confident": (25, lambda w: not w["kinds"] and w["max"] < 0.1 and w["gop"] < -5),
    "random":            (10, lambda w: True),
}
used_rec, per_group, picked = set(), Counter(), []
KIND_ORDER = ["gemination", "vowel", "consonant"]
for name, (n, cond) in strata.items():
    pool = [w for w in W if cond(w) and w["id"] not in used_rec]
    rng.shuffle(pool)
    if name.startswith("err"):  # balance error kinds: gemination first (rare), then alternate
        by = defaultdict(list)
        for w in pool: by[w["kinds"][0] if len(w["kinds"]) == 1 else "mixed"].append(w)
        pool = []
        while any(by.values()):
            for kk in KIND_ORDER + ["mixed"]:
                if by[kk]: pool.append(by[kk].pop())
    got = 0
    for w in pool:
        if got >= n: break
        if w["id"] in used_rec or per_group[w["speaker"]] >= 9: continue
        used_rec.add(w["id"]); per_group[w["speaker"]] += 1; got += 1
        picked.append({"stratum": name, **w})
    print(f"{name:26s} {got}/{n} (pool {len(pool)})")
for p in picked: p["clip_id"] = secrets.token_hex(5)
print("total", len(picked), "groups", dict(sorted(per_group.items())))
print("error kinds in sample", Counter(k for p in picked for k in p["kinds"]))
json.dump(picked, open("key_qmb.json", "w"), ensure_ascii=False, indent=0)
json.dump([{"clip_id": p["clip_id"], "id": p["id"], "word": p["word"], "ours_words": ref_words[" ".join(json.loads(next(l for l in open("/home/claude/kjobs/gop/out/qmb_gop.jsonl") if json.loads(l)["id"] == p["id"]))["ref"])]["words"]} for p in picked],
          open("cut_list_qmb.json", "w"))

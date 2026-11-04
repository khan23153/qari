import gzip, hashlib, json, os, random, secrets, shutil, subprocess
rng = random.Random(77)
K = "kout"; OUT = "page/clips"; os.makedirs(OUT, exist_ok=True)
man = json.load(open(f"{K}/manifest.json"))
key_qmb = {k["clip_id"]: k for k in json.load(open("key_qmb.json"))}
tlog = {k["clip_id"]: k for k in json.load(open(f"{K}/tlog_scores_PRIVATE.json"))}
corpus = json.load(gzip.open("/home/claude/qari/mobile/assets/quran_corpus.json.gz"))
mushaf = {(s["surah_number"], a["ayah_number"]): [w["text"] for w in a["words"] if any(c.isalpha() for c in w["text"])]
          for s in corpus["surahs"] for a in s["ayahs"]}
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
def recut(m, cid):
    a, b = m["word_span_s"]; dur = b - a; pad = max(0.2, (0.9 - dur) / 2)
    src = f"{K}/clips/{m['context_clip']}"
    dst = f"{OUT}/{cid}_w.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{max(0, a - pad):.3f}", "-t", f"{dur + 2 * pad:.3f}", "-i", src,
                    "-ac", "1", "-b:a", "48k", dst], check=True)
    shutil.copy(src, f"{OUT}/{cid}_c.mp3")
page, key = [], []
for m in man:
    cid = m["clip_id"]
    if m["source"] == "QuranMB.v2":
        k = key_qmb[cid]; s, a, n = k["surah"], k["ayah"], k["mushaf_index"]
        info = {"stratum": k["stratum"], "dataset_wrong": bool(k["kinds"]), "dataset_kinds": k["kinds"], "v3_word_max": k["max"],
                "gop_word_max": k["gop"], "dataset_uncertain": k["uncertain"], "group": k["speaker"]}
    else:
        t = tlog[cid]; s, a, n = m["surah"], m["ayah"], m["word_index"]
        info = {"stratum": t["stratum"], "dataset_wrong": None, "dataset_kinds": None, "v3_word_max": t["v3_max"], "gop_word_max": t["gop_max"]}
    ref = mushaf[(s, a)][n]
    recut(m, cid)
    page.append({"c": cid, "w": f"{cid}_w.mp3", "x": f"{cid}_c.mp3", "wh": sha(f"{OUT}/{cid}_w.mp3"), "xh": sha(f"{OUT}/{cid}_c.mp3"),
                 "ref": ref, "s": s, "a": a, "n": n + 1})
    key.append({"clip_id": cid, "duplicate_of": None, "source": m["source"], "source_id": m["source_id"],
                "source_audio_sha256": m["source_audio_sha256"], "word_span_s": m["word_span_s"], "surah": s, "ayah": a,
                "word_number": n + 1, "reference": ref, **info})
# hidden repeats for within-reviewer consistency: 12 clips, new ids, identical audio
for src in rng.sample([p for p in page if p["c"] in key_qmb], 12):
    cid = secrets.token_hex(5)
    shutil.copy(f"{OUT}/{src['w']}", f"{OUT}/{cid}_w.mp3"); shutil.copy(f"{OUT}/{src['x']}", f"{OUT}/{cid}_c.mp3")
    page.append({**src, "c": cid, "w": f"{cid}_w.mp3", "x": f"{cid}_c.mp3"})
    base = next(k for k in key if k["clip_id"] == src["c"])
    key.append({**base, "clip_id": cid, "duplicate_of": src["c"]})
rng.shuffle(page)
json.dump({"version": "review-v1", "clips": page}, open("page/clips.json", "w"), ensure_ascii=False)
json.dump({"version": "review-v1", "note": "PRIVATE: never publish. Strata, model scores and dataset labels per clip.",
           "clips": key}, open("/home/claude/kjobs/review_key_PRIVATE.json", "w"), ensure_ascii=False, indent=1)
print(len(page), "page clips;", len(os.listdir(OUT)), "files")

"""Load time, memory and CPU latency of the pronunciation verifier.

Usage: python scripts/bench_pronunciation_verifier.py /path/to/safha-mdd-v3
Synthetic audio: measures cost only, says nothing about accuracy.
"""
import json, os, resource, sys, time, threading
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
import numpy as np, torch
from ml.inference.pronunciation_verifier import PronunciationVerifier
from ml.alignment.quran_g2p import ayah_word_phonemes

def rss_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
out = {"threads": torch.get_num_threads(), "cpus": os.cpu_count()}
out["rss_before_mb"] = rss_mb()
t = time.time(); v = PronunciationVerifier(sys.argv[1], threshold=0.5).load()
out["load_s"] = round(time.time() - t, 1); out["rss_after_load_mb"] = round(rss_mb())
ph = [p for w in ayah_word_phonemes(2, 255) for p in w]
rng = np.random.default_rng(0)
res = {}
for sec in (5, 10, 15):
    audio = (rng.standard_normal(16000 * sec) * 0.05).astype(np.float32)
    n = int(len(ph) * sec / 15)
    v.score(audio, ph[:n])  # warm
    ts = []
    for _ in range(3):
        t = time.time(); v.score(audio, ph[:n]); ts.append(time.time() - t)
    res[f"{sec}s"] = {"median_s": round(sorted(ts)[1], 2), "rtf": round(sorted(ts)[1] / sec, 2)}
out["single"] = res
out["rss_peak_single_mb"] = round(rss_mb())
# two sessions finalizing at once
audio = (rng.standard_normal(16000 * 10) * 0.05).astype(np.float32)
times = []
def job():
    t = time.time(); v.score(audio, ph[:len(ph) * 2 // 3]); times.append(time.time() - t)
ths = [threading.Thread(target=job) for _ in range(2)]
t = time.time(); [x.start() for x in ths]; [x.join() for x in ths]
out["two_concurrent_10s"] = {"wall_s": round(time.time() - t, 2), "each_s": [round(x, 2) for x in times]}
out["rss_peak_mb"] = round(rss_mb())
print(json.dumps(out, indent=1))

"""Experiment script (2026-11-05): v3 vs v3+GOP fusion on QuranMB.v2 with group- and verse-disjoint splits.

Reads the Kaggle dump kjobs/gop/out/qmb_gop.jsonl (per-phoneme v3 probabilities and GOP) and
kjobs/wordeval/ref_words.json; paths are those of the run that produced
docs/mdd-v3-baseline-and-copying-test-20261104.md. Not part of the app.
"""
"""Rigorous look at v3 vs v3+GOP fusion on QuranMB.v2 (word level)."""
import json, sys, random
sys.path.insert(0, "/home/claude/qari")
import numpy as np
from sklearn.linear_model import LogisticRegression
from ml.evaluation.word_level_mdd import align, word_records, wilson, VOWELS
ref_words = json.load(open("/home/claude/kjobs/wordeval/ref_words.json"))
recs = [json.loads(l) for l in open("out/qmb_gop.jsonl")]
def pk(p): return 0 if p in VOWELS else 1 if (len(p) == 2 and p[0] == p[1]) else 2
def feats(p, g, ph):
    lg = np.log(max(p, 1e-5) / max(1 - p, 1e-5)); g = -30.0 if g is None else max(-30.0, min(30.0, g)); k = np.eye(3)[pk(ph)]
    return np.r_[lg, g, k, k * g, k * lg]
def phone_labels(r):
    a = align(r["ref"], r["ann"]); to = align(r["ref"], r["ours"]); lab = [0] * len(r["ours"])
    for i, p in enumerate(r["ref"]):
        if (r["ann"][a[i]] if a[i] is not None else None) != p and to[i] is not None: lab[to[i]] = 1
    return lab
verse = {ref: k for k, ref in enumerate(sorted(ref_words))}
for r in recs:
    r["group"] = int(r["id"].split("_")[0]); r["verse"] = verse[" ".join(r["ref"])]; r["plab"] = phone_labels(r)

def fit(train):
    X = [feats(p, g, ph) for r in train for p, g, ph in zip(r["probs"], r["gop"], r["ours"])]
    y = [l for r in train for l in r["plab"]]
    return LogisticRegression(max_iter=2000).fit(np.array(X), np.array(y))
def words_of(rs, lr):
    W = []
    for r in rs:
        lens = [len(w) for w in ref_words[" ".join(r["ref"])]["words"]]
        f = lr.predict_proba(np.array([feats(p, g, ph) for p, g, ph in zip(r["probs"], r["gop"], r["ours"])]))[:, 1]
        base = word_records(r, lens); k = 0
        for w, n in zip(base, lens):
            w["fused"] = float(f[k:k + n].max()); w["group"] = r["group"]; w["verse"] = r["verse"]; k += n
        W += base
    return W
def thr_for(W, key, target=0.90):
    s = np.array([w[key] for w in W]); y = np.array([bool(w["kinds"]) for w in W])
    for c in np.unique(np.round(s, 5)):
        f = s >= c
        if f.sum() and (f & y).sum() / f.sum() >= target: return c
def run(split_name, train_mask, test_mask):
    tr = [r for r in recs if train_mask(r)]; te = [r for r in recs if test_mask(r)]
    lr = fit(tr); Wd = words_of(tr, lr); Wt = words_of(te, lr)
    t_v3, t_f = thr_for(Wd, "max"), thr_for(Wd, "fused")
    y = np.array([bool(w["kinds"]) for w in Wt])
    a = np.array([w["max"] >= t_v3 for w in Wt]); b = np.array([w["fused"] >= t_f for w in Wt])
    print(f"\n== {split_name}: train {len(tr)} recs, test {len(te)} recs, {len(Wt)} words ({y.sum()} wrong); dev thresholds v3 {t_v3:.4f}, fused {t_f:.4f}")
    for name, f in (("v3", a), ("v3+GOP", b)):
        tp, fp, fn, tn = (f & y).sum(), (f & ~y).sum(), (~f & y).sum(), (~f & ~y).sum()
        print(f"  {name:7s} P {tp/(tp+fp):.3f} {wilson(int(tp),int(tp+fp))}  R {tp/(tp+fn):.3f} {wilson(int(tp),int(tp+fn))}  false accusations {fp} / {fp+tn} correct words ({fp/(fp+tn):.4f})")
        for kind in ("vowel", "consonant", "gemination"):
            m = np.array([kind in w["kinds"] for w in Wt])
            print(f"      {kind:10s} {int((f&m).sum())}/{int(m.sum())} = {(f&m).sum()/max(1,m.sum()):.3f} {wilson(int((f&m).sum()), int(m.sum()))}")
    print(f"  wrong words: both catch {int((a&b&y).sum())}, only v3 {int((a&~b&y).sum())}, only fused {int((~a&b&y).sum())}, both miss {int((~a&~b&y).sum())}")
    print(f"  correct words: both accuse {int((a&b&~y).sum())}, only v3 {int((a&~b&~y).sum())}, only fused {int((~a&b&~y).sum())}")
    # paired bootstrap over recording groups of the recall difference
    groups = sorted({w["group"] for w in Wt}); G = np.array([w["group"] for w in Wt]); rng = np.random.default_rng(0); diffs, pd = [], []
    for _ in range(2000):
        pick = rng.choice(groups, len(groups)); m = np.concatenate([np.where(G == g)[0] for g in pick])
        yy, aa, bb = y[m], a[m], b[m]
        diffs.append((bb & yy).sum() / yy.sum() - (aa & yy).sum() / yy.sum())
        pd.append((bb & yy).sum() / max(1, bb.sum()) - (aa & yy).sum() / max(1, aa.sum()))
    print(f"  recall gain {np.mean(diffs):+.3f}  group-bootstrap 95% [{np.percentile(diffs,2.5):+.3f}, {np.percentile(diffs,97.5):+.3f}]; precision change {np.mean(pd):+.3f} [{np.percentile(pd,2.5):+.3f}, {np.percentile(pd,97.5):+.3f}]")
    return Wt, lr, t_v3, t_f
run("groups 0-8 -> 9-17 (verses shared)", lambda r: r["group"] <= 8, lambda r: r["group"] >= 9)
vs = sorted(set(r["verse"] for r in recs)); random.Random(0).shuffle(vs); A = set(vs[: len(vs) // 2])
run("groups 0-8 & verses A -> groups 9-17 & verses B (both unseen)", lambda r: r["group"] <= 8 and r["verse"] in A,
    lambda r: r["group"] >= 9 and r["verse"] not in A)
# independence of the two raw signals on true error PHONEMES (no fusion)
pos = [(p, g) for r in recs for p, g, l in zip(r["probs"], r["gop"], r["plab"]) if l and g is not None]
p = np.array([x[0] for x in pos]); g = np.array([x[1] for x in pos])
from scipy.stats import spearmanr
print(f"\nerror phonemes n={len(pos)}: Spearman(v3 prob, GOP) = {spearmanr(p, g).correlation:.3f}; "
      f"v3>=0.5 {np.mean(p>=.5):.3f}, GOP>0 {np.mean(g>0):.3f}, both {np.mean((p>=.5)&(g>0)):.3f}, either {np.mean((p>=.5)|(g>0)):.3f}, neither {np.mean((p<.5)&(g<=0)):.3f}")
print(f"  if independent, both would be {np.mean(p>=.5)*np.mean(g>0):.3f}")

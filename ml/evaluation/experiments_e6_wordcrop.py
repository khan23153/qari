"""Experiment script (2026-11-05): E6 word-cropped GOP + vowel duel + shadda duration vs full-ayah GOP and E5.
Reads Kaggle dumps (kjobs/e6/out/e6_slots.jsonl, kjobs/gop/out/qmb_gop.jsonl). Not part of the app.
"""
"""E6 vs full-ayah GOP vs E5 on QuranMB.v2, group split (0-8 fit, 9-17 test) and group+verse split."""
import json, sys, random
sys.path.insert(0, "/home/claude/qari")
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from ml.evaluation.word_level_mdd import align, word_records, wilson, VOWELS
E6F = sys.argv[1]
ref_words = json.load(open("/home/claude/kjobs/wordeval/ref_words.json"))
full = {json.loads(l)["id"]: json.loads(l) for l in open("/home/claude/kjobs/gop/out/qmb_gop.jsonl")}
e6 = {json.loads(l)["id"]: json.loads(l) for l in open(E6F)}
verse = {r: k for k, r in enumerate(sorted(ref_words))}
def pk(p): return 0 if p in VOWELS else 1 if (len(p) == 2 and p[0] == p[1]) else 2
def clip(x, lo=-30, hi=30): return max(lo, min(hi, x))
def feats(p, g, slot, ph, use):
    k = np.eye(3)[pk(ph)]; f = []
    if "v3" in use:
        lg = np.log(max(p, 1e-5) / max(1 - p, 1e-5)); f += [lg, *(k * lg)]
    if "gop" in use:
        gg = -30.0 if g is None else clip(g); f += [gg, *(k * gg)]
    if "e6" in use:
        s = slot or {}
        cg = s.get("crop_gop"); ds = s.get("duel_seq"); df = s.get("duel_frame"); du = s.get("dur")
        f += [-30.0 if cg is None else clip(cg), cg is None,
              (clip(ds) if ds is not None else -30.0) * (pk(ph) == 0), (clip(df) if df is not None else -30.0) * (pk(ph) == 0),
              (min(du, 5.0) if du is not None else 0.0) * (pk(ph) == 1), (min(du, 5.0) if du is not None else 0.0) * (pk(ph) == 2)]
        f += list(k * (-30.0 if cg is None else clip(cg)))
    return np.array(f + list(k), dtype=float)
recs = []
for rid, r in full.items():
    if rid not in e6: continue
    words = ref_words[" ".join(r["ref"])]["words"]; slots = []
    for w, ws in zip(words, e6[rid]["words"]):
        slots += (ws if ws else [None] * len(w))
    a = align(r["ref"], r["ann"]); to = align(r["ref"], r["ours"]); lab = [0] * len(r["ours"])
    for i, p in enumerate(r["ref"]):
        if (r["ann"][a[i]] if a[i] is not None else None) != p and to[i] is not None: lab[to[i]] = 1
    recs.append({**r, "slots": slots, "plab": lab, "group": int(rid.split("_")[0]), "verse": verse[" ".join(r["ref"])]})
print("recordings", len(recs))
VARIANTS = {"full GOP": ["gop"], "E5 v3+GOP": ["v3", "gop"], "E6 alone": ["e6"], "v3+E6": ["v3", "e6"], "v3+GOP+E6": ["v3", "gop", "e6"]}
def X(rs, use): return np.array([feats(p, g, s, ph, use) for r in rs for p, g, s, ph in zip(r["probs"], r["gop"], r["slots"], r["ours"])])
def words_scores(rs, lr, use, key):
    W = []
    for r in rs:
        lens = [len(w) for w in ref_words[" ".join(r["ref"])]["words"]]
        f = lr.predict_proba(np.array([feats(p, g, s, ph, use) for p, g, s, ph in zip(r["probs"], r["gop"], r["slots"], r["ours"])]))[:, 1]
        base = word_records(r, lens); k = 0
        for w, n in zip(base, lens): w[key] = float(f[k:k + n].max()); w["group"] = r["group"]; k += n
        W.append(base)
    return W
def thr_for(s, y, target=0.90):
    for c in np.unique(np.round(s, 5)):
        f = s >= c
        if f.sum() and (f & y).sum() / f.sum() >= target: return c
def run(name, trm, tem):
    tr = [r for r in recs if trm(r)]; te = [r for r in recs if tem(r)]
    res, flags = {}, {}
    ytr = yte = G = None
    for vn, use in VARIANTS.items():
        lr = LogisticRegression(max_iter=3000).fit(X(tr, use), np.array([l for r in tr for l in r["plab"]]))
        Wd = [w for ws in words_scores(tr, lr, use, "s") for w in ws]; Wt = [w for ws in words_scores(te, lr, use, "s") for w in ws]
        sd = np.array([w["s"] for w in Wd]); yd = np.array([bool(w["kinds"]) for w in Wd])
        st = np.array([w["s"] for w in Wt]); yte = np.array([bool(w["kinds"]) for w in Wt]); G = np.array([w["group"] for w in Wt])
        kinds = {k: np.array([k in w["kinds"] for w in Wt]) for k in ("vowel", "consonant", "gemination")}
        t = thr_for(sd, yd); f = st >= t; flags[vn] = f
        tp, fp, fn, tn = (f & yte).sum(), (f & ~yte).sum(), (~f & yte).sum(), (~f & ~yte).sum()
        o = np.argsort(-st); tt = yte[o]; cp = np.cumsum(tt); cf = np.cumsum(~tt); P = cp / (cp + cf); R = cp / tt.sum()
        r95 = R[np.where(P >= .95)[0].max()] if (P >= .95).any() else 0.0
        res[vn] = (roc_auc_score(yte, st), tp / (tp + fp), wilson(int(tp), int(tp + fp)), tp / (tp + fn), wilson(int(tp), int(tp + fn)), fp, tn + fp, r95,
                   {k: (f & m).sum() / max(1, m.sum()) for k, m in kinds.items()}, {k: int(m.sum()) for k, m in kinds.items()})
    print(f"\n== {name}: test words {len(yte)} ({yte.sum()} wrong); thresholds chosen on fit half at precision >= 0.90")
    for vn, (auc, P, Pc, R, Rc, fp, nc, r95, kr, kn) in res.items():
        print(f"  {vn:11s} AUC {auc:.3f}  P {P:.3f} {Pc}  R {R:.3f} {Rc}  false acc {fp}/{nc}  R@P.95(test curve) {r95:.3f}  | vowel {kr['vowel']:.3f} cons {kr['consonant']:.3f} gem {kr['gemination']:.3f} (n {kn['gemination']})")
    rng = np.random.default_rng(0); groups = sorted(set(G))
    for vn in ("E6 alone", "v3+E6", "v3+GOP+E6"):
        d = []
        for _ in range(2000):
            pick = rng.choice(groups, len(groups)); m = np.concatenate([np.where(G == g)[0] for g in pick]); y = yte[m]
            d.append(((flags[vn][m] & y).sum() - (flags["E5 v3+GOP"][m] & y).sum()) / y.sum())
        print(f"  recall change {vn} vs E5: {np.mean(d):+.3f} [{np.percentile(d,2.5):+.3f}, {np.percentile(d,97.5):+.3f}]")
run("groups 0-8 -> 9-17", lambda r: r["group"] <= 8, lambda r: r["group"] >= 9)
vs = sorted({r["verse"] for r in recs}); random.Random(0).shuffle(vs); A = set(vs[:len(vs) // 2])
run("groups 0-8 & verses A -> groups 9-17 & verses B", lambda r: r["group"] <= 8 and r["verse"] in A, lambda r: r["group"] >= 9 and r["verse"] not in A)
# canonicalization test on error slots missed by both (v3 < 0.5, full GOP < -5): does word-cropping flip them?
miss = [(r["probs"][i], r["gop"][i], (r["slots"][i] or {}), r["ours"][i]) for r in recs for i, l in enumerate(r["plab"])
        if l and r["gop"][i] is not None and r["probs"][i] < 0.5 and r["gop"][i] < -5]
cg = [s.get("crop_gop") for _, _, s, _ in miss if s.get("crop_gop") is not None]
ok_neg = [s.get("crop_gop") for r in recs for i, (l, s) in enumerate(zip(r["plab"], r["slots"])) if not l and s and s.get("crop_gop") is not None]
print(f"\nerror slots missed by both with full-ayah GOP < -5: n={len(miss)}; cropped GOP > 0 on {np.mean(np.array(cg) > 0):.3f} of them "
      f"(cropped GOP > 0 on correct slots: {np.mean(np.array(ok_neg) > 0):.3f}); median cropped GOP {np.median(cg):.2f}")
vm = [(s.get("duel_seq"), s.get("duel_frame")) for _, _, s, ph in miss if ph in VOWELS and s.get("duel_seq") is not None]
if vm: print(f"  vowel slots among them n={len(vm)}: duel_seq > 0 on {np.mean([a > 0 for a, _ in vm]):.3f}, duel_frame > 0 on {np.mean([b is not None and b > 0 for _, b in vm]):.3f}")

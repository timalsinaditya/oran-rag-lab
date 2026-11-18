"""Analyses for the report (CPU only, reads saved runs). Usage: python bench/analysis.py"""
import json, os, re
from collections import Counter
B = os.path.dirname(os.path.abspath(__file__))
rd = lambda p: {json.loads(l)["qid"]: json.loads(l) for l in open(f"{B}/{p}") if l.strip()}
norm = lambda s: " ".join(re.findall(r"[a-z0-9]+", s.lower()))

def fix_break(set_, base, rag):
    b, r = rd(f"runs/{set_}__{base}.jsonl"), rd(f"runs/{set_}__{rag}.jsonl")
    q = [x for x in r if x in b]
    fx = sum(r[x]["correct"] and not b[x]["correct"] for x in q); br = sum(b[x]["correct"] and not r[x]["correct"] for x in q)
    return fx, br

def quartiles(set_, base, rag, ctx):
    b, r = rd(f"runs/{set_}__{base}.jsonl"), rd(f"runs/{set_}__{rag}.jsonl")
    c = {k: v["ctx"][0]["score"] for k, v in rd(f"ctx/{set_}__{ctx}.jsonl").items()}
    qs = sorted(r, key=lambda x: c[x]); n = len(qs); out = []
    for i in range(4):
        g = qs[i*n//4:(i+1)*n//4]
        out.append((c[g[0]], c[g[-1]], sum(b[x]["correct"] for x in g)/len(g), sum(r[x]["correct"] for x in g)/len(g)))
    return out

print("== official ORANBench: 7B base vs 7B + RAG (166 specs)")
print("fixed, broke:", fix_break("oranbench", "q7b_base", "q7b_ragfull"))
for lo, hi, ab, ar in quartiles("oranbench", "q7b_base", "q7b_ragfull", "idxfull"):
    print(f"  top score {lo:.2f}-{hi:.2f}: base {ab:.3f}  rag {ar:.3f}  ({ar-ab:+.3f})")
print("== sample_500, 29 docs:")
print("fixed, broke:", fix_break("sample_500", "q7b_base", "q7b_rag29"))
for lo, hi, ab, ar in quartiles("sample_500", "q7b_base", "q7b_rag29", "idx29"):
    print(f"  top score {lo:.2f}-{hi:.2f}: base {ab:.3f}  rag {ar:.3f}  ({ar-ab:+.3f})")

r = rd("runs/oranbench__q7b_ragfull.jsonl")
print("== position bias (official, RAG): pred", sorted(Counter(x["pred"] for x in r.values()).items()),
      " gold", sorted(Counter(x["answer"] for x in r.values()).items()))

# error analysis of wrong RAG answers: is the correct option's text present in the 5 passages given to the model?
sets = {json.loads(l)["qid"]: json.loads(l) for l in open(f"{B}/sets/oranbench.jsonl")}
ctx = rd("ctx/oranbench__idxfull.jsonl")
cat = Counter()
for qid, x in r.items():
    if x["correct"]:
        continue
    q = sets[qid]; text = norm(" ".join(c["text"] for c in ctx[qid]["ctx"][:5]))
    gold = norm(q["options"][q["answer"] - 1]); wrong = norm(q["options"][x["pred"] - 1])
    g_in, w_in = gold in text, wrong in text
    key = ("gold option text in passages" if g_in and not w_in else "both options' text in passages" if g_in and w_in
           else "only the picked (wrong) option in passages" if w_in else "neither option's text in passages")
    cat[(x["level"], key)] += 1
print("== wrong RAG answers on official set, by evidence in the passages (exact-text proxy)")
for lv in ("easy", "medium", "hard"):
    tot = sum(v for (l, _), v in cat.items() if l == lv)
    print(f"  {lv} ({tot} wrong):", {k: v for (l, k), v in cat.items() if l == lv})
tune = {"q7b_ragfull": "v1 800-tok", "q7b_v2_k5": "v2", "q7b_v2h_k5": "v2+hybrid", "q7b_v2h_k8": "v2+hybrid k8"}
print("== fixed/broke vs base on tune_200 (base from sample_500):")
b = rd("runs/sample_500__q7b_base.jsonl")
for t, n in tune.items():
    rr = rd(f"runs/tune_200__{t}.jsonl")
    print(f"  {n}: fixed {sum(rr[q]['correct'] and not b[q]['correct'] for q in rr)}, broke {sum(b[q]['correct'] and not rr[q]['correct'] for q in rr)}")

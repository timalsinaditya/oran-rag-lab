"""Build site/assets/oranbench.json: 1,500 official ORANBench questions with base and RAG predictions
and the top-5 retrieved sources (names/locations only, no spec text)."""
import json, math, re, pathlib
R = pathlib.Path(__file__).resolve().parent.parent
rd = lambda p: [json.loads(l) for l in open(R / p)]
qs = {q["qid"]: q for q in rd("bench/sets/oranbench.jsonl")}
base = {r["qid"]: r for r in rd("bench/runs/oranbench__q7b_base.jsonl")}
rag = {r["qid"]: r for r in rd("bench/runs/oranbench__q7b_ragfull.jsonl")}
ctx = {c["qid"]: c["ctx"][:5] for c in rd("bench/ctx/oranbench__idxfull.jsonl")}
def probs(s):
    m = max(s); e = [math.exp(x - m) for x in s]; t = sum(e); return [round(x / t, 3) for x in e]
out = []
for qid, q in qs.items():
    b, r = base[qid], rag[qid]
    out.append({"id": qid, "lv": q["level"][0], "q": q["question"], "o": q["options"], "a": q["answer"],
                "bp": b["pred"], "rp": r["pred"], "bpr": probs(b["scores"]) if "scores" in b else None, "rpr": probs(r["scores"]) if "scores" in r else None,
                "src": [[re.sub(r"\.(pdf|docx)$", "", c["source"]), c["loc"], round(c["score"], 3)] for c in ctx[qid]]})
json.dump(out, open(R / "site/assets/oranbench.json", "w"), separators=(",", ":"))
acc = lambda k: sum(x[k] == x["a"] for x in out) / len(out)
print(len(out), "questions; base", round(acc("bp"), 3), "rag", round(acc("rp"), 3))

# ---- specification list: id -> file name from the download log, grouped by working group (links only)
specs = []
for line in open(R / "catalog/download_full.log"):
    m = re.match(r"id=(\d+) -> (.+)", line.strip())
    if not m: continue
    name = re.sub(r"\s+\.", ".", m.group(2).strip()); zipped = name.startswith("unzipped ")
    name = name.removeprefix("unzipped ")
    stem = re.sub(r"\.(pdf|docx|zip)$", "", name, flags=re.I)
    g = re.search(r"(WG\d+|SFG|SuFG|TIFG|TSC|nGRG|OSFG)", stem)
    wg = g.group(1).upper() if g else "OTHER"
    v = re.search(r"v\d+\.\d+(\.\d+)?", stem)
    specs.append({"id": int(m.group(1)), "name": stem, "wg": wg, "ver": v.group(0) if v else "",
                  "fmt": "zip" if zipped else name.rsplit(".", 1)[-1].lower()})
json.dump(specs, open(R / "site/assets/specs.json", "w"), separators=(",", ":"))
from collections import Counter
print(len(specs), "spec links;", Counter(s["wg"] for s in specs).most_common())

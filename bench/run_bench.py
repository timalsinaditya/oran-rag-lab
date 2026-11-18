"""ORAN-Bench-13K evaluation harness (multiple choice).

Two stages, so the retriever and a large generator never share the 24 GB GPU:
  python bench/run_bench.py sample   --n 500 --seed 42                 # fixed eval set: 500/level (ORANSight-2.0 protocol)
  python bench/run_bench.py retrieve --set sample_500 --index index --tag idx29 -k 5
  python bench/run_bench.py answer   --set sample_500 --ctx idx29 --model Qwen/Qwen2.5-7B-Instruct --tag q7b_rag29
  python bench/run_bench.py answer   --set sample_500 --model Qwen/Qwen2.5-7B-Instruct --tag q7b_base   # no --ctx = no RAG
  python bench/run_bench.py score                                       # table of every run

Answering uses logit scoring: one forward pass, then pick the option number ("1".."N") with the highest
next-token probability. Deterministic, no free-text parsing, ~10x faster than generation.
Leakage guard: the ORAN-Bench-13K and ORANSight papers are excluded from retrieval.
"""
import argparse, json, os, random, re, glob, time

BENCH = os.path.dirname(os.path.abspath(__file__))
DATA, SETS, CTX, RUNS = (f"{BENCH}/{d}" for d in ("data", "sets", "ctx", "runs"))
LEVELS = {"E": "easy", "M": "medium", "H": "hard"}
EXCLUDE = ("ORAN-Bench-13K", "ORANSight")     # papers about the benchmark itself -> never retrieved

SYS_BASE = ("You are an expert in O-RAN (Open Radio Access Network) specifications. "
            "Answer the multiple-choice question with the number of the correct option only.")
SYS_RAG = ("You are an expert in O-RAN (Open Radio Access Network) specifications. Use the context passages "
           "from the O-RAN specifications to answer the multiple-choice question. If the context is not "
           "sufficient, use your own knowledge. Answer with the number of the correct option only.")


def load_level(lv):
    return [json.loads(l) for l in open(f"{DATA}/fin_{lv}.json") if l.strip()]


def clean_opt(o):
    return re.sub(r"^\s*\d+\.\s*", "", o).strip()


def jl_write(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def jl_read(path):
    # tolerant of a crash mid-write (power loss leaves NUL padding / a truncated last line): skip bad lines
    out = []
    for l in open(path, errors="replace"):
        l = l.replace("\0", "").strip()
        if l:
            try: out.append(json.loads(l))
            except json.JSONDecodeError: pass
    return out


# ------------------------------------------------------------------ build eval sets
def cmd_sample(a):
    rng, rows = random.Random(a.seed), []
    for lv in LEVELS:
        items = load_level(lv)
        idx = sorted(range(len(items))) if a.n == 0 else sorted(rng.sample(range(len(items)), a.n))
        for i in idx:
            q, opts, ans = items[i]
            rows.append({"qid": f"{lv}{i}", "level": LEVELS[lv], "question": q.strip(),
                         "options": [clean_opt(o) for o in opts], "answer": int(str(ans).strip())})
    name = "full" if a.n == 0 else f"sample_{a.n}"
    jl_write(f"{SETS}/{name}.jsonl", rows)
    print(f"{SETS}/{name}.jsonl: {len(rows)} questions")


# ------------------------------------------------------------------ stage 1: retrieval
def cmd_retrieve(a):
    import sys; sys.path.insert(0, os.path.dirname(BENCH))
    os.chdir(os.path.dirname(BENCH))
    from rag import RAG
    rows, t0 = jl_read(f"{SETS}/{a.set}.jsonl"), time.time()
    final = f"{CTX}/{a.set}__{a.tag}.jsonl"
    if os.path.exists(final) and {c["qid"] for c in jl_read(final)} >= {r["qid"] for r in rows}:
        print(f"already complete: {final} (skipping)", flush=True)
        return
    # reuse: contexts already retrieved with the same index/settings for another set (e.g. sample_500 -> full)
    known = {c["qid"]: c for f in (a.reuse or []) for c in jl_read(f"{CTX}/{f}.jsonl")}
    partial = f"{CTX}/{a.set}__{a.tag}.partial.jsonl"
    if os.path.exists(partial):                 # resume after a crash / reboot
        known.update({c["qid"]: c for c in jl_read(partial)})
    out = [known[r["qid"]] for r in rows if r["qid"] in known]
    rows = [r for r in rows if r["qid"] not in known]
    if known:
        print(f"reused {len(out)} contexts, retrieving {len(rows)}", flush=True)
    rag = RAG(load_llm=False, index_dir=a.index)
    for n, r in enumerate(rows, 1):
        query = r["question"] if a.query == "q" else r["question"] + " " + " ".join(r["options"])
        hits = rag.retrieve(query, a.k, exclude=EXCLUDE, hybrid=a.hybrid)
        out.append({"qid": r["qid"], "ctx": [{"source": h["source"], "loc": h["loc"], "score": h["score"],
                                              "text": h["text"]} for h in hits]})
        if n % 100 == 0:
            print(f"  {n}/{len(rows)}  {(time.time() - t0) / n:.2f}s/q", flush=True)
        if n % 50 == 0:                         # checkpoint: a crash or reboot loses at most ~2 minutes
            jl_write(partial, out)
    jl_write(f"{CTX}/{a.set}__{a.tag}.jsonl", out)
    if os.path.exists(partial):
        os.remove(partial)
    print(f"saved {CTX}/{a.set}__{a.tag}.jsonl")


# ------------------------------------------------------------------ stage 2: answering
def cmd_answer(a):
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    rows = jl_read(f"{SETS}/{a.set}.jsonl")
    ctx = {c["qid"]: c["ctx"] for c in jl_read(f"{CTX}/{a.set}__{a.ctx}.jsonl")} if a.ctx else None
    tok = AutoTokenizer.from_pretrained(a.model)
    kw = dict(device_map="cuda", dtype=torch.bfloat16)
    if a.load_4bit:
        kw["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                                       bnb_4bit_compute_dtype=torch.bfloat16)
    model = AutoModelForCausalLM.from_pretrained(a.model, **kw).eval()
    digit_ids = {d: tok.encode(str(d), add_special_tokens=False)[-1] for d in range(1, 10)}

    out_path = f"{RUNS}/{a.set}__{a.tag}.jsonl"
    done = {r["qid"]: r for r in jl_read(out_path)} if os.path.exists(out_path) else {}
    want = {r["qid"] for r in rows}
    for f in (a.reuse or []):                   # answers from the same model+ctx+k on another set
        for r in jl_read(f"{RUNS}/{f}.jsonl"):
            if r["qid"] in want and r["qid"] not in done:
                done[r["qid"]] = r
    if a.reuse:
        jl_write(out_path, list(done.values()))
        print(f"reused {len(done)} answers", flush=True)
    results, t0 = list(done.values()), time.time()
    os.makedirs(RUNS, exist_ok=True)
    f = open(out_path, "a")
    todo = [r for r in rows if r["qid"] not in done]
    for n, r in enumerate(todo, 1):
        opts = "\n".join(f"{i}. {o}" for i, o in enumerate(r["options"], 1))
        user = f"Question: {r['question']}\nOptions:\n{opts}\nAnswer with the option number only."
        if ctx is not None:
            passages = "\n\n".join(f"[{i}] ({c['source']}, {c['loc']})\n{c['text'][:a.ctx_chars]}"
                                   for i, c in enumerate(ctx[r["qid"]][:a.k], 1))
            user = f"Context:\n{passages}\n\n{user}"
        msgs = [{"role": "system", "content": SYS_RAG if ctx is not None else SYS_BASE},
                {"role": "user", "content": user}]
        prompt = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
        enc = tok(prompt, return_tensors="pt").to("cuda")
        with torch.no_grad():
            logits = model(**enc, logits_to_keep=1).logits[0, -1].float()   # only last position: avoids a seq x vocab tensor
        cand = list(range(1, len(r["options"]) + 1))
        scores = {d: logits[digit_ids[d]].item() for d in cand}
        pred = max(scores, key=scores.get)
        rec = {"qid": r["qid"], "level": r["level"], "answer": r["answer"], "pred": pred,
               "correct": pred == r["answer"],
               "scores": [round(scores[d], 3) for d in cand]}     # per-option logits: for blending / calibration
        results.append(rec)
        f.write(json.dumps(rec) + "\n"); f.flush()
        if n % 100 == 0:
            acc = sum(x["correct"] for x in results) / len(results)
            print(f"  {len(results)}/{len(rows)}  acc={acc:.3f}  {(time.time() - t0) / n:.2f}s/q", flush=True)
    f.close()
    summarize(a.set, a.tag)


# ------------------------------------------------------------------ scoring
def summarize(set_name, tag, only=None):
    res = jl_read(f"{RUNS}/{set_name}__{tag}.jsonl")
    if only is not None:
        res = [x for x in res if x["qid"] in only]
    if not res:
        return dict(tag=tag, n=0, easy=None, medium=None, hard=None, avg=None, overall=None)
    by = {lv: [x["correct"] for x in res if x["level"] == lv] for lv in LEVELS.values()}
    accs = {lv: sum(v) / len(v) for lv, v in by.items() if v}
    avg = sum(accs.values()) / len(accs)              # macro average over levels (ORANSight-2.0 'Average')
    overall = sum(x["correct"] for x in res) / len(res)
    return dict(tag=tag, n=len(res), **{lv: accs.get(lv) for lv in LEVELS.values()}, avg=avg, overall=overall)


def cmd_score(a):
    rows = []
    only = {r["qid"] for r in jl_read(f"{SETS}/{a.set}.jsonl")} if a.set else None
    for p in sorted(glob.glob(f"{RUNS}/*.jsonl")):
        s, t = os.path.basename(p)[:-6].split("__", 1)
        if only is None:
            rows.append((s, summarize(s, t)))
        else:                                   # every run that covers this set, restricted to its questions
            r = summarize(s, t, only)
            if r["n"] == len(only):
                rows.append((a.set if s == a.set else f"{s}>sub", r))
    print(f"{'set':12s} {'run':28s} {'n':>6s} {'easy':>6s} {'medium':>7s} {'hard':>6s} {'AVG':>6s} {'overall':>8s}")
    for s, r in rows:
        f = lambda v: f"{v:.3f}" if v is not None else "  -  "
        print(f"{s:12s} {r['tag']:28s} {r['n']:6d} {f(r['easy']):>6s} {f(r['medium']):>7s} {f(r['hard']):>6s} "
              f"{f(r['avg']):>6s} {f(r['overall']):>8s}")
    print("\nPublished (ORANSight-2.0, Table V; 500/level):  best 0.904 / 0.884 / 0.878  avg 0.889 ;  NVIDIA-O-RAN avg 0.826")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("sample"); p.add_argument("--n", type=int, default=500); p.add_argument("--seed", type=int, default=42)
    p = sub.add_parser("retrieve"); p.add_argument("--set", default="sample_500"); p.add_argument("--index", default="index")
    p.add_argument("--tag", required=True); p.add_argument("-k", type=int, default=5)
    p.add_argument("--query", choices=["q", "qo"], default="qo", help="q = question only, qo = question + options")
    p.add_argument("--hybrid", action="store_true", help="add BM25 keyword candidates before reranking")
    p.add_argument("--reuse", nargs="*", help="ctx files (set__tag) whose contexts to reuse, e.g. sample_500__idxfull")
    p = sub.add_parser("answer"); p.add_argument("--set", default="sample_500"); p.add_argument("--ctx", default=None)
    p.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct"); p.add_argument("--tag", required=True)
    p.add_argument("-k", type=int, default=5); p.add_argument("--ctx-chars", type=int, default=3000)
    p.add_argument("--load-4bit", action="store_true")
    p.add_argument("--reuse", nargs="*", help="run files (set__tag) whose answers to reuse, e.g. sample_500__q7b_ragfull")
    p = sub.add_parser("score"); p.add_argument("--set", default=None,
                                                 help="score every run on this set's questions (e.g. tune_200)")
    a = ap.parse_args()
    {"sample": cmd_sample, "retrieve": cmd_retrieve, "answer": cmd_answer, "score": cmd_score}[a.cmd](a)

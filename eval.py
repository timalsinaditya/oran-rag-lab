"""Part 2 Task A: evaluate base LLM vs RAG on eval/questions.json.

Usage:
  python eval.py generate   # Qwen2.5-7B answers every question with and without RAG -> results/eval_answers.json
  python eval.py judge      # Phi-4 (different model family) scores answers          -> results/eval_results.csv, eval_summary.md
  python eval.py all        # both

Metrics
  correctness (base & RAG): judge compares the answer with the reference -> correct / partial / incorrect
  grounding   (RAG):        judge checks every claim is supported by the retrieved passages -> yes / partial / no
                            (base has no sources, so by construction it is ungrounded)
  retrieval hit@k:          the expected source document appears among the top-k retrieved passages
Accuracy = (#correct + 0.5 * #partial) / N ; strict accuracy counts only "correct".
"""
import json, re, sys, gc, textwrap
import pandas as pd, torch

OVR = "eval/overrides.json"
QFILE, ANS, CSV, MD = "eval/questions.json", "results/eval_answers.json", "results/eval_results.csv", "results/eval_summary.md"
JUDGE_MODEL = "microsoft/phi-4"
K = 5


# ---------------------------------------------------------------- phase 1: generate
def retrieval_hit(q, hits):
    """True if every expected source doc is among the retrieved passages (None for unanswerable questions)."""
    srcs = q.get("source")
    if not srcs:
        return None
    srcs = [srcs] if isinstance(srcs, str) else srcs
    return all(any(h["source"].startswith(s) for h in hits) for s in srcs)


def generate():
    from rag import RAG
    rag, qs, out = RAG(), json.load(open(QFILE)), []
    for q in qs:
        base = rag.answer_base(q["question"])
        ans, hits = rag.answer_rag(q["question"], K)
        out.append(dict(q, base_answer=base, rag_answer=ans,
                        retrieved=[{k: h[k] for k in ("rank", "source", "loc", "score", "text")} for h in hits],
                        retrieval_hit=retrieval_hit(q, hits)))
        print(f"[{q['id']:2d}] hit={out[-1]['retrieval_hit']!s:5}  {q['question']}")
    json.dump(out, open(ANS, "w"), indent=1)
    print(f"saved {ANS}")
    del rag; gc.collect(); torch.cuda.empty_cache()


# ---------------------------------------------------------------- phase 2: judge
CORRECT_PROMPT = """You are grading an answer about O-RAN specifications.
Question: {question}
Reference answer: {reference}
Candidate answer: {answer}

Compare the candidate with the reference. Extra correct detail is fine.
- "correct": contains the key facts of the reference and nothing contradicting it
- "partial": some key facts right but important ones missing, or minor errors
- "incorrect": key facts wrong, contradicting the reference, or a refusal / "not covered"
Reply with JSON only: {{"verdict": "correct|partial|incorrect", "reason": "<one sentence>"}}"""

UNANSWERABLE_PROMPT = """You are grading an answer about O-RAN specifications.
The question CANNOT be answered from the O-RAN document collection the assistant has: {reference}
Question: {question}
Candidate answer: {answer}

- "correct": the candidate declines, says the information is not available/not covered, or clearly states it does not know
- "partial": the candidate hedges heavily but still gives a specific value or claim
- "incorrect": the candidate confidently gives a specific answer (a fabricated value, name or fact)
Reply with JSON only: {{"verdict": "correct|partial|incorrect", "reason": "<one sentence>"}}"""

GROUND_PROMPT = """You are checking whether an answer is grounded in retrieved documents.
Retrieved passages:
{context}

Answer: {answer}

Is every factual claim in the answer supported by the passages above (ignore whether it is actually true)?
- "yes": all claims supported
- "partial": most claims supported, some not
- "no": main claims not supported by the passages
Reply with JSON only: {{"grounded": "yes|partial|no", "reason": "<one sentence>"}}"""


class Judge:
    def __init__(self):
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        self.tok = AutoTokenizer.from_pretrained(JUDGE_MODEL)
        self.m = AutoModelForCausalLM.from_pretrained(
            JUDGE_MODEL, device_map="cuda",
            quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                                   bnb_4bit_compute_dtype=torch.bfloat16))

    @torch.no_grad()
    def ask(self, prompt):
        text = self.tok.apply_chat_template([{"role": "user", "content": prompt}],
                                            add_generation_prompt=True, tokenize=False)
        enc = self.tok(text, return_tensors="pt").to("cuda")
        out = self.m.generate(**enc, max_new_tokens=150, do_sample=False, pad_token_id=self.tok.eos_token_id)
        raw = self.tok.decode(out[0, enc["input_ids"].shape[1]:], skip_special_tokens=True)
        m = re.search(r"\{.*?\}", raw, re.S)
        try:
            return json.loads(m.group(0))
        except Exception:
            return {"verdict": "unparsed", "grounded": "unparsed", "reason": raw.strip()[:200]}


def cited_passage(r):
    """First passage the RAG answer cites as [n] (falls back to rank 1)."""
    m = re.search(r"\[(\d+)\]", r["rag_answer"])
    n = int(m.group(1)) if m else 1
    return next((h for h in r["retrieved"] if h["rank"] == n), r["retrieved"][0])


def judge():
    rows, J = json.load(open(ANS)), Judge()
    for r in rows:
        P = CORRECT_PROMPT if r.get("answerable", True) else UNANSWERABLE_PROMPT
        b = J.ask(P.format(question=r["question"], reference=r["reference"], answer=r["base_answer"]))
        g = J.ask(P.format(question=r["question"], reference=r["reference"], answer=r["rag_answer"]))
        ctx = "\n\n".join(f"[{h['rank']}] {h['text'][:2500]}" for h in r["retrieved"])
        gr = J.ask(GROUND_PROMPT.format(context=ctx, answer=r["rag_answer"]))
        r.update(base_verdict=b.get("verdict"), base_reason=b.get("reason"),
                 rag_verdict=g.get("verdict"), rag_reason=g.get("reason"),
                 rag_grounded=gr.get("grounded"), ground_reason=gr.get("reason"),
                 rag_has_citation=bool(re.search(r"\[\d+\]", r["rag_answer"])))
        print(f"[{r['id']:2d}] base={r['base_verdict']:9s} rag={r['rag_verdict']:9s} grounded={r['rag_grounded']}")
    json.dump(rows, open(ANS, "w"), indent=1)
    report(rows)


def apply_overrides(rows):
    """Manual corrections of judge verdicts (eval/overrides.json), recorded with a reason."""
    import os
    if not OVR or not os.path.exists(OVR):
        return []
    byid, applied = {r["id"]: r for r in rows}, []
    for o in json.load(open(OVR)):
        r = byid[o["id"]]
        applied.append(dict(o, judge_value=r.get(o["field"])))
        r[o["field"] + "_judge"] = r.get(o["field"])
        r[o["field"]] = o["value"]
    return applied


def report(rows):
    raw = pd.DataFrame(rows)
    raw_acc = {c: raw[c].map(lambda v: {"correct": 1.0, "partial": 0.5}.get(v, 0.0)).mean()
               for c in ("base_verdict", "rag_verdict")}
    applied = apply_overrides(rows)
    df = pd.DataFrame(rows)
    cols = [c for c in ["id", "topic", "qtype", "question", "reference", "source", "base_answer", "base_verdict", "base_reason",
            "rag_answer", "rag_verdict", "rag_reason", "rag_grounded", "ground_reason", "rag_has_citation", "retrieval_hit"] if c in df]
    df[cols].to_csv(CSV, index=False)

    n = len(df)
    score = {"correct": 1.0, "partial": 0.5}
    acc = lambda col: df[col].map(lambda v: score.get(v, 0.0)).mean()
    strict = lambda col: (df[col] == "correct").mean()
    gscore = df["rag_grounded"].map({"yes": 1.0, "partial": 0.5}).fillna(0).mean()

    L = [f"# Task A: Base LLM vs RAG ({n} questions)\n",
         "Generator: Qwen2.5-7B-Instruct · Retriever: bge-m3 + bge-reranker-v2-m3 (top-5) · Judge: Phi-4 (4-bit)\n",
         "| Metric | Base (no RAG) | RAG |", "|---|---|---|",
         f"| Accuracy (correct=1, partial=0.5) | {acc('base_verdict'):.1%} | {acc('rag_verdict'):.1%} |",
         f"| Accuracy, raw judge (before manual review) | {raw_acc['base_verdict']:.1%} | {raw_acc['rag_verdict']:.1%} |",
         f"| Strict accuracy (correct only) | {strict('base_verdict'):.1%} | {strict('rag_verdict'):.1%} |",
         f"| Grounding (yes=1, partial=0.5) | 0% (no sources) | {gscore:.1%} |",
         f"| Answers with citations | 0% | {df['rag_has_citation'].mean():.1%} |",
         f"| Retrieval hit@{K} (expected doc retrieved) | n/a | {df['retrieval_hit'].dropna().astype(float).mean():.1%} |", "",
         "## Verdict counts\n", "| Verdict | Base | RAG |", "|---|---|---|"]
    for v in ["correct", "partial", "incorrect", "unparsed"]:
        L.append(f"| {v} | {(df.base_verdict == v).sum()} | {(df.rag_verdict == v).sum()} |")

    L += ["", "## By topic (accuracy)\n", "| Topic | N | Base | RAG |", "|---|---|---|---|"]
    for t, g in df.groupby("topic", sort=False):
        a = lambda col: g[col].map(lambda v: score.get(v, 0.0)).mean()
        L.append(f"| {t} | {len(g)} | {a('base_verdict'):.0%} | {a('rag_verdict'):.0%} |")
    if "qtype" in df:
        L += ["", "## By question type (accuracy)\n", "| Type | N | Base | RAG |", "|---|---|---|---|"]
        for t, g in df.groupby("qtype", sort=False):
            a = lambda col: g[col].map(lambda v: score.get(v, 0.0)).mean()
            L.append(f"| {t} | {len(g)} | {a('base_verdict'):.0%} | {a('rag_verdict'):.0%} |")

    if applied:
        L += ["", f"## Manual review of judge verdicts ({len(applied)} overrides)\n",
              "| Q | Field | Judge | Manual | Reason |", "|---|---|---|---|---|"]
        L += [f"| {o['id']} | {o['field']} | {o['judge_value']} | {o['value']} | {o['reason']} |" for o in applied]

    fixed = [r for r in rows if r["base_verdict"] == "incorrect" and r["rag_verdict"] == "correct"]
    L += ["", f"## Base hallucinated, RAG correct ({len(fixed)} cases)\n"]
    for r in fixed:
        p = cited_passage(r)
        L += [f"### Q{r['id']}. {r['question']}",
              f"- **Reference:** {r['reference']}",
              f"- **Base (incorrect):** {r['base_answer']}",
              f"  - _Judge:_ {r['base_reason']}",
              f"- **RAG (correct):** {r['rag_answer']}",
              f"- **Cited passage [{p['rank']}]** `{p['source']}` {p['loc']}:",
              "  > " + textwrap.shorten(p["text"], 600), ""]

    worse = [r for r in rows if r["rag_verdict"] != "correct"]
    L += [f"## RAG not fully correct ({len(worse)} cases), for the error analysis\n"]
    for r in worse:
        L.append(f"- **Q{r['id']}** ({r['rag_verdict']}, retrieval hit={r['retrieval_hit']}): {r['question']} | {r['rag_reason']}")
    open(MD, "w").write("\n".join(L) + "\n")
    print("\n".join(L[:20]))
    print(f"\nsaved {CSV} and {MD}")


if __name__ == "__main__":
    import argparse, os
    ap = argparse.ArgumentParser()
    ap.add_argument("step", nargs="?", default="all", choices=["generate", "judge", "all", "report"])
    ap.add_argument("--questions", default=QFILE)
    ap.add_argument("--out", default="results", help="output folder")
    ap.add_argument("--overrides", default=OVR, help="manual verdict overrides ('' for none)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    QFILE, OVR = a.questions, a.overrides
    ANS, CSV, MD = (f"{a.out}/eval_answers.json", f"{a.out}/eval_results.csv", f"{a.out}/eval_summary.md")
    step = a.step
    if step in ("generate", "all"):
        generate()
    if step in ("judge", "all"):
        judge()
    if step == "report":
        report(json.load(open(ANS)))

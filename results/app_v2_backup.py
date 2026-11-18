"""O-RAN LLM Assistant: web app for the Lab 2 deliverables.

Tabs
  💬 Chat              streaming RAG chat with [n] citations, cited passages panel, optional no-RAG comparison
  📝 ORAN-Bench quiz   pick a benchmark question, the model answers it live (with / without RAG)
  🔎 Explorer          browse saved benchmark runs: every model's pick + retrieved passages per question
  📊 Results           Task A and ORAN-Bench result tables
  ℹ️ About             pipeline, corpus and design choices

Usage:  python app.py   ->  http://localhost:7860   (over SSH: ssh -N -L 7860:localhost:7860 user@server)
"""
import glob, json, math, os, random, re, sys, threading
import gradio as gr

ROOT = os.path.dirname(os.path.abspath(__file__))
BENCH = f"{ROOT}/bench"
sys.path.insert(0, BENCH)
from run_bench import SYS_RAG as MCQ_SYS_RAG, SYS_BASE as MCQ_SYS_BASE   # same prompts as the benchmark runs
from rag import RAG_SYSTEM, BASE_SYSTEM

KBS = {"Full O-RAN corpus: 166 specs, v2 chunks (best)": "index_v2",
       "Full O-RAN corpus: 166 specs, 800-token chunks": "index_full",
       "Lab corpus: 29 documents": "index"}
KBS = {k: v for k, v in KBS.items() if os.path.exists(f"{ROOT}/{v}/faiss.index")}
KB_DEFAULT = next(iter(KBS))

# ------------------------------------------------------------------ model (loaded once, shared by all tabs)
_rag, _lock, _load_error = None, threading.Lock(), None


def get_rag():
    global _rag, _load_error
    with _lock:
        if _rag is None:
            import torch
            free = torch.cuda.mem_get_info()[0] / 2**30
            if free < 18:   # 7B bf16 + embedder + reranker; never push another GPU job out of memory
                raise gr.Error(f"Only {free:.1f} GB GPU memory free (need ~18 GB); another GPU job is running. "
                               "The Explorer and Results tabs work without the GPU.")
            os.chdir(ROOT)
            from rag import RAG
            _rag = RAG(index_dir=KBS[KB_DEFAULT])
        return _rag


def _warmup():
    try:
        get_rag()
        print("models loaded", flush=True)
    except Exception as e:                      # app still works (explorer/results); chat loads on first use
        print(f"warm-up skipped: {e}", flush=True)


def kb_info(kb):
    try:
        n = len(json.load(open(f"{ROOT}/{KBS[kb]}/chunks.json")))
        docs = len({c["source"] for c in json.load(open(f"{ROOT}/{KBS[kb]}/chunks.json"))})
        return f"{n:,} chunks from {docs} documents"
    except Exception:
        return ""


def passages_md(hits, title="Retrieved passages"):
    if not hits:
        return ""
    out = [f"### {title}"]
    for h in hits:
        text = re.sub(r"^\[[^\]]*\]\n", "", h["text"])        # drop the "[spec | section]" chunk prefix for display
        out.append(f"**[{h['rank']}] {h['source']}**  \n_{h['loc']}_ · relevance {h['score']:.2f}\n\n"
                   f"<details><summary>{text[:220].strip()} …</summary>\n\n{text}\n\n</details>")
    return "\n\n".join(out)


# ------------------------------------------------------------------ 💬 chat
def as_text(content):
    """Gradio 6 returns chat message content as a list of parts ([{"type": "text", "text": ...}]); flatten it."""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        return content.get("text") or ""
    if isinstance(content, (list, tuple)):
        return "".join(as_text(c) for c in content)
    return str(content or "")


FOLLOW_UP = re.compile(r"\b(it|its|it's|this|that|these|those|they|them|their|above|same|also)\b", re.I)


def chat(message, history, kb, k, hybrid, compare):
    message = (message or "").strip()
    if not message:
        yield history, gr.update(), gr.update(), ""
        return
    rag = get_rag()
    rag.use_index(KBS[kb])
    # earlier turns -> (user, assistant) pairs; keep the last 3 so the prompt stays small
    history = [{"role": m["role"], "content": as_text(m["content"])} for m in (history or [])]
    pairs, prev_user = [], None
    for m in history:
        if m["role"] == "user":
            prev_user = m["content"]
        elif prev_user is not None:
            pairs.append((prev_user, m["content"]))
    pairs = pairs[-3:]
    # short / pronoun follow-ups ("what about its procedures?") are retrieved together with the last question
    # that named the topic (walk back over earlier follow-ups, which don't name it either)
    is_follow = lambda t: len(t.split()) <= 6 or bool(FOLLOW_UP.search(t))
    query = message
    if pairs and is_follow(message):
        users = [u for u, _ in pairs]
        anchor = next((u for u in reversed(users) if not is_follow(u)), users[0])
        query = anchor + " " + message
    hits = rag.retrieve(query, int(k), hybrid=hybrid)
    ctx = passages_md(hits)
    history = history + [{"role": "user", "content": message}, {"role": "assistant", "content": ""}]
    # history for the LLM: earlier answers only (their passages are no longer in context, so strip citations)
    llm_hist = [(u, re.sub(r"\[\d+\]", "", a)) for u, a in pairs]
    for text in rag.stream(RAG_SYSTEM, rag.rag_prompt(message, hits), history=llm_hist):
        history[-1]["content"] = text
        yield history, ctx, "", ""
    base = ""
    if compare:
        for text in rag.stream(BASE_SYSTEM, message, history=llm_hist):
            base = "### Same model without RAG\n_No documents, model memory only (Part 1 baseline):_\n\n" + text
            yield history, ctx, base, ""
    yield history, ctx, base, ""


# ------------------------------------------------------------------ 📝 quiz (live MCQ)
def jl(path):
    return [json.loads(l) for l in open(path) if l.strip()] if os.path.exists(path) else []


QUIZ_SETS = {"Official ORANBench (ORANSight-2.0 eval set, 1,500)": "oranbench",
             "ORAN-Bench-13K, all questions (13,819)": "full"}
_quiz_cache = {}


def quiz_questions(set_name):
    if set_name not in _quiz_cache:
        _quiz_cache[set_name] = jl(f"{BENCH}/sets/{QUIZ_SETS[set_name]}.jsonl")
    return _quiz_cache[set_name]


def quiz_pick(set_name, level):
    qs = [q for q in quiz_questions(set_name) if level == "all" or q["level"] == level]
    q = random.choice(qs)
    opts = "\n".join(f"{i}. {o}" for i, o in enumerate(q["options"], 1))
    md = f"**{q['qid']}** · _{q['level']}_\n\n### {q['question']}\n\n{opts}"
    return q, md, None, "", ""


def mcq_probs(rag, q, hits):
    """Same scoring as the benchmark: next-token logits of the option numbers, softmax over the options."""
    import torch
    opts = "\n".join(f"{i}. {o}" for i, o in enumerate(q["options"], 1))
    user = f"Question: {q['question']}\nOptions:\n{opts}\nAnswer with the option number only."
    if hits is not None:
        passages = "\n\n".join(f"[{i}] ({c['source']}, {c['loc']})\n{c['text'][:3000]}" for i, c in enumerate(hits, 1))
        user = f"Context:\n{passages}\n\n{user}"
    msgs = [{"role": "system", "content": MCQ_SYS_RAG if hits is not None else MCQ_SYS_BASE},
            {"role": "user", "content": user}]
    enc = rag.tok(rag.tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False),
                  return_tensors="pt").to("cuda")
    with torch.no_grad():
        logits = rag.llm(**enc, logits_to_keep=1).logits[0, -1].float()
    ids = [rag.tok.encode(str(i), add_special_tokens=False)[-1] for i in range(1, len(q["options"]) + 1)]
    p = torch.softmax(logits[ids], 0).tolist()
    return {f"{i}. {o[:60]}": p[i - 1] for i, o in enumerate(q["options"], 1)}


def quiz_answer(q, kb, use_rag):
    if not q:
        raise gr.Error("Pick a question first.")
    rag = get_rag()
    rag.use_index(KBS[kb])
    hits = None
    if use_rag:
        hits = rag.retrieve(q["question"] + " " + " ".join(q["options"]), 5,
                            exclude=("ORAN-Bench-13K", "ORANSight"), hybrid=True)
    probs = mcq_probs(rag, q, hits)
    pick = max(probs, key=probs.get)
    picked = int(pick.split(".")[0])
    verdict = ("✅ **Correct**" if picked == q["answer"] else "❌ **Wrong**") + \
        f": model picked **{picked}**, correct answer is **{q['answer']}. {q['options'][q['answer'] - 1]}**"
    return probs, verdict, passages_md(hits or [], "Passages given to the model")


# ------------------------------------------------------------------ 🔎 explorer (saved runs)
SETS = {"oranbench": "Official ORANBench (ORANSight-2.0 set, 1,500)",
        "sample_500": "Our random sample, seed 42 (1,500)",
        "tune_200": "Tuning subset (600)"}
RUN_NAMES = {"q7b_base": "7B, no RAG", "q32b_base": "32B, no RAG", "q7b_rag29": "7B + RAG (29 docs)",
             "q7b_ragfull": "7B + RAG (166 specs)", "q7b_v2_k5": "7B + RAG v2", "q7b_v2_k8": "7B + RAG v2 k=8",
             "q7b_v2h_k5": "7B + RAG v2 hybrid", "q7b_v2h_k8": "7B + RAG v2 hybrid k=8"}
CTX_NAMES = {"idx29": "29-doc index", "idxfull": "166 specs, 800-token chunks", "idxv2": "166 specs, v2",
             "idxv2h": "166 specs, v2 hybrid"}
OUTCOMES = ["all", "RAG correct, base wrong (RAG fixed it)", "RAG wrong, base correct (RAG broke it)",
            "both wrong", "both correct"]
PUBLISHED = [("ORANSight-2.0 best (Qwen2.5-32B + RAG)", .904, .884, .878, .889),
             ("Gemma-2 27B + reranker (ORANSight-2.0)", .895, .875, .871, .880),
             ("NVIDIA-O-RAN chatbot", .826, .816, .836, .826),
             ("TSpec-LLM", .748, .668, .526, .647)]


def load_set(set_name):
    qs = jl(f"{BENCH}/sets/{set_name}.jsonl")
    runs = {}
    for p in sorted(glob.glob(f"{BENCH}/runs/{set_name}__*.jsonl")):
        res = {r["qid"]: r for r in jl(p)}
        if len(res) >= len(qs):                         # complete runs only
            runs[os.path.basename(p)[len(set_name) + 2:-6]] = res
    ctxs = {}
    for p in sorted(glob.glob(f"{BENCH}/ctx/{set_name}__*.jsonl")):
        tag = os.path.basename(p)[len(set_name) + 2:-6]
        if not tag.endswith(".partial"):
            ctxs[tag] = {c["qid"]: c["ctx"] for c in jl(p)}
    return qs, runs, ctxs


def accs(qs, res):
    a = {}
    for lv in ("easy", "medium", "hard"):
        v = [res[q["qid"]]["correct"] for q in qs if q["level"] == lv and q["qid"] in res]
        a[lv] = sum(v) / len(v) if v else None
    got = [x for x in a.values() if x is not None]
    a["avg"] = sum(got) / len(got) if got else None
    return a


def score_table(qs, runs, published=True):
    f = lambda x: f"{x:.3f}" if x is not None else "–"
    lines = ["| System | Easy | Medium | Hard | **Avg** |", "|---|---|---|---|---|"]
    for tag, res in runs.items():
        a = accs(qs, res)
        lines.append(f"| {RUN_NAMES.get(tag, tag)} (ours) | {f(a['easy'])} | {f(a['medium'])} | {f(a['hard'])} | "
                     f"**{f(a['avg'])}** |")
    if published:
        for name, e, m, h, avg in PUBLISHED:
            lines.append(f"| _{name}, published_ | _{e:.3f}_ | _{m:.3f}_ | _{h:.3f}_ | _{avg:.3f}_ |")
    return "\n".join(lines)


def filtered(set_name, level, outcome, base_run, rag_run):
    qs, runs, ctxs = load_set(set_name)
    choices = list(runs)
    base_run = base_run if base_run in runs else ("q7b_base" if "q7b_base" in runs else
                                                  next((t for t in choices if "base" in t), None))
    rag_run = rag_run if rag_run in runs else next((t for t in reversed(choices) if "rag" in t or "v2" in t), None)
    sel = [q for q in qs if level == "all" or q["level"] == level]
    if outcome != "all" and base_run and rag_run:
        b, r = runs[base_run], runs[rag_run]
        keep = {OUTCOMES[1]: lambda x, y: y and not x, OUTCOMES[2]: lambda x, y: x and not y,
                OUTCOMES[3]: lambda x, y: not x and not y, OUTCOMES[4]: lambda x, y: x and y}[outcome]
        sel = [q for q in sel if keep(b[q["qid"]]["correct"], r[q["qid"]]["correct"])]
    labels = [f"{q['qid']} · {q['level']} · {q['question'][:70]}" for q in sel]
    return qs, runs, choices, base_run, rag_run, labels


def refresh(set_name, level, outcome, base_run, rag_run):
    qs, runs, choices, base_run, rag_run, labels = filtered(set_name, level, outcome, base_run, rag_run)
    return (score_table(qs, runs, published=(set_name == "oranbench")),
            gr.update(choices=choices, value=base_run), gr.update(choices=choices, value=rag_run),
            gr.update(choices=labels, value=labels[0] if labels else None), f"**{len(labels)}** questions match")


def show(set_name, label, ctx_k):
    if not label:
        return "_No question selected._", ""
    qs, runs, ctxs = load_set(set_name)
    qid = label.split(" · ")[0]
    q = next(x for x in qs if x["qid"] == qid)
    rows = ["| # | Option | Correct | " + " | ".join(RUN_NAMES.get(t, t) for t in runs) + " |",
            "|---|---|---|" + "---|" * len(runs)]
    for i, o in enumerate(q["options"], 1):
        marks = ["✅" if r[qid]["pred"] == i == r[qid]["answer"] else "❌" if r[qid]["pred"] == i else ""
                 for r in runs.values()]
        rows.append(f"| {i} | {o} | {'✔️' if i == q['answer'] else ''} | " + " | ".join(marks) + " |")
    md = (f"### {qid} ({q['level']})\n\n**{q['question']}**\n\n" + "\n".join(rows) +
          "\n\n✔️ correct answer · ✅ model's pick (right) · ❌ model's pick (wrong)")
    out = []
    for tag, c in ctxs.items():
        if c.get(qid):
            out.append(passages_md([dict(h, rank=n) for n, h in enumerate(c[qid][:int(ctx_k)], 1)],
                                   f"Retrieved: {CTX_NAMES.get(tag, tag)}"))
    return md, "\n\n".join(out) or "_No retrieval saved for this question._"


def step(d, set_name, level, outcome, base_run, rag_run, label):
    labels = filtered(set_name, level, outcome, base_run, rag_run)[-1]
    if not labels:
        return None
    i = labels.index(label) if label in labels else 0
    return gr.update(value=labels[max(0, min(len(labels) - 1, i + d))])


# ------------------------------------------------------------------ 📊 results
def bench_results_md():
    out = []
    qs, runs, _ = load_set("oranbench")
    if runs:
        out += ["### ORAN-Bench: official ORANBench set (the exact 1,500 questions ORANSight-2.0 used)",
                score_table(qs, runs), ""]
    qs, runs, _ = load_set("sample_500")
    if runs:
        out += ["### ORAN-Bench: our random sample (seed 42, 500 per level)", score_table(qs, runs, False), ""]
    qs, runs, _ = load_set("tune_200")
    if runs:
        out += ["### Retrieval ablation (600-question tuning subset)", score_table(qs, runs, False),
                "_Differences under ~3 points on 600 questions can be noise._", ""]
    return "\n".join(out)


TASK_A = {"Diverse questions (WG1–WG11, 7 question types), 29 docs": "results/v2_29docs_diverseQ/eval_summary.md",
          "Original questions, 29 docs": "results/v2_29docs_origQ/eval_summary.md",
          "Original questions, 8 docs (first version)": "results/v1_8docs/eval_summary.md"}


def task_a_md(name):
    p = f"{ROOT}/{TASK_A[name]}"
    return open(p).read() if os.path.exists(p) else "_not found_"


ABOUT = """
## How it works

```
 O-RAN specs (PDF/DOCX)                                         question
        │                                                           │
  parse + clean  ── page / section locations, drop TOC,             │
        │           boilerplate, ASN.1, headers/footers             ▼
  chunk (400 tokens, 15% overlap, "[spec | section]" prefix)   ┌──────────────┐
        │                                                      │ bge-m3 dense │──┐ top-30
  embed (BAAI/bge-m3) ──► FAISS (cosine) ─────────────────────►│ FAISS search │  │
        └──────────────────► BM25 keyword index ──────────────►│ BM25 search  │──┤ top-30
                                                               └──────────────┘  ▼
                                                     cross-encoder reranker (bge-reranker-v2-m3)
                                                                   │ top-5 passages
                                                                   ▼
                                                     Qwen2.5-7B-Instruct  ──►  answer with [n] citations
```

| Component | Choice | Why |
|---|---|---|
| Corpus | 166 latest-version O-RAN ALLIANCE specs (WG1–WG11, TIFG); lab corpus: 29 docs | The benchmark's questions come from the specs; older versions removed so they don't crowd results |
| Chunking | 400 tokens, 60 overlap, spec/section prefix (lab index: 800/120) | Small chunks pin down single facts; the prefix keeps document context |
| Retrieval | bge-m3 dense + BM25 → cross-encoder reranker → top-5 | Dense finds meaning, BM25 finds exact identifiers, reranker reads question and passage together |
| Generator | Qwen2.5-7B-Instruct (bf16, one 24 GB NVIDIA L4) | Strong open 7B; same family as the published best (32B) |
| Grounding | Answer only from passages, cite [n], refuse if not covered | Reduces hallucination; every claim is checkable |
| Evaluation | Task A: 50 questions, LLM judge (Phi-4); ORAN-Bench-13K multiple choice via option logits | Judge from a different model family; deterministic multiple-choice scoring |
"""

# ------------------------------------------------------------------ layout
CSS = """
#chatbot {min-height: 520px}
.passages {max-height: 640px; overflow-y: auto}
footer {display: none !important}
"""

with gr.Blocks(title="O-RAN LLM Assistant") as demo:
    gr.Markdown("# 📡 O-RAN LLM Assistant\nAsk about the O-RAN ALLIANCE specifications. Answers are grounded in "
                "retrieved spec passages and cite their sources. _Qwen2.5-7B-Instruct + bge-m3 / BM25 retrieval "
                "+ bge-reranker-v2-m3 · Lab 2, ECE 592 / CSC 591_")

    with gr.Tab("💬 Chat"):
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(elem_id="chatbot", label="Conversation", height=560)
                with gr.Row():
                    msg = gr.Textbox(placeholder="e.g. What does the A1 interface do?", show_label=False, scale=8,
                                     autofocus=True)
                    send = gr.Button("Send", variant="primary", scale=1)
                    clear = gr.Button("New chat", scale=1)
                gr.Examples(["What does the A1 interface do?", "List the E2AP services.",
                             "What is the difference between the hierarchical and hybrid M-Plane architecture models?",
                             "Which E2SM-KPM event trigger styles exist?", "What is the O2 interface used for?",
                             "What does the O-RAN Z7 interface connect?"], inputs=msg, label="Try")
                baseline = gr.Markdown()
            with gr.Column(scale=2):
                with gr.Accordion("Settings", open=False):
                    kb = gr.Dropdown(list(KBS), value=KB_DEFAULT, label="Knowledge base")
                    kb_txt = gr.Markdown(kb_info(KB_DEFAULT))
                    k = gr.Slider(1, 10, value=5, step=1, label="Passages (top-k)")
                    hybrid = gr.Checkbox(value=True, label="Hybrid search (dense + BM25 keywords)")
                    compare = gr.Checkbox(value=False, label="Also show the answer without RAG")
                ctx_panel = gr.Markdown("_Cited passages appear here._", elem_classes="passages")
        kb.change(kb_info, kb, kb_txt)
        ins, outs = [msg, chatbot, kb, k, hybrid, compare], [chatbot, ctx_panel, baseline, msg]
        msg.submit(chat, ins, outs)
        send.click(chat, ins, outs)
        clear.click(lambda: ([], "_Cited passages appear here._", "", ""), None, outs)

    with gr.Tab("📝 ORAN-Bench quiz"):
        gr.Markdown("Pick a question from the benchmark. The model answers it **live**: with RAG it reads the "
                    "top-5 retrieved passages; without RAG it uses only its own memory. The bars show its "
                    "confidence in each option.")
        quiz_q = gr.State(None)
        with gr.Row():
            qset = gr.Dropdown(list(QUIZ_SETS), value=next(iter(QUIZ_SETS)), label="Question set", scale=3)
            qlvl = gr.Dropdown(["all", "easy", "medium", "hard"], value="all", label="Level", scale=1)
            qkb = gr.Dropdown(list(KBS), value=KB_DEFAULT, label="Knowledge base", scale=3)
        new_q = gr.Button("🎲 Random question")
        q_md = gr.Markdown()
        with gr.Row():
            ask_rag = gr.Button("Answer with RAG", variant="primary")
            ask_base = gr.Button("Answer without RAG")
        with gr.Row():
            probs = gr.Label(label="Model confidence per option", num_top_classes=6)
            verdict = gr.Markdown()
        q_ctx = gr.Markdown(elem_classes="passages")
        new_q.click(quiz_pick, [qset, qlvl], [quiz_q, q_md, probs, verdict, q_ctx])
        ask_rag.click(lambda q, b: quiz_answer(q, b, True), [quiz_q, qkb], [probs, verdict, q_ctx])
        ask_base.click(lambda q, b: quiz_answer(q, b, False), [quiz_q, qkb], [probs, verdict, q_ctx])

    with gr.Tab("🔎 Explorer"):
        gr.Markdown("Browse the saved benchmark runs: every model's answer to every question, and what retrieval found.")
        with gr.Row():
            set_dd = gr.Dropdown([(v, k_) for k_, v in SETS.items()], value="oranbench", label="Question set", scale=2)
            lvl_dd = gr.Dropdown(["all", "easy", "medium", "hard"], value="all", label="Level")
            out_dd = gr.Dropdown(OUTCOMES, value="all", label="Outcome", scale=2)
        with gr.Row():
            base_dd = gr.Dropdown([], label="Compare: base run")
            rag_dd = gr.Dropdown([], label="Compare: RAG run")
            ctxk = gr.Slider(1, 10, value=5, step=1, label="Passages to show")
        scores = gr.Markdown()
        count = gr.Markdown()
        with gr.Row():
            prev_b = gr.Button("◀ Previous", scale=0)
            q_dd = gr.Dropdown([], label="Question", scale=5)
            next_b = gr.Button("Next ▶", scale=0)
        ex_md = gr.Markdown()
        ex_ctx = gr.Markdown(elem_classes="passages")
        filt, fouts = [set_dd, lvl_dd, out_dd, base_dd, rag_dd], [scores, base_dd, rag_dd, q_dd, count]
        for c in (set_dd, lvl_dd, out_dd):
            c.change(refresh, filt, fouts)
        for c in (base_dd, rag_dd):
            c.input(refresh, filt, fouts)
        q_dd.change(show, [set_dd, q_dd, ctxk], [ex_md, ex_ctx])
        ctxk.change(show, [set_dd, q_dd, ctxk], [ex_md, ex_ctx])
        prev_b.click(lambda *a: step(-1, *a), filt + [q_dd], q_dd)
        next_b.click(lambda *a: step(+1, *a), filt + [q_dd], q_dd)

    with gr.Tab("📊 Results"):
        res_md = gr.Markdown(bench_results_md())
        gr.Markdown("---\n## Task A: base LLM vs RAG on our own question sets (judged by Phi-4)")
        ta = gr.Dropdown(list(TASK_A), value=next(iter(TASK_A)), label="Question set")
        ta_md = gr.Markdown(task_a_md(next(iter(TASK_A))))
        ta.change(task_a_md, ta, ta_md)

    with gr.Tab("ℹ️ About"):
        gr.Markdown(ABOUT)

    demo.load(refresh, filt, fouts)
    demo.load(bench_results_md, None, res_md)

if __name__ == "__main__":
    threading.Thread(target=_warmup, daemon=True).start()
    demo.queue(default_concurrency_limit=1).launch(server_name="0.0.0.0", server_port=7860,
                                                   theme=gr.themes.Soft(primary_hue="indigo"), css=CSS)

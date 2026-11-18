"""Task B1 demo on the final system (166 specs, 800-token chunks, dense + reranker, top-5), via the running web app's API.
Usage: python bench/b1_demo_final.py  (app must be running)  -> results/taskB1_demo_final.md"""
import re
from gradio_client import Client
QUERIES = [
    "How does an xApp subscribe to E2 Node data, and what happens in the Near-RT RIC platform?",
    "What is the difference between the Non-RT RIC and the Near-RT RIC in terms of control loop timing and interfaces?",
    "What is A1 enrichment information and who provides it?",
    "In the O-RAN AI/ML workflow, what are the ML training host and the ML inference host, and where can they be deployed?",
    "What does the O-RAN Z7 interface connect, and which working group specifies it?",   # does not exist -> must decline
]
KB = "Full O-RAN corpus: 166 specs"
c = Client("http://localhost:7860/", verbose=False)
txt = lambda m: m if isinstance(m, str) else "".join(p.get("text", "") for p in m) if isinstance(m, list) else str(m)
out = ["# Task B1: spec Q&A assistant with citations (final system)\n",
       "Knowledge base: 166 O-RAN specs, 12,042 chunks (800 tokens, 15% overlap) · retrieval: bge-m3 top-30 → "
       "bge-reranker-v2-m3 → top-5 · generator: Qwen2.5-7B-Instruct\n"]
for i, q in enumerate(QUERIES, 1):
    hist, ctx, base, _ = c.predict(q, [], KB, 5, True, api_name="/chat")
    ans = txt(hist[-1]["content"])
    cited = sorted({int(n) for n in re.findall(r"\[(\d+)\]", ans)})
    srcs = re.findall(r"\*\*\[(\d+)\] (.+?)\*\*\s*\n_(.+?)_ · relevance ([\d.]+)", ctx)
    out += [f"## Demo {i}: {q}\n", "**RAG answer:**\n", ans, "\n**Cited sources:**\n"]
    out += [f"- [{n}] `{s}`, {loc} (relevance {sc})" for n, s, loc, sc in srcs if int(n) in cited] or \
           ["- _(no citations: the assistant declined)_"]
    out += ["\n**Same model without RAG:**\n", re.sub(r"^### .*\n_.*_\n\n", "", base), ""]
    print(f"done {i}", flush=True)
open("results/taskB1_demo_final.md", "w").write("\n".join(out) + "\n")

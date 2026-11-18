"""Part 2 Task B1: Spec Q&A assistant with citations - demo queries.

Usage: python demo_b1.py   -> prints and saves results/taskB1_demo.md
Each answer lists the cited passages (source document + page/section) so every claim can be checked.
Query 5 is deliberately out of scope, to show the assistant refuses instead of hallucinating.
"""
import re, textwrap
from rag import RAG

QUERIES = [
    "How does an xApp subscribe to E2 Node data, and what happens in the Near-RT RIC platform?",
    "What is the difference between the Non-RT RIC and the Near-RT RIC in terms of control loop timing and interfaces?",
    "What is A1 enrichment information and who provides it?",
    "In the O-RAN AI/ML workflow, what are the ML training host and the ML inference host, and where can they be deployed?",
    "What is the maximum transmit power of an O-RU in the 3.5 GHz band?",   # out of scope -> should refuse
]

rag = RAG()
out = ["# Task B1 - Spec Q&A assistant with citations\n",
       f"Index: {rag.index.ntotal} chunks · retrieval: bge-m3 -> bge-reranker-v2-m3 (top-5) · generator: Qwen2.5-7B-Instruct\n"]
for i, q in enumerate(QUERIES, 1):
    ans, hits = rag.answer_rag(q, 5)
    cited = sorted({int(n) for n in re.findall(r"\[(\d+)\]", ans)})
    out += [f"## Demo {i}: {q}\n", "**Answer:**\n", ans, "\n**Cited sources:**\n"]
    for h in hits:
        if h["rank"] in cited:
            out.append(f"- [{h['rank']}] `{h['source']}` - {h['loc']}  \n  > {textwrap.shorten(h['text'], 250)}")
    if not cited:
        out.append("- _(no citations - answer declined or not grounded)_")
    out.append("")
    print(f"done {i}/{len(QUERIES)}")

open("results/taskB1_demo.md", "w").write("\n".join(out) + "\n")
print("\n".join(out))

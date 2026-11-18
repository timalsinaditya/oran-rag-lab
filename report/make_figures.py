"""Figures for the report: fig1_architecture.png, fig2_rag_effect.png, fig3_oranbench.png (300 dpi)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = os.path.dirname(os.path.abspath(__file__))
NAVY, BLUE, GREEN, ORANGE, GREY = "#1f2d3d", "#dceaff", "#e2f4e6", "#ffe6c7", "#ececec"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})


# ------------------------------------------------------------------ Figure 1: architecture
def box(ax, x, y, w, h, title, sub="", fill=BLUE, cyl=False):
    if cyl:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.35",
                                    fc=fill, ec=NAVY, lw=1.2))
    else:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                    fc=fill, ec=NAVY, lw=1.2))
    nt, ns = title.count("\n") + 1, (sub.count("\n") + 1) if sub else 0
    block = nt * 0.30 + (0.12 + ns * 0.25 if sub else 0)          # stack title + sub, centred in the box
    top = y + h / 2 + block / 2
    ax.text(x + w / 2, top, title, ha="center", va="top", fontsize=9.2, fontweight="bold", color=NAVY,
            linespacing=1.1)
    if sub:
        ax.text(x + w / 2, top - nt * 0.30 - 0.12, sub, ha="center", va="top", fontsize=7.4, color="#33475b",
                linespacing=1.3)
    return (x, y, w, h)


def arrow(ax, a, b, label="", dotted=False, side="h"):
    (x1, y1, w1, h1), (x2, y2, w2, h2) = a, b
    if side == "h":
        p, q = (x1 + w1, y1 + h1 / 2), (x2, y2 + h2 / 2)
    else:  # vertical, from bottom of a to top of b
        p, q = (x1 + w1 / 2, y1), (x2 + w2 / 2, y2 + h2)
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=12, lw=1.3, color=NAVY,
                                 linestyle=(0, (2, 2)) if dotted else "-"))
    if label:
        ax.text((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 - 0.3, label, ha="center", va="top", fontsize=7.4,
                color=NAVY, style="italic")


fig, ax = plt.subplots(figsize=(13, 5.6))
ax.set_xlim(0, 16.2); ax.set_ylim(0, 7); ax.axis("off")
ax.text(8.1, 6.75, "O-RAN RAG Assistant: System Architecture", ha="center", fontsize=13, fontweight="bold",
        color=NAVY)
ax.plot([0.2, 16.0], [3.55, 3.55], ls="--", color="#9aa7b4", lw=1)
ax.text(0.2, 6.25, "OFFLINE: build the knowledge base (once)", fontsize=9, fontweight="bold", color="#3a5f8f")
ax.text(0.2, 3.2, "ONLINE: answer a question (per query)", fontsize=9, fontweight="bold", color="#2f6b45")

# offline lane
y, h = 4.25, 1.55
d = box(ax, 0.2, y, 2.6, h, "O-RAN ALLIANCE\nspecifications", "166 specs · all WGs\nPDF & DOCX · latest only")
p = box(ax, 3.3, y, 2.7, h, "Parse & clean", "page / section locations\ndrop TOC, boilerplate\ndrop ASN.1 listings")
c = box(ax, 6.5, y, 2.0, h, "Chunk", "800 tokens\n15% overlap")
e = box(ax, 9.0, y, 2.2, h, "Embed", "BAAI/bge-m3", fill=ORANGE)
f = box(ax, 11.7, y, 2.6, h, "FAISS index", "cosine similarity\n12,042 chunks", fill=GREY, cyl=True)
for a, b in ((d, p), (p, c), (c, e), (e, f)):
    arrow(ax, a, b)

# online lane
y2, h2 = 0.95, 1.9
q = box(ax, 0.2, y2, 2.3, h2, "User question", "\"What does the A1\ninterface do?\"", fill=GREEN)
qe = box(ax, 2.9, y2, 2.0, h2, "Embed question", "BAAI/bge-m3", fill=ORANGE)
ds = box(ax, 5.3, y2, 2.1, h2, "Dense search", "top-30\ncandidates", fill=GREEN)
r = box(ax, 7.8, y2, 2.4, h2, "Cross-encoder\nreranker", "bge-reranker-v2-m3\n+ spec-name boost", fill=ORANGE)
l = box(ax, 11.3, y2, 2.5, h2, "LLM", "Qwen2.5-7B-Instruct\nanswer only from passages\ncite [n] · else decline",
        fill=ORANGE)
a_ = box(ax, 14.2, y2, 1.85, h2, "Grounded\nanswer", "with [n] citations\n+ spec / page", fill=GREEN)
for a, b in ((q, qe), (qe, ds), (ds, r)):
    arrow(ax, a, b)
arrow(ax, r, l, "top-5\npassages")
arrow(ax, l, a_)
arrow(ax, f, ds, dotted=True, side="v")
ax.text(13.2, 3.75, "nearest-neighbour\nsearch over the index", fontsize=7.2, color="#55606b", style="italic",
        va="center")
ax.text(16.0, 0.15, "Hardware: 1× NVIDIA L4 (24 GB)", ha="right", fontsize=7.5, color="#6b7680")
fig.savefig(f"{OUT}/fig1_architecture.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

# ------------------------------------------------------------------ Figure 2: when RAG helps / hurts
q_labels = ["lowest 25%", "25–50%", "50–75%", "highest 25%"]
eff29 = [-1.9, -1.1, 1.3, 12.0]
efffull = [9.6, 15.7, 19.5, 18.7]
fig, ax = plt.subplots(figsize=(6.6, 3.4))
xs = range(4); wd = 0.38
b1 = ax.bar([x - wd / 2 for x in xs], eff29, wd, label="29 documents (our sample)", color="#9db4cf", ec=NAVY, lw=.6)
b2 = ax.bar([x + wd / 2 for x in xs], efffull, wd, label="166 specs (official set)", color="#2f5d8a", ec=NAVY, lw=.6)
for bars in (b1, b2):
    for bar in bars:
        v = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, v + (0.5 if v >= 0 else -1.4), f"{v:+.1f}", ha="center",
                fontsize=7.5, color=NAVY)
ax.axhline(0, color=NAVY, lw=.8)
ax.set_xticks(list(xs)); ax.set_xticklabels(q_labels)
ax.set_xlabel("Questions grouped by retrieval confidence (reranker score of the top passage)")
ax.set_ylabel("RAG − no RAG (accuracy points)")
ax.set_ylim(-4, 23)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False, fontsize=8, loc="upper left")
fig.tight_layout()
fig.savefig(f"{OUT}/fig2_rag_effect.png", dpi=300, facecolor="white")
plt.close(fig)

# ------------------------------------------------------------------ Figure 3: ORANBench comparison
systems = ["Tele-LLM", "TSpec-LLM", "NVIDIA O-RAN", "Ours: 7B, no RAG", "ORANSight-2.0\nGemma-2 27B + rerank",
           "Ours: 7B + RAG\n(166 specs)", "ORANSight-2.0 best\n(32B + RAG)"]
avg = [0.573, 0.647, 0.826, 0.721, 0.880, 0.879, 0.889]
colors = ["#c9d2dc"] * 3 + ["#9db4cf", "#c9d2dc", "#2f5d8a", "#c9d2dc"]
fig, ax = plt.subplots(figsize=(6.8, 3.5))
bars = ax.barh(range(len(systems)), avg, color=colors, ec=NAVY, lw=.6)
for b, v in zip(bars, avg):
    ax.text(v + 0.006, b.get_y() + b.get_height() / 2, f"{v:.3f}", va="center", fontsize=8, color=NAVY)
ax.set_yticks(range(len(systems))); ax.set_yticklabels(systems, fontsize=8)
ax.set_xlim(0.5, 0.95); ax.set_xlabel("ORANBench average accuracy (easy / medium / hard)")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(f"{OUT}/fig3_oranbench.png", dpi=300, facecolor="white")
plt.close(fig)
print("saved fig1_architecture.png, fig2_rag_effect.png, fig3_oranbench.png")

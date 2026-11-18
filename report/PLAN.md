# Lab 2 report: paper-style plan

Working title: **"A 7B Open-Book Assistant for O-RAN: Retrieval-Augmented Generation over the Full O-RAN
Specification Corpus Approaches 32B State of the Art on ORAN-Bench-13K"**

Format: IEEE two-column style (conference template), ~6–8 pages + appendix. Write it tomorrow (2026-11-17).
Status legend: ✅ result exists · ⏳ running/queued · ☐ to do

---

## 1. Paper outline: what goes where

| § | Section | Content | Source files / numbers |
|---|---|---|---|
| — | Abstract | Problem, approach (RAG over full O-RAN spec corpus, 7B), headline: official ORANBench score vs ORANSight-2.0 0.889, NVIDIA-O-RAN 0.826; lab eval 90–96% vs 18–28% base | all below |
| I | Introduction | LLMs hallucinate on telecom specs; O-RAN specs are large, versioned, multi-WG; contributions list (4 bullets: pipeline, corpus, eval + analysis, UI/demo) | — |
| II | Related work | RAG; dense retrieval + rerankers; telecom LLMs (Tele-LLMs, TSpec-LLM, NVIDIA-O-RAN, ORANSight 1/2); benchmarks (ORAN-Bench-13K, ORANBench); LLM-as-judge; distracting context | refs §3 |
| III | System design | Fig. 1 pipeline diagram; corpus (§III-A), parsing + chunking (§III-B), retrieval (§III-C), generation + prompts (§III-D), UI (§III-E). **Each design choice + its reason + citation** (table in §2 below) | `ingest.py`, `rag.py`, `app.py`, `catalog/` |
| IV | Experimental setup | Hardware (1× NVIDIA L4 24 GB); models; Part-2 Task A question sets (25 original + 25 diverse, qtypes); judge (phi-4 4-bit, different family); ORAN-Bench protocol (official ORANBench 1,500 + our seed-42 sample); logit scoring; fairness rules (papers excluded, leakage check, no-RAG baselines) | `eval/`, `bench/` |
| V-A | Results: lab evaluation (Task A) | Table: base vs RAG (accuracy, strict, grounding, citations, hit@5) for 8-doc / 29-doc × orig / diverse Qs; by qtype; ≥2 "base hallucinated, RAG correct" cases with cited passage (Q9, Q12, Q24 "Z-WG") | `results/v1_8docs/`, `results/v2_29docs_*` |
| V-B | Results: ORAN-Bench | **Main table** vs published (ORANSight-2.0 Table V/VI, NVIDIA, TSpec, Tele-LLM); corpus scaling 29 → 166 specs; model scaling 7B vs 32B no-RAG; chunking/k/hybrid ablation | `bench/runs/`, `run_bench.py score` |
| V-C | Analysis | When RAG helps/hurts (fixed vs broke, by reranker-score quartile; gating experiment); hard-question error analysis (retrieval miss vs reading error); option-position bias check; retrieval confidence 29 vs full corpus | analysis scripts (to save) |
| V-D | Task B1 demo | 3–5 spec Q&A with citations, incl. one correct refusal | `results/taskB1_demo.md` (re-run ☐) |
| V-E | Task C (optional) | QLoRA fine-tune: base vs RAG vs FT (vs FT+RAG) | ☐ |
| VI | Discussion & limitations | 7B ≈ 32B because open-book; benchmark generated from the same specs; different sample ⇒ use official set; scoring method differences; energy/latency (2.6 s/q rerank) | — |
| VII | Conclusion | — | — |
| App. | Appendix | Prompts; spec list (166, with versions); UI screenshots; example explorer pages; judge overrides with reasons | `docs_full/`, `catalog/latest.csv` |

### Figures / tables to produce
- ☐ Fig. 1 pipeline diagram (ingest → FAISS + BM25 → reranker → 7B → answer w/ citations)
- ☐ Fig. 2 UI screenshot (Ask tab) + Fig. 3 explorer screenshot
- ☐ Fig. 4 accuracy by level for: 7B base, 7B+RAG29, 32B base, 7B+RAG full, ORANSight best (bar chart)
- ☐ Fig. 5 RAG − base by reranker-score quartile (the "RAG hurts when retrieval misses" plot)
- ✅/⏳ Table: main ORAN-Bench results; Table: ablations; Table: lab eval metrics

---

## 2. Design choices: why + reference (for §III)

| Choice | What we did | Why | Ref |
|---|---|---|---|
| RAG instead of (only) fine-tuning | retrieve spec passages, condition the LLM | grounding, citations, updatable corpus, less hallucination | [Lewis20], [Gao23-survey] |
| Corpus | 166 latest-version O-RAN specs (WG1–WG11, TIFG), deduplicated by (release, version); papers excluded | benchmark questions are generated from specs; stale duplicates crowd top-k | [ORAN-Bench], O-RAN specs |
| Parsing | PDF per line w/ page loc; DOCX per paragraph/table w/ section loc; TOC, boilerplate, ASN.1/YANG dropped; (v2) header/footer + line-number strip | citations need page/section; noise pollutes retrieval; ORANSight notes uniform splitting is a limitation | [ORANSight2 §VI] |
| Chunk size | 800 tok / 120 overlap (15%); v2 400/60 | handout 500–1000 & 10–20%; smaller chunks = more precise for fact questions; reranker 1,024-token limit (10% of 800-tok chunks truncated) | [Handout], [BGE-M3] |
| Contextual chunk header (v2) | prefix `[spec | section]` | chunks lose their document context; prefix restores it for embedder + reranker | [Anthropic24-contextual] |
| Embedder | BAAI/bge-m3 (1024-d, 8k ctx) | strong open retriever, long context so chunks are not truncated | [BGE-M3] |
| Vector store | FAISS IndexFlatIP on normalized vectors (= cosine), exact search | 12–28k vectors: exact search is milliseconds, no ANN error | [FAISS] |
| Two-stage retrieval | dense top-30 → cross-encoder reranker → top-k | bi-encoder is fast but coarse; cross-encoder reads query+passage jointly; ORANSight App. D shows reranker +12.8 pts | [Nogueira19], [ORANSight2 App. D], [Jacob24] |
| Reranker | BAAI/bge-reranker-v2-m3 | same family as embedder; same model class ORANSight used | [BGE-M3], [C-Pack] |
| Hybrid (exp.) | + BM25 top-30 before reranking (bm25s) | exact identifiers (T2a_min_cp_dl, PRACH) are weak in dense space | [Robertson09], [Ma21-hybrid], [bm25s] |
| Query | question + options | options carry the discriminating terms | (ours; ablation ☐) |
| Spec-name boost | +0.2 if question names the spec | metadata routing for "in E2AP…" questions | (ours) |
| Generator | Qwen2.5-7B-Instruct bf16 (fits 24 GB with retriever) | strong open 7B; same family as ORANSight best (Qwen2.5-32B) → like-for-like | [Qwen2.5] |
| MCQ scoring | next-token logits over "1".."N", argmax | deterministic, no parsing failures; standard in MMLU-style eval | [Hendrycks21], [Robinson23] |
| Position-bias check | compare predicted vs gold option distribution | LLMs can prefer option positions | [Zheng24-MCQ], [Pezeshkpour24] |
| Distracting context analysis / gating | RAG vs base by reranker-score quartile; fall back to base below threshold | irrelevant context can mislead; adaptive retrieval | [Shi23], [Yoran24], [Mallen23], [Asai24-SelfRAG] |
| k (passages) | 5 (ablate 8) | more context ≠ better; models use middle of long contexts poorly | [Liu24-lost] |
| Judge (Task A) | microsoft/phi-4 4-bit, different family from generator; refusal = correct on unanswerable; manual overrides logged | LLM-as-judge agrees well with humans; self-preference bias → use other family | [Zheng23-judge], [Panickssery24], [Phi-4] |
| Fine-tune (Task C) | QLoRA on Qwen2.5-7B | fits 24 GB; ORANSight-2.0 also uses QLoRA | [Hu22-LoRA], [Dettmers23-QLoRA] |
| Fairness | exclude ORAN-Bench/ORANSight papers; verbatim-question leakage check (0/600); official ORANBench set; no-RAG baselines | avoid benchmark leakage, comparable protocol | [ORAN-Bench], [ORANSight2] |

---

## 3. References

**Verified** = checked against the ORANSight-2.0 PDF bibliography (`docs/ORANSight-2.0.pdf`) or the dataset card.
**Check** = from memory; confirm the venue/year/ID before submitting (Google Scholar / arXiv).

### Telecom / O-RAN (verified)
- [ORANSight2] P. Gajjar, V. K. Shah, "ORANSight-2.0: Foundational LLMs for O-RAN." (NC State NextG Wireless Lab; arXiv — check ID). Table V (main), Table VI + App. D (reranker), §VI limitations.
- [ORAN-Bench] P. Gajjar, V. K. Shah, "ORAN-Bench-13K: An open source benchmark for assessing LLMs in open radio access networks," arXiv:2407.06245, 2024.
- [ORANBench-HF] prnshv/ORANBench, Hugging Face dataset (1,500 Qs, 500/level, ORANSight-2.0 evaluation set), MIT license.
- [Tele-LLMs] A. Maatouk, K. C. Ampudia, R. Ying, L. Tassiulas, "Tele-LLMs: A series of specialized large language models for telecommunications," arXiv:2409.05314, 2024.
- [TSpec-LLM] R. Nikbakht, M. Benzaghta, G. Geraci, "TSpec-LLM: An open-source dataset for LLM understanding of 3GPP specifications," arXiv:2406.01768, 2024.
- [NVIDIA-ORAN] A. Canaveras et al., "Advanced RAG techniques for telco O-RAN specifications using NVIDIA NIM microservices," NVIDIA Technical Blog, Oct. 2024.
- [Bariah23] L. Bariah et al., "Large language models for telecom: The next big thing?," arXiv:2306.10249, 2023.
- [Maatouk25] A. Maatouk et al., "Large language models for telecom: Forthcoming impact on the industry," IEEE Communications Magazine, 63(1):62–68, 2025.
- [Fund-ORAN] N. D. Tripathi, V. K. Shah, *Fundamentals of O-RAN*, Wiley, 2025.
- O-RAN ALLIANCE specifications (cite each one used in examples with WG, name, release, version; full list in appendix from `catalog/latest.csv`).

### Retrieval / RAG
- [Lewis20] P. Lewis et al., "Retrieval-augmented generation for knowledge-intensive NLP tasks," NeurIPS 2020. (check)
- [Gao23-survey] Y. Gao et al., "Retrieval-augmented generation for large language models: A survey," arXiv:2312.10997, 2023. (check)
- [Karpukhin20] V. Karpukhin et al., "Dense passage retrieval for open-domain question answering," EMNLP 2020. (check)
- [BGE-M3] J. Chen, S. Xiao, P. Zhang, K. Luo, D. Lian, Z. Liu, "BGE M3-Embedding: Multi-lingual, multi-functionality, multi-granularity text embeddings through self-knowledge distillation," arXiv:2402.03216, 2024. (verified)
- [C-Pack] S. Xiao, Z. Liu, P. Zhang, N. Muennighoff, "C-Pack: Packaged resources to advance general Chinese embedding," 2023 (arXiv:2309.07597 — check). (verified title/authors)
- [Nogueira19] R. Nogueira, K. Cho, "Passage re-ranking with BERT," arXiv:1901.04085, 2019. (check)
- [Jacob24] M. Jacob et al., "Drowning in documents: Consequences of scaling reranker inference," arXiv:2411.11767, 2024. (verified)
- [FAISS] J. Johnson, M. Douze, H. Jégou, "Billion-scale similarity search with GPUs," IEEE Trans. Big Data, 2019; and/or M. Douze et al., "The Faiss library," arXiv:2401.08281, 2024. (check)
- [Robertson09] S. Robertson, H. Zaragoza, "The probabilistic relevance framework: BM25 and beyond," Foundations and Trends in IR, 2009. (check)
- [bm25s] X. H. Lù, "BM25S: Orders of magnitude faster lexical search via eager sparse scoring," arXiv:2407.03618, 2024. (check)
- [Ma21-hybrid] X. Ma et al., "A replication study of dense passage retriever," arXiv:2104.05740, 2021 (dense + BM25 hybrid gains). (check)
- [Anthropic24-contextual] Anthropic, "Introducing Contextual Retrieval," blog post, Sept. 2024 (chunk context prefixes). (check)
- [Liu24-lost] N. F. Liu et al., "Lost in the middle: How language models use long contexts," TACL 2024. (check)
- [Shi23] F. Shi et al., "Large language models can be easily distracted by irrelevant context," ICML 2023. (check)
- [Yoran24] O. Yoran et al., "Making retrieval-augmented language models robust to irrelevant context," ICLR 2024. (check)
- [Mallen23] A. Mallen et al., "When not to trust language models: Investigating effectiveness of parametric and non-parametric memories," ACL 2023 (adaptive retrieval). (check)
- [Asai24-SelfRAG] A. Asai et al., "Self-RAG: Learning to retrieve, generate, and critique through self-reflection," ICLR 2024. (check)

### Models
- [Qwen2.5] Qwen Team (A. Yang et al.), "Qwen2.5 technical report," arXiv:2412.15115, 2024. (verified)
- [Phi-4] M. Abdin et al., "Phi-4 technical report," arXiv:2412.08905, 2024. (check)
- [Gemma2] Gemma Team, "Gemma 2: Improving open language models at a practical size," arXiv:2408.00118, 2024. (verified; for the comparison row)

### Evaluation
- [Hendrycks21] D. Hendrycks et al., "Measuring massive multitask language understanding," ICLR 2021. (check)
- [Robinson23] J. Robinson, D. Wingate, "Leveraging large language models for multiple choice question answering," ICLR 2023. (check)
- [Zheng24-MCQ] C. Zheng et al., "Large language models are not robust multiple choice selectors," ICLR 2024. (check)
- [Pezeshkpour24] P. Pezeshkpour, E. Hruschka, "Large language models sensitivity to the order of options in multiple-choice questions," Findings of NAACL 2024. (check)
- [Zheng23-judge] L. Zheng et al., "Judging LLM-as-a-judge with MT-Bench and Chatbot Arena," NeurIPS 2023 Datasets & Benchmarks. (check)
- [Panickssery24] A. Panickssery, S. Bowman, S. Feng, "LLM evaluators recognize and favor their own generations," NeurIPS 2024. (check)

### Fine-tuning (Task C)
- [Hu22-LoRA] E. J. Hu et al., "LoRA: Low-rank adaptation of large language models," ICLR 2022. (check)
- [Dettmers23-QLoRA] T. Dettmers, A. Pagnoni, A. Holtzman, L. Zettlemoyer, "QLoRA: Efficient finetuning of quantized LLMs," NeurIPS 2023. (verified)

---

## 4. Facts about ORANSight-2.0 to state correctly (from the PDF)
- Eval set "ORANBench": 500 random per level from ORAN-Bench-13K (13,952 Qs in paper; GitHub now 13,819) → published as prnshv/ORANBench (we use it).
- Standard RAG: FAISS + **bge-large-en-v1.5**, specs + srsRAN code, **88,808 chunks**, recursive splitter (uniform, structure-agnostic — they list this as a limitation).
- Reranker variant (App. D, Table VI): 35 candidates → **BGE-M3 reranker** → top 5, on *fine-tuned* ORANSight Gemma-2 27B: 0.747 → 0.880.
- Best ORANBench: Qwen2.5-32B-based ORANSight + RAG, 0.904 / 0.884 / 0.878, avg 0.889. Hardware: RTX 4090 24 GB.
- Our differences to state: stock (not fine-tuned) 7B; bge-m3 embedder; reranker on every query; 166 latest specs only, no code; logit scoring.

---

## 5. Results inventory (fill tables from these)

| Result | Status | Where |
|---|---|---|
| Part 1 smoke tests, chunk count, baseline | ✅ | `results/part1_*.txt` |
| Task A, 8 docs, original 25 Qs (RAG 96% vs base 26%) | ✅ | `results/v1_8docs/` |
| Task A, 29 docs, original Qs (96% vs 28%) | ✅ | `results/v2_29docs_origQ/` |
| Task A, 29 docs, diverse Qs (90% vs 18%) | ✅ | `results/v2_29docs_diverseQ/` |
| Task B1 demo (5 queries) | ✅ old / ☐ re-run on bigger index + new out-of-scope Q | `results/taskB1_demo.md`, `demo_b1.py` |
| ORAN-Bench, our sample_500: 7B base 0.713, 7B+RAG29 0.739, 32B base 0.763, **7B+RAG full 0.872** | ✅ | `bench/runs/sample_500__*` |
| ORAN-Bench, official ORANBench: 7B+RAG full, 7B base | ⏳ ~21:30 Nov 16 | `bench/runs/oranbench__*` |
| Ablation (600 subset): v2 chunks k=5/k=8, hybrid k=5/k=8 | ⏳ ~23:30 Nov 16 | `bench/runs/tune_200__*` |
| RAG helps/hurts analysis + gating (29 docs) | ✅ numbers in chat → ☐ save as script + table | ☐ `bench/analysis.py` |
| Leakage check (0/600 verbatim) | ✅ → ☐ save as script | ☐ `bench/analysis.py` |
| Hard-question error analysis | ☐ | ☐ |
| UI screenshots (Ask + explorer) | ☐ (Ask tab needs free GPU) | `app.py` |
| Task C QLoRA | ☐ optional | — |
| 32B + RAG full on official set | ☐ optional | — |

## 6. Tomorrow's order of work
1. Read overnight results; pick best config (ablation); if a variant wins >3 pts on 600 → confirm on official ORANBench.
2. Save analyses as `bench/analysis.py` (fixed/broke, quartiles, gating, leakage, position bias, hard-question errors).
3. UI screenshots (GPU free) + re-run B1 demo on `index_full`.
4. Figures (pipeline diagram, bar chart, quartile plot).
5. Write the paper sections in the order: III → IV → V → II → I → VI/VII → Abstract.
6. Optional: Task C QLoRA; 32B + RAG on official set.

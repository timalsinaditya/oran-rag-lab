"""Part 1 (c,d,f): RAG chain + no-RAG baseline.

Usage:
  python rag.py "What does the A1 interface do?"          # RAG answer + retrieved passages + baseline
  python rag.py -k 8 "List the E2AP services."
"""
import json, argparse, textwrap, re, os
import faiss, torch
from sentence_transformers import SentenceTransformer, CrossEncoder
from transformers import AutoTokenizer, AutoModelForCausalLM

INDEX_DIR = "index"
EMBED_MODEL = "BAAI/bge-m3"
RERANK_MODEL = "BAAI/bge-reranker-v2-m3"  # cross-encoder reranker
CANDIDATES = 30                           # dense-retrieval candidates passed to the reranker
SPEC_BOOST = 0.2                          # added to reranker score (0-1) for chunks from a spec named in the query


def spec_code(source):
    """Full spec name from the file name, e.g.
    'O-RAN.WG3.TS.E2AP-R005-v09.00.docx' -> 'E2AP', 'O-RAN.WG3.TS.E2SM-KPM-R005-v08.00.docx' -> 'E2SM-KPM',
    'O-RAN.WG2.TS.Non-RT-RIC-ARCH-R004-v07.00.docx' -> 'NON-RT-RIC-ARCH'.  Non-spec files (papers) -> None."""
    m = re.match(r"O-RAN\.WG\d+\.(?:TS\.|TR\.)?(.+?)(?:\.0)?(?:-R\d{3})?-v\d", source)
    return m.group(1).upper() if m else None


def _norm(text):
    return " " + " ".join(re.findall(r"[A-Z0-9]+", text.upper())) + " "


def spec_mentioned(source, query):
    """True if the question names this chunk's spec, matched as a whole phrase so common words never match:
    'E2AP' in 'List the E2AP services'; 'E2SM-KPM' in '... in E2SM-KPM?'.
    Interface names map to their General Aspects & Principles spec (A1 -> A1GAP, Y1 -> Y1GAP, O2 -> O2-GA&P),
    and 'M-Plane' maps to the WG4 MP spec."""
    code = spec_code(source)
    if not code:
        return False
    q = _norm(query)
    if _norm(code) in q:
        return True
    compact = re.sub(r"[^A-Z0-9]", "", code)
    if compact.endswith("GAP") and re.fullmatch(r"[A-Z]\d", compact[:-3]):
        return f" {compact[:-3]} " in q
    return code == "MP" and " M PLANE " in q


LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"   # ~15 GB in bf16, fits the 24 GB L4

RAG_SYSTEM = ("You are an O-RAN expert assistant. Answer the question using ONLY the numbered "
              "context passages below. Cite every claim with the passage number(s) like [1] or [2][3]. "
              "If the context does not contain the answer, say \"The provided documents do not cover this.\" "
              "Do not use outside knowledge.")
BASE_SYSTEM = "You are an O-RAN expert assistant. Answer the question concisely."


class RAG:
    def __init__(self, llm_model=LLM_MODEL, load_llm=True, index_dir=INDEX_DIR):
        self._indexes = {}
        self.use_index(index_dir)
        self.embedder = SentenceTransformer(EMBED_MODEL, device="cuda")
        self.reranker = CrossEncoder(RERANK_MODEL, device="cuda", max_length=1024)
        if load_llm:
            self.tok = AutoTokenizer.from_pretrained(llm_model)
            self.llm = AutoModelForCausalLM.from_pretrained(llm_model, dtype=torch.bfloat16,
                                                            device_map="cuda")

    def use_index(self, index_dir):
        """Switch knowledge base (FAISS + chunks + BM25) without reloading the models; indexes are cached."""
        if index_dir not in self._indexes:
            self._indexes[index_dir] = dict(index=faiss.read_index(f"{index_dir}/faiss.index"),
                                            chunks=json.load(open(f"{index_dir}/chunks.json")), bm25=None)
        if getattr(self, "index_dir", None) in self._indexes:
            self._indexes[self.index_dir]["bm25"] = self.bm25          # keep a BM25 built for the old index
        d = self._indexes[index_dir]
        self.index_dir, self.index, self.chunks, self.bm25 = index_dir, d["index"], d["chunks"], d["bm25"]

    def _bm25(self):
        """Keyword index over the same chunks (built once, cached next to the FAISS index)."""
        import bm25s
        if self.bm25 is None:
            path = f"{self.index_dir}/bm25"
            if os.path.exists(path):
                self.bm25 = bm25s.BM25.load(path)
            else:
                self.bm25 = bm25s.BM25()
                self.bm25.index(bm25s.tokenize([c["text"] for c in self.chunks], stopwords="en", show_progress=False),
                                show_progress=False)
                self.bm25.save(path)
        return self.bm25

    def retrieve(self, query, k=5, rerank=True, exclude=(), hybrid=False):
        """Stage 1: dense search (bge-m3) for top-N candidates (+ BM25 keyword top-N if hybrid: catches exact
        spec terms like 'T2a_min_cp_dl' or 'PRACH' that dense embeddings blur).
        Stage 2: cross-encoder reranker reads (query, passage) pairs jointly and keeps the best k.
        exclude: source-file prefixes to never return (e.g. the benchmark's own paper, to avoid leakage)."""
        import bm25s
        q = self.embedder.encode([query], normalize_embeddings=True).astype("float32")
        scores, ids = self.index.search(q, CANDIDATES if rerank else k)
        pool = {int(i): float(s) for s, i in zip(scores[0], ids[0])}
        if hybrid:
            bids, _ = self._bm25().retrieve(bm25s.tokenize([query], stopwords="en", show_progress=False),
                                            k=CANDIDATES, show_progress=False)
            for i in bids[0]:
                pool.setdefault(int(i), float("nan"))      # keyword-only hit: no dense score
        cands = [dict(self.chunks[i], dense_score=s) for i, s in pool.items()
                 if not any(self.chunks[i]["source"].startswith(e) for e in exclude)]
        if rerank:
            rs = self.reranker.predict([(query, c["text"]) for c in cands], batch_size=8)
            for c, s in zip(cands, rs):
                # metadata boost: the question names a spec (e.g. "E2AP") -> prefer chunks from that spec
                c["score"] = float(s) + (SPEC_BOOST if spec_mentioned(c["source"], query) else 0.0)
            cands = sorted(cands, key=lambda c: -c["score"])[:k]
        else:
            for c in cands:
                c["score"] = c["dense_score"]
        for r, c in enumerate(cands):
            c["rank"] = r + 1
        return cands

    @torch.no_grad()
    def generate(self, system, user, max_new_tokens=512):
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        prompt = self.tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
        enc = self.tok(prompt, return_tensors="pt").to("cuda")
        out = self.llm.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False,
                                pad_token_id=self.tok.eos_token_id)
        return self.tok.decode(out[0, enc["input_ids"].shape[1]:], skip_special_tokens=True).strip()

    def answer_rag(self, query, k=5, hybrid=False):
        hits = self.retrieve(query, k, hybrid=hybrid)
        ans = self.generate(RAG_SYSTEM, self.rag_prompt(query, hits))
        return ans, hits

    @staticmethod
    def rag_prompt(query, hits):
        ctx = "\n\n".join(f"[{h['rank']}] (source: {h['source']}, {h['loc']})\n{h['text']}" for h in hits)
        return f"Context:\n{ctx}\n\nQuestion: {query}"

    def stream(self, system, user, history=(), max_new_tokens=512):
        """Generate token by token (for the chat UI). history = [(user_msg, assistant_msg), ...] earlier turns."""
        from threading import Thread
        from transformers import TextIteratorStreamer
        msgs = [{"role": "system", "content": system}]
        for u, a in history:
            msgs += [{"role": "user", "content": u}, {"role": "assistant", "content": a}]
        msgs.append({"role": "user", "content": user})
        prompt = self.tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
        enc = self.tok(prompt, return_tensors="pt").to("cuda")
        streamer = TextIteratorStreamer(self.tok, skip_prompt=True, skip_special_tokens=True)
        Thread(target=self.llm.generate, kwargs=dict(**enc, streamer=streamer, max_new_tokens=max_new_tokens,
                                                     do_sample=False, pad_token_id=self.tok.eos_token_id)).start()
        text = ""
        for piece in streamer:
            text += piece
            yield text

    def answer_base(self, query):
        return self.generate(BASE_SYSTEM, query)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--no-baseline", action="store_true")
    a = ap.parse_args()

    rag = RAG()
    print(f"Index: {rag.index.ntotal} chunks\n")
    ans, hits = rag.answer_rag(a.question, a.k)
    print("=" * 80, f"\nTOP-{a.k} RETRIEVED PASSAGES\n" + "=" * 80)
    for h in hits:
        print(f"[{h['rank']}] score={h['score']:.3f}  {h['source']}  {h['loc']}")
        print(textwrap.indent(textwrap.shorten(h["text"], 300), "    "))
    print("=" * 80, "\nRAG ANSWER\n" + "=" * 80 + f"\n{ans}\n")
    if not a.no_baseline:
        print("=" * 80, "\nNO-RAG BASELINE ANSWER\n" + "=" * 80 + f"\n{rag.answer_base(a.question)}\n")


if __name__ == "__main__":
    main()

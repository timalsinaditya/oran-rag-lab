"""Part 1 (a,b): load PDFs/DOCX from docs/, chunk (800 tokens, 15% overlap), embed, store in FAISS.

Usage:  python ingest.py
Output: index/faiss.index  +  index/chunks.json (text + source + location metadata)
  - PDF chunks are located by page   ("p.4" or "p.4-5")
  - DOCX chunks are located by section heading ("§5.3 A1 interface"), since Word files have no pages
"""
import json, os, glob, re
import faiss, tiktoken
from pypdf import PdfReader
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from sentence_transformers import SentenceTransformer

DOCS_DIR = os.environ.get("DOCS_DIR", "docs")        # e.g. DOCS_DIR=docs_full INDEX_DIR=index_full python ingest.py
INDEX_DIR = os.environ.get("INDEX_DIR", "index")
CHUNK_TOKENS, OVERLAP = 800, 120          # 120/800 = 15% overlap
EMBED_MODEL = "BAAI/bge-m3"               # 8k-token context, so 800-token chunks are not truncated

enc = tiktoken.get_encoding("cl100k_base")


def pdf_units(path):
    """Yield (text, location) per page."""
    for pno, page in enumerate(PdfReader(path).pages, start=1):
        text = page.extract_text() or ""
        # drop table-of-contents lines ("5.1 E2 interface ........ 9") - they pollute retrieval
        text = "\n".join(l for l in text.splitlines() if not re.search(r"\.{5,}|…{3,}", l))
        yield text, f"p.{pno}"


def docx_units(path):
    """Yield (text, location) per paragraph/table, location = most recent heading."""
    doc, heading = Document(path), "front matter"
    for el in doc.element.body.iterchildren():
        tag = el.tag.split("}")[-1]
        if tag == "p":
            p = Paragraph(el, doc)
            text, style = p.text.strip(), (p.style.name if p.style is not None else "")
            if not text or style.lower().startswith("toc"):
                continue                                   # skip empty lines and table of contents
            if style.lower().startswith("heading"):
                heading = text[:80]
            yield text, f"§{heading}"
        elif tag == "tbl":
            rows = [" | ".join(c.text.strip() for c in r.cells) for r in Table(el, doc).rows]
            yield "\n".join(rows), f"§{heading}"


BOILERPLATE = re.compile(r"front matter|list of (figures|tables)|foreword|references|"
                         r"specification notations|revision history|copyright|introduction$", re.I)


def is_noise(text, loc_start, loc_end):
    """Drop chunks that hurt retrieval: spec boilerplate sections and ASN.1 code listings."""
    if BOILERPLATE.search(loc_start) and BOILERPLATE.search(loc_end):
        return True
    if text.count("::=") >= 3 or text.count("PROTOCOL-IES") + text.count("CRITICALITY") >= 6:
        return True                                     # ASN.1 definitions
    return False


def chunk(units, source):
    """Concatenate units as tokens (remembering each token's location), then slide a window."""
    toks, locs = [], []
    for text, loc in units:
        t = enc.encode(text + "\n")
        toks += t
        locs += [loc] * len(t)
    out, step = [], CHUNK_TOKENS - OVERLAP
    for start in range(0, max(len(toks) - OVERLAP, 1), step):
        end = min(start + CHUNK_TOKENS, len(toks))
        text = enc.decode(toks[start:end]).strip()
        if len(text) < 50:
            continue
        if is_noise(text, locs[start], locs[end - 1]):
            continue
        l0, l1 = locs[start], locs[end - 1]
        if l0 == l1:
            loc = l0
        elif l0.startswith("p.") and l1.startswith("p."):
            loc = f"{l0}-{l1[2:]}"
        else:
            loc = f"{l0} … {l1}"
        out.append({"source": source, "loc": loc, "n_tokens": end - start, "text": text})
    return out


def main():
    chunks = []
    files = sorted(glob.glob(f"{DOCS_DIR}/**/*.pdf", recursive=True) +
                   glob.glob(f"{DOCS_DIR}/**/*.docx", recursive=True))
    for f in files:
        try:
            units = pdf_units(f) if f.lower().endswith(".pdf") else docx_units(f)
        except Exception as e:                      # one unreadable file must not kill a long run
            print(f"SKIPPED {os.path.basename(f)}: {type(e).__name__}: {e}")
            continue
        c = chunk(units, os.path.basename(f))
        print(f"{os.path.basename(f):60s} {len(c):5d} chunks")
        chunks += c
    print(f"\nTOTAL CHUNKS INDEXED: {len(chunks)}")

    model = SentenceTransformer(EMBED_MODEL, device="cuda")
    emb = model.encode([c["text"] for c in chunks], batch_size=16, show_progress_bar=True,
                       normalize_embeddings=True).astype("float32")
    index = faiss.IndexFlatIP(emb.shape[1])   # cosine similarity (vectors are normalized)
    index.add(emb)

    os.makedirs(INDEX_DIR, exist_ok=True)
    faiss.write_index(index, f"{INDEX_DIR}/faiss.index")
    json.dump(chunks, open(f"{INDEX_DIR}/chunks.json", "w"), indent=1)
    print(f"Saved {index.ntotal} vectors (dim={emb.shape[1]}) to {INDEX_DIR}/")


if __name__ == "__main__":
    main()

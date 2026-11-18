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
CHUNK_TOKENS = int(os.environ.get("CHUNK_TOKENS", 800))   # default 800 / 120 = 15% overlap (lab index)
OVERLAP = int(os.environ.get("OVERLAP", 120))
STRIP_HF = os.environ.get("STRIP_HF") == "1"     # drop PDF page headers/footers repeated on many pages
PREFIX = os.environ.get("PREFIX") == "1"         # prepend "[spec | section]" to each chunk (helps embed + rerank)
EMBED_MODEL = "BAAI/bge-m3"               # 8k-token context, so 800-token chunks are not truncated

enc = tiktoken.get_encoding("cl100k_base")


PDF_HEADING = re.compile(r"^(?:\d+(?:\.\d+){0,5}|Annex [A-Z](?:\.\d+)*)\.?\s+[A-Z][A-Za-z0-9 ,/&()\-–']{2,90}$")


PDF_BOILER_HEADING = re.compile(r"^(?:Annex [A-Z]?\s*\(informative\)\s*:?\s*)?(?:Revision|Change|Document) [Hh]istory\b.*$"
                                r"|^(?:\d+(?:\.\d+)?\s+)?(?:Foreword|References|Normative references|Informative references"
                                r"|Modal verbs terminology|Copyright Notice)\s*$")


def _hf_key(line):
    return re.sub(r"\d+", "#", line.strip().lower())   # "Page 12 of 300" == "Page 13 of 300"


def _strip_line_numbers(lines):
    """Some specs (e.g. WG9) print a line number at the end of every line: 'IPSEC or not. 20'.
    Walk the page looking for the running sequence 1, 2, 3, ... at line ends and strip only those numbers;
    applied only if the run reaches 8, so numbers that belong to the text or tables are kept."""
    out, expect, hits = [], 1, []
    for i, l in enumerate(lines):
        m = re.search(r"(?:^|\s)(\d{1,3})\s*$", l)
        if m and int(m.group(1)) == expect:
            hits.append((i, m.start())); expect += 1
    if expect <= 8:
        return lines
    out = list(lines)
    for i, pos in hits:
        out[i] = lines[i][:pos]
    return out


def pdf_units(path):
    """Yield (text, location, section) per line; location = page, section = last detected heading."""
    pages = [(p.extract_text() or "").splitlines() for p in PdfReader(path).pages]
    common = set()
    if STRIP_HF and len(pages) >= 4:
        from collections import Counter
        cnt = Counter(k for ls in pages for k in {_hf_key(l) for l in ls[:3] + ls[-3:] if l.strip()})
        common = {k for k, n in cnt.items() if n >= 0.3 * len(pages)}   # on >=30% of pages = header/footer
    pages = [_strip_line_numbers(ls) for ls in pages]
    section = ""
    for pno, lines in enumerate(pages, start=1):
        for i, l in enumerate(lines):
            if re.search(r"\.{5,}|…{3,}", l):          # table-of-contents lines ("5.1 E2 interface ..... 9")
                continue
            if common and (i < 3 or i >= len(lines) - 3) and _hf_key(l) in common:
                continue
            t = l.strip()
            if (PDF_HEADING.match(t) and not re.search(r"\d\s*$", t)) or PDF_BOILER_HEADING.match(t):
                section = " ".join(t.split())[:80]
            yield l, f"p.{pno}", section


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
                heading = " ".join(text.split())[:80]
            yield text, f"§{heading}", heading
        elif tag == "tbl":
            rows = [" | ".join(c.text.strip() for c in r.cells) for r in Table(el, doc).rows]
            yield "\n".join(rows), f"§{heading}", heading


BOILERPLATE = re.compile(r"front matter|list of (figures|tables)|foreword|references|"
                         r"specification notations|revision history|change history|document history|copyright|"
                         r"modal verbs|introduction$", re.I)


def is_noise(text, loc_start, loc_end):
    """Drop chunks that hurt retrieval: spec boilerplate sections and ASN.1 code listings."""
    if BOILERPLATE.search(loc_start) and BOILERPLATE.search(loc_end):
        return True
    if text.count("::=") >= 3 or text.count("PROTOCOL-IES") + text.count("CRITICALITY") >= 6:
        return True                                     # ASN.1 definitions
    return False


def chunk(units, source):
    """Concatenate units as tokens (remembering each token's location), then slide a window."""
    toks, locs, secs = [], [], []
    for text, loc, sec in units:
        t = enc.encode(text + "\n")
        toks += t
        locs += [loc] * len(t)
        secs += [sec] * len(t)
    spec = re.sub(r"(-R\d{3})?[-_ ]v\d+\.\d+.*$", "", os.path.splitext(source)[0])
    out, step = [], CHUNK_TOKENS - OVERLAP
    for start in range(0, max(len(toks) - OVERLAP, 1), step):
        end = min(start + CHUNK_TOKENS, len(toks))
        text = enc.decode(toks[start:end]).strip()
        if len(text) < 50:
            continue
        if is_noise(text, locs[start], locs[end - 1]):
            continue
        l0, l1 = locs[start], locs[end - 1]
        if STRIP_HF and BOILERPLATE.search(secs[start] or "-") and BOILERPLATE.search(secs[end - 1] or "-"):
            continue                                # PDF boilerplate sections (detected headings)
        if l0 == l1:
            loc = l0
        elif l0.startswith("p.") and l1.startswith("p."):
            loc = f"{l0}-{l1[2:]}"
        else:
            loc = f"{l0} … {l1}"
        if PREFIX:
            text = f"[{spec} | {secs[start] or loc}]\n{text}"
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

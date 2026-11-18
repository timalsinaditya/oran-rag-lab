"""Pick the latest version of every O-RAN spec in catalog.csv.

Usage: python dedupe.py [--wg WG1,WG2,WG3] [--all-types]
Output: latest.csv (one row per spec: newest release/version) and a summary per working group.

Normalisation (so different versions of one spec group together):
  "2019.09.30-ORAN-WG2.A1GAP_v01.00.pdf", "O-RAN.WG2.A1GAP-v02.02.pdf", "O-RAN.WG2.TS.A1GAP-R005-v05.04.pdf"
   -> key "WG2-A1GAP"; ordered by (release R00x, version vXX.YY[.ZZ]).
By default only .pdf/.docx are kept (zip = YANG/ASN.1 models, xlsx = annex tables).
"""
import csv, re, sys, argparse
from collections import defaultdict

ap = argparse.ArgumentParser()
ap.add_argument("--wg", help="comma list, e.g. WG1,WG2,WG3")
ap.add_argument("--all-types", action="store_true")
a = ap.parse_args()


# Old / misspelled names of specs that were later renamed (found by reviewing latest.csv)
ALIASES = {
    "WG2-A1GANP": "WG2-A1GAP",                                  # 2019 file name typo
    "WG2-R1-GAP": "WG2-R1GAP",
    "WG2-R1-USE-CASES-AND-REQUIREMENTS": "WG2-R1UCR",
    "WG2-USECASEREQUIREMENTS": "WG2-USE-CASE-REQUIREMENTS",
}


def parse(fn):
    name = fn.strip().strip('"').strip()
    m = re.match(r"(.*)\.([A-Za-z0-9]+)$", name)
    stem, ext = (m.group(1).strip(), m.group(2).lower()) if m else (name, "")
    stem = re.sub(r"^\d{4}[.-]\d{2}[.-]\d{2}[-_ ]*", "", stem)                     # leading date
    vm = list(re.finditer(r"[-_ .]v(\d+)\.(\d+)(?:\.(\d+))?", stem, re.I))
    ver = tuple(int(x or 0) for x in vm[-1].groups()) if vm else (0, 0, 0)
    if vm:
        stem = stem[:vm[-1].start()]
    rm = re.search(r"[-_ .]R(\d{3})\b", stem)
    rel = int(rm.group(1)) if rm else 0
    if rm:
        stem = stem[:rm.start()] + stem[rm.end():]
    s = re.sub(r"^(O-RAN|ORAN)[.\-_ ]*", "", stem, flags=re.I)                     # O-RAN. / ORAN- / O-RAN-
    s = re.sub(r"(?<=[.\-_ ])(TS|TR)(?=[.\-_ ]|$)", "", s)                          # .TS. / -TR markers
    s = re.sub(r"\.0$", "", s.strip())                                              # MP.0 == MP
    key = re.sub(r"[.\-_ ]+", "-", s).strip("-").upper()
    key = ALIASES.get(key, key)
    wg = (re.match(r"(WG\d+|TIFG|SFG|TIFG|[A-Z]+)", key) or [None])[0] if key else None
    return dict(key=key, wg=wg, rel=rel, ver=ver, ext=ext, name=name)


rows = [r for r in csv.DictReader(open("catalog.csv")) if r["status"] == "200" and r["filename"]]
groups = defaultdict(list)
for r in rows:
    p = parse(r["filename"])
    if not a.all_types and p["ext"] not in ("pdf", "docx"):
        continue
    if a.wg and p["wg"] not in a.wg.upper().split(","):
        continue
    groups[p["key"]].append(dict(p, id=int(r["id"]), bytes=r["bytes"]))

latest = []
for key, vs in groups.items():
    # newest release, then version; same version in pdf & docx -> prefer pdf (page numbers for citations)
    best = max(vs, key=lambda v: (v["rel"], v["ver"], v["ext"] == "pdf"))
    latest.append(dict(best, n_versions=len(vs), older_ids=" ".join(str(v["id"]) for v in vs if v is not best)))
latest.sort(key=lambda v: (v["wg"] or "", v["key"]))

with open("latest.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["key", "wg", "id", "filename", "release", "version", "bytes", "n_versions", "older_ids"])
    for v in latest:
        w.writerow([v["key"], v["wg"], v["id"], v["name"], f"R{v['rel']:03d}" if v["rel"] else "",
                    "v" + ".".join(f"{x:02d}" for x in v["ver"]), v["bytes"], v["n_versions"], v["older_ids"]])

by_wg = defaultdict(lambda: [0, 0, 0])
for v in latest:
    by_wg[v["wg"]][0] += 1; by_wg[v["wg"]][1] += v["n_versions"]; by_wg[v["wg"]][2] += int(v["bytes"] or 0)
print(f"{len(rows)} files in catalog -> {sum(len(g) for g in groups.values())} pdf/docx kept -> {len(latest)} unique specs (latest only)\n")
print(f"{'group':8s} {'specs':>6s} {'versions':>9s} {'latest MB':>10s}")
for wg, (n, nv, b) in sorted(by_wg.items(), key=lambda t: str(t[0])):
    print(f"{str(wg):8s} {n:6d} {nv:9d} {b/1e6:10.1f}")
print("\nsaved latest.csv")

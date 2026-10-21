"""E2E: both modes on the locked Capital Prep master. Checks every content slot filled and every label unchanged."""
import os, re, sys, subprocess, zipfile, hashlib
os.environ.setdefault("LP_DB", "/tmp/test_capprep.db")
from docx import Document
from core import engine, capprep, store, pdfio, template, llm
os.makedirs("samples/output", exist_ok=True)

def labels(doc_bytes_or_path):
    d = Document(doc_bytes_or_path) if isinstance(doc_bytes_or_path, str) else Document(__import__("io").BytesIO(doc_bytes_or_path))
    out = []
    def runs(p): return [r.text for r in p.runs if r.bold and r.text.strip()]
    for p in d.paragraphs: out += runs(p)
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs: out += runs(p)
    return out
def media_hashes(b):
    z = zipfile.ZipFile(b if isinstance(b, str) else __import__("io").BytesIO(b))
    return {n: hashlib.md5(z.read(n)).hexdigest() for n in z.namelist() if n.startswith("word/media") or "header" in n or n == "word/styles.xml"}

master_labels = labels(capprep.MASTER); master_media = media_hashes(capprep.MASTER)
store.seed_samples(os.getcwd())
past = store.search("anyone", "Mutations")[0][4]
assert "Natural Selection" in past, "sample past lesson missing"
for mode in ("new", "experienced"):
    ctx = dict(topic="Natural Selection & Adaptations", subject="Science", grade="8", minutes=40, teacher="Ms. Rivera",
               date="10/14/2026", week_of="10/13/26", standards="MS-LS3-1\nMS-LS4-4", day=1, days=1,
               past_lesson=past if mode == "experienced" else "")
    content, out = engine.run_capprep(mode, ctx)
    fn = f"samples/output/capprep_{mode}.docx"; open(fn, "wb").write(out)
    txt = template.doc_text(out) + "\n" + "\n".join(p.text for p in Document(fn).paragraphs)
    missing = [k for k in capprep.FIELDS if content.get(k) and str(content[k]).split("\n")[0].lstrip("•- ")[:18] not in txt]
    # labels: bold text in the output must contain the master's bold labels in order (date/times are content)
    norm = lambda L: [re.sub(r"\d+[^ ]*", "#", x).strip() for x in L]
    ol = norm(labels(out)); ml = norm(master_labels)
    from collections import Counter
    oc = Counter(ol); lost = [l for l in ml if not (oc[l] > 0 or l.startswith("Week of:"))]
    for l in ml: oc[l] -= 1
    week_ok = all(k in Document(fn).paragraphs[0].text for k in ("Week of:", "Subject:", "Illuminator:"))
    om = media_hashes(out); diff = [k for k in master_media if master_media[k] != om.get(k)]
    same_media = not diff or print("changed parts:", diff)
    print(f"{mode}: fields filled {len(capprep.FIELDS)-len(missing)}/{len(capprep.FIELDS)} missing={missing} labels_lost={lost} logo/header/styles identical={same_media}")
    assert not missing and not lost and week_ok and same_media
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", "samples/output", fn], capture_output=True)
    subprocess.run(["pdftoppm", "-r", "80", "-png", fn.replace(".docx", ".pdf"), fn.replace(".docx", "")])

# ---- structural invariance: all non-content XML of the master must be unchanged in the output
from lxml import etree
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
def struct(path):
    z = zipfile.ZipFile(path); root = etree.fromstring(z.read("word/document.xml"))
    ser = lambda e: etree.tostring(e)
    out = {"sectPr": [ser(e) for e in root.iter(W + "sectPr")],
           "tblPr/grid/trPr/tcPr": [ser(e) for tag in ("tblPr", "tblGrid", "trPr", "tcPr") for e in root.iter(W + tag)],
           "drawings": [ser(e) for e in root.iter(W + "drawing")]}
    # every master paragraph (label or empty slot) keeps its pPr; label runs keep text + rPr
    paras = []
    for p in root.iter(W + "p"):
        txt = "".join(t.text or "" for t in p.iter(W + "t"))
        if txt.strip():
            ppr = p.find(W + "pPr"); runs = [(ser(r.find(W + "rPr")) if r.find(W + "rPr") is not None else b"", "".join(t.text or "" for t in r.iter(W + "t"))) for r in p.findall(W + "r")]
            paras.append((ser(ppr) if ppr is not None else b"", runs))
    return out, paras
EDITABLE = re.compile(r"(\d+/\d+/\d+|\d+ [Mm]inutes|Week of:|Illuminator: |Grade|Illuminator will launch)")
ms, mp = struct(capprep.MASTER)
for mode in ("new", "experienced"):
    os_, op = struct(f"samples/output/capprep_{mode}.docx")
    for k in ms: assert ms[k] == os_[k], f"{mode}: {k} changed"
    opset = {(a, tuple(b)) for a, b in op}; olabels = [(a, r) for a, b in op for r in b]
    bad = []
    for ppr, runs in mp:
        if EDITABLE.search("".join(t for _, t in runs)): continue
        if (ppr, tuple(runs)) in opset: continue
        # label paragraph may have content appended (e.g. 'Level 1: ' + text): label runs must be a prefix
        if any(a == ppr and tuple(b[:len(runs)])[:-1] == tuple(runs)[:-1] for a, b in op): continue
        bad.append("".join(t for _, t in runs)[:40])
    print(f"{mode}: section/table/cell/drawing XML identical; label paragraphs changed: {bad}")
    assert not bad
print("ALL OK")

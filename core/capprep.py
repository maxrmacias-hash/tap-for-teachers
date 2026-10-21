"""Locked Capital Prep Bronx master template (templates/capprep_master.docx).

The school's original DOCX is filled IN PLACE: logo/header, styles, fonts, colors, tables, labels
and wording are never changed. Content is written only into the empty content slots that follow
each label (cloning that slot's paragraph + run formatting). The IP Coaching / Scholar Grouping /
IEP tables are deliberately left blank (student data, no PII)."""
import copy, io, os, re
from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

MASTER = os.path.join(os.path.dirname(__file__), "..", "templates", "capprep_master.docx")
NAME = "Capital Prep Bronx (official template)"

# id -> description used for generation
FIELDS = {
 "week_of": "VERY SHORT, max 8 chars, e.g. '10/13/26'", "subject": "VERY SHORT, max 9 chars, e.g. 'Science'",
 "illuminator": "teacher name, max 12 chars, e.g. 'Ms. Rivera'", "date": "MM/DD/YYYY",
 "topic": "lesson topic / unit-phase title", "standards": "NGSS codes, one per line (e.g. MS-LS3-1)",
 "learner_expectations": "1-2 sentences starting 'Scholars will…'",
 "objective": "SWBAT: 'Scholars will be able to … because they can … (standard code).'",
 "know": "bullets: what scholars will know", "able_to_do": "bullets: what scholars should be able to do",
 "donow_time": "minutes for Do Now/Engage (number)", "donow_entry": "Entry / hook task bullets",
 "donow_prior": "Prior knowledge activation bullets", "donow_groupings": "groupings + voice level, e.g. 'Independent → turn-and-talk. Voice Level 0 → 1.'",
 "donow_mods": "Level 1 / Level 2 / Level 3 modifications for Do Now (lines starting 'Level 1:' etc.)",
 "mini_time": "minutes for Mini-Lesson (number)", "mini_activity": "Mini-lesson Activity/Task: Illuminator models… numbered steps",
 "mini_transition": "transition sentence to scholar work time", "mini_level1": "Level 1 supports", "mini_level2": "Level 2 (standard) and stretch",
 "scw_time": "minutes for Scholar-Centered Work (number)", "scw_activity": "Scholar-centered task steps incl. groupings + voice level",
 "scw_level3": "Level 3 question + supports", "vocabulary": "key terms separated by ' • '",
 "cfu_questions": "numbered check-for-understanding questions", "cfu_criteria": "criteria for success bullets",
 "differentiation": "differentiation strategies bullets (incl. extension)", "tlac": "Teach Like a Champion strategies bullets",
 "exit_time": "minutes for Exit Ticket (number)", "exit_activity": "exit ticket task", "exit_groupings": "e.g. 'Individual, silent. Voice Level 0.'",
 "exit_mods": "success criteria / modifications for exit ticket",
 "p5_objectives": "objective restated for coaching page", "p5_skills": "skills being taught (bullets)",
 "ip_grade": "grade, e.g. '8'",
}
VOCAB = ("School vocabulary (Capital Preparatory Bronx Charter School): teachers are 'Illuminators', students are "
 "'Scholars'. Objectives are written SWBAT style ('Scholars will be able to … because they can …'). Always state "
 "voice levels (Voice Level 0 silent, 1 whisper/partner, 2 group, 3 presenter). Differentiate as Level 1 "
 "(sentence starters, word banks, visuals), Level 2 (standard), Level 3 (stretch/extension). Cite NGSS codes "
 "(e.g. MS-LS3-1) for science. Use TLAC strategies (Cold Call, Turn and Talk, Right is Right, Stretch It, Circulate). "
 "ALWAYS build in Pauker Writing (Dr. Robert Pauker's Structured Writing & Thinking Program): (1) Quick Picture - scholars visualize/sketch the core image of the idea (in the Do Now or mini-lesson); (2) Area of Focus - one main idea per paragraph based on the Quick Picture; (3) Guide Questions - lesson-specific questions scholars answer to draft an analytical paragraph; (4) Elaboration - evaluate and add evidence/explanation. The Illuminator models a Pauker paragraph in the Mini-Lesson; Scholar-Centered Work ends with a Pauker analytical paragraph answering the lesson question with lesson-specific Guide Questions; the exit ticket is a short Pauker paragraph or the Elaboration step. Supports: Level 1 paragraph frame with Guide Questions + sentence starters, Level 2 standard, Level 3 elaborate with additional evidence/counterexample. List 'Pauker Writing (Structured Writing & Thinking)' in skills. "
 "Never include student names. Do not write section labels; write only the content for each field.")

# Length budget so a filled plan stays at the master's 5 pages (max lines, max chars per line).
MASTER_PAGES = 5
BUDGET = {k: (1, 110) for k in FIELDS}
BUDGET.update({"standards": (2, 20), "objective": (1, 170), "learner_expectations": (1, 130),
  "donow_entry": (1, 140), "donow_mods": (3, 60), "mini_activity": (4, 90), "mini_level2": (2, 70),
  "scw_activity": (1, 300), "scw_level3": (2, 70), "cfu_questions": (2, 80), "exit_activity": (1, 140),
  "vocabulary": (1, 100), "differentiation": (1, 140)})
BUDGET_TEXT = ("LENGTH BUDGET (the filled plan must stay at the master's 5 pages): keep every value concise; "
  + "; ".join(f"{k} <= {n} line(s) x {c} chars" for k, (n, c) in BUDGET.items())
  + ". Merge short items with ' • ' instead of new lines.")

def enforce_budget(content):
    """Hard cap: keep at most the budgeted number of lines per field (lines beyond are merged with ' • ')."""
    out = {}
    for k, v in content.items():
        n = BUDGET.get(k, (1, 200))[0]; lines = [l for l in str(v).split("\n") if l.strip()]
        if len(lines) > n: lines = lines[:n - 1] + [" • ".join(x.strip().lstrip("•- ") for x in lines[n - 1:])]
        out[k] = "\n".join(lines)
    return out

def page_count(docx_bytes):
    """Pages when rendered by LibreOffice (None if unavailable)."""
    import subprocess, tempfile, os, re
    with tempfile.TemporaryDirectory() as td:
        fn = os.path.join(td, "p.docx"); open(fn, "wb").write(docx_bytes)
        try:
            subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", td, fn], capture_output=True, timeout=90)
            info = subprocess.run(["pdfinfo", fn[:-5] + ".pdf"], capture_output=True, text=True).stdout
            m = re.search(r"Pages:\s+(\d+)", info); return int(m.group(1)) if m else None
        except Exception:
            return None

def is_capprep(name_or_bytes):
    return name_or_bytes == "capprep"

def _num(p): return p._p.pPr is not None and p._p.pPr.numPr is not None
def _empty(p): return not p.text.strip() and not p._p.xpath(".//w:drawing")

def _set_text(p, text, bullet_slot):
    """Write text into paragraph p keeping its first run's formatting (bold removed for content)."""
    runs = p.runs
    if runs:
        r0 = runs[0]
        for r in runs[1:]: r._r.getparent().remove(r._r)
    else:
        r0 = p.add_run()
        mark = p._p.pPr.find(qn("w:rPr")) if p._p.pPr is not None else None
        if mark is not None:
            rpr = r0._r.get_or_add_rPr()
            for ch in mark:
                if ch.tag not in (qn("w:b"), qn("w:bCs"), qn("w:rtl")): rpr.append(copy.deepcopy(ch))
    is_bullet = bool(re.match(r"^\s*[-•*]\s+", text))
    if is_bullet or bullet_slot: text = re.sub(r"^\s*(?:[-•*]\s+)", "", text)
    if is_bullet and not _num(p):
        # reuse the template's own list formatting: the bullet list used in this cell (else this table)
        tc = p._p.xpath("ancestor::w:tc[1]"); tbl = p._p.xpath("ancestor::w:tbl[last()]")
        proto = None
        for scope in (tc, tbl):
            if scope:
                found = [n for n in scope[0].xpath(".//w:p/w:pPr/w:numPr") if n.getparent().getparent() is not p._p]
                if found: proto = found[0]; break
        if proto is not None:
            ppr = p._p.get_or_add_pPr(); ppr.insert(1 if ppr.find(qn("w:pStyle")) is not None else 0, copy.deepcopy(proto))
    r0.text = text; r0.bold = None if not (r0._r.rPr is not None and r0._r.rPr.find(qn("w:b")) is not None) else False

def _clone_after(p, remove_num=False):
    new = copy.deepcopy(p._p)
    p._p.addnext(new); np_ = Paragraph(new, p._parent)
    if remove_num and new.pPr is not None and new.pPr.numPr is not None: new.pPr.remove(new.pPr.numPr)
    return np_

def _fill_after(anchor, text, content_rpr_from=None):
    """Fill consecutive empty slot paragraphs after anchor, then clone the last slot for extra lines."""
    lines = [l for l in str(text).split("\n") if l.strip()]
    if not lines: return
    slots, nxt = [], anchor._p.getnext()
    while nxt is not None and nxt.tag == qn("w:p"):
        par = Paragraph(nxt, anchor._parent)
        if not _empty(par): break
        slots.append(par); nxt = nxt.getnext()
    # keep one blank spacer before the next label if the template had spare slots
    usable = slots[:-1] if len(slots) > len(lines) and len(slots) > 1 else slots
    last = anchor
    for i, line in enumerate(lines):
        if i < len(usable):
            par = usable[i]
        else:
            src = usable[-1] if usable else anchor
            par = _clone_after(last if i else src, remove_num=not usable)
            if not usable and i == 0:
                for r in par.runs[1:]: r._r.getparent().remove(r._r)
        _set_text(par, line, _num(par)); last = par
        if not usable: usable_guard = None

def _append_inline(p, label_run_idx, value):
    """Insert value as a new run right after run[label_run_idx], cloning that run's formatting."""
    r = p.runs[label_run_idx]; new = copy.deepcopy(r._r); r._r.addnext(new)
    from docx.text.run import Run
    nr = Run(new, p); nr.text = value
    return nr

def _replace_in_run(p, pattern, repl):
    for r in p.runs:
        if re.search(pattern, r.text): r.text = re.sub(pattern, repl, r.text, count=1); return True
    return False

def _cell(t, r, c): return t.cell(r, c)
def _para(cell, startswith):
    for p in cell.paragraphs:
        if p.text.strip().startswith(startswith): return p
    raise KeyError(startswith)

def populate(content: dict, master_path=MASTER) -> bytes:
    d = Document(master_path); c = {k: (str(v) if v is not None else "") for k, v in content.items()}
    t = d.tables[0]
    # header line: single bold run 'Week of:\t\t\t     Subject: \t\t   ...   Illuminator:  '
    p0 = d.paragraphs[0]; r = p0.runs[0]
    txt = r.text
    # Master whitespace/tabs kept EXACTLY; each value is inserted right after its label (values must be short).
    for lab, key in (("Illuminator:", "illuminator"), ("Subject:", "subject"), ("Week of:", "week_of")):
        if c.get(key):
            v = c[key].strip()[:{"week_of": 8, "subject": 12, "illuminator": 16}[key]]
            i = txt.index(lab) + len(lab); txt = txt[:i] + " " + v + txt[i:]
    r.text = txt
    # top table
    _fill_after(_para(_cell(t, 0, 0), "Topic:"), c.get("topic", ""))
    _fill_after(_para(_cell(t, 0, 0), "Learner Expectation"), c.get("learner_expectations", ""))
    _fill_after(_para(_cell(t, 0, 0), "Objective:"), c.get("objective", ""))
    if c.get("date"): _replace_in_run(_para(_cell(t, 0, 3), "Date:"), r"\d{1,2}/\d{1,2}/\d{2,4}", c["date"])
    _fill_after(_para(_cell(t, 0, 4), "Standards:"), c.get("standards", ""))
    _fill_after(_para(_cell(t, 1, 3), "What students will know"), c.get("know", ""))
    _fill_after(_para(_cell(t, 1, 3), "What students should be able"), c.get("able_to_do", ""))
    # times in Section column (keep wording/format, swap the number)
    for (row, key) in ((3, "donow_time"), (4, "mini_time"), (5, "scw_time"), (10, "exit_time")):
        n = re.sub(r"\D", "", c.get(key, ""))
        if n:
            for p in _cell(t, row, 0).paragraphs:
                if _replace_in_run(p, r"\d+(?= [Mm]inutes)", n): break
    # Do Now
    cell = _cell(t, 3, 1)
    _fill_after(_para(cell, "Entry:"), c.get("donow_entry", ""))
    _fill_after(_para(cell, "Prior Knowledge"), c.get("donow_prior", ""))
    _fill_after(_para(cell, "Scholar Groupings"), c.get("donow_groupings", ""))
    mods = _cell(t, 3, 4); lines = [l for l in c.get("donow_mods", "").split("\n") if l.strip()]
    for p, l in zip(mods.paragraphs, lines): _set_text(p, l, False)
    if len(lines) > len(mods.paragraphs):
        _fill_after(mods.paragraphs[-1], "\n".join(lines[len(mods.paragraphs):]))
    # Mini-lesson: replace the sample sentence after 'Activity/Task: ' (run 1), more lines into slots
    cell = _cell(t, 4, 1); pa = _para(cell, "Activity/Task:"); al = [l for l in c.get("mini_activity", "").split("\n") if l.strip()]
    if al:
        pa.runs[1].text = al[0]
        for rr in pa.runs[2:]: rr.text = ""
        _fill_after(pa, "\n".join(al[1:]))
    _fill_after(_para(cell, "Transition to scholar"), c.get("mini_transition", ""))
    cell = _cell(t, 4, 4)
    p1 = _para(cell, "Level 1:"); 
    if c.get("mini_level1"): p1.runs[-1].text = " " + c["mini_level1"].split("\n")[0]; _fill_after(p1, "\n".join(c["mini_level1"].split("\n")[1:]))
    p2 = _para(cell, "Level 2:")
    if c.get("mini_level2"): _append_inline(p2, 0, " " + c["mini_level2"].split("\n")[0]); _clone_fill_tail(p2, c["mini_level2"].split("\n")[1:])
    # Scholar-centered work
    _fill_after(_para(_cell(t, 5, 1), "Activity/Task:"), c.get("scw_activity", ""))
    _fill_after(_para(_cell(t, 5, 4), "Level 3 question:"), c.get("scw_level3", ""))
    # merged rows
    v = _cell(t, 6, 1).paragraphs[0]
    if c.get("vocabulary"): _set_text(v, c["vocabulary"].replace("\n", " • "), False)
    _fill_after(_para(_cell(t, 7, 1), "Check For Understanding Questions"), c.get("cfu_questions", ""))
    _fill_after(_para(_cell(t, 7, 1), "Criteria for Success"), c.get("cfu_criteria", ""))
    _fill_after(_para(_cell(t, 8, 1), "Differentiation Strategies"), c.get("differentiation", ""))
    tl = _cell(t, 9, 1).paragraphs[0]; tll = [l for l in c.get("tlac", "").split("\n") if l.strip()]
    if tll: _set_text(tl, tll[0], True); _clone_fill_tail(tl, tll[1:])
    # Exit ticket
    cell = _cell(t, 10, 1)
    _fill_after(_para(cell, "Activity/Task:"), c.get("exit_activity", ""))
    pg = _para(cell, "Scholar Groupings")
    if c.get("exit_groupings"): _clone_fill_tail(pg, c["exit_groupings"].split("\n"), plain=True)
    em = _cell(t, 10, 4).paragraphs[0]; eml = [l for l in c.get("exit_mods", "").split("\n") if l.strip()]
    if eml: _set_text(em, eml[0], False); _clone_fill_tail(em, eml[1:])
    # IP coaching header: Illuminator / Grade only (no scholar data)
    p10 = [p for p in d.paragraphs if p.text.strip().startswith("Illuminator:") and "Grade" in p.text]
    if p10:
        p = p10[0]
        if c.get("ip_grade"): p.runs[3].text = ":  " + c["ip_grade"]
        if c.get("illuminator"): p.runs[1].text = " " + c["illuminator"] + "\t"
    # coaching page table
    t3 = d.tables[3]
    _clone_fill_tail(_para(_cell(t3, 0, 0), "Objectives:"), c.get("p5_objectives", "").split("\n"), plain=True)
    _fill_after(_para(_cell(t3, 1, 1), "What skills"), c.get("p5_skills", ""))
    _unique_para_ids(d.element)
    from lxml import etree
    body_xml = etree.tostring(d.element, encoding="UTF-8", xml_declaration=False)
    return _graft_document_xml(master_path, body_xml)

def _unique_para_ids(root):
    """Cloned paragraphs inherit w14:paraId/textId; Word requires them unique (duplicates trigger repair)."""
    W14 = "{http://schemas.microsoft.com/office/word/2010/wordml}"
    for attr in ("paraId", "textId"):
        seen, nxt = set(), 0x10000000
        for p in root.iter(qn("w:p")):
            v = p.get(W14 + attr)
            if v is None: continue
            if v in seen:
                while f"{nxt:08X}" in seen: nxt += 1
                v = f"{nxt:08X}"; p.set(W14 + attr, v); nxt += 1
            seen.add(v)

def _graft_document_xml(master_path, filled: bytes) -> bytes:
    """Byte-for-byte copy of every part of the school's original file (logo, header, styles, fonts,
    numbering, theme...), replacing ONLY word/document.xml with the filled body."""
    import zipfile
    master_doc = zipfile.ZipFile(master_path).read("word/document.xml")
    decl = master_doc[:master_doc.index(b"?>") + 2]          # keep the master's exact XML declaration
    new_doc = decl + filled
    buf = io.BytesIO()
    with zipfile.ZipFile(master_path) as src, zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            dst.writestr(info, new_doc if info.filename == "word/document.xml" else src.read(info.filename))
    return buf.getvalue()

def _clone_fill_tail(anchor, lines, plain=False):
    """Insert new paragraphs after anchor (no slots available), cloning anchor formatting, content not bold."""
    last = anchor
    for l in [x for x in lines if x.strip()]:
        np_ = _clone_after(last, remove_num=plain)
        for r in np_.runs[1:]: r._r.getparent().remove(r._r)
        _set_text(np_, l, _num(np_))
        if np_.runs: np_.runs[0].bold = False
        last = np_

def demo_content(ctx):
    topic = ctx.get("topic", "Topic"); subj = ctx.get("subject", "Science"); g = str(ctx.get("grade", "8"))
    m = int(ctx.get("minutes") or 40); past = ctx.get("past_lesson", "")
    tdn, tml, tet = max(4, m // 10), max(8, m // 5), max(8, m // 5); tsw = m - tdn - tml - tet
    std = ctx.get("standards") or "MS-LS3-1"
    d = {
     "week_of": ctx.get("week_of", ""), "subject": subj[:9],
     "illuminator": ctx.get("teacher", ""), "date": ctx.get("date", ""), "ip_grade": g,
     "topic": f"{topic}" + (f" – Day {ctx['day']} of {ctx['days']}" if ctx.get("days", 1) > 1 else ""),
     "standards": std, "learner_expectations": f"Scholars will explain the key ideas of {topic} and apply them to new examples.",
     "objective": f"Scholars will be able to explain {topic} because they can describe and give evidence for its key ideas ({std.splitlines()[0]}).",
     "know": f"• Key ideas and vocabulary of {topic}",
     "able_to_do": f"• Explain {topic} with evidence",
     "donow_time": tdn, "donow_entry": f"• Image hook + quick write: What do you know about {topic}?",
     "donow_prior": "• Quick recall of yesterday's key term", "donow_groupings": "• Independent → turn-and-talk. Voice Level 0 → 1.",
     "donow_mods": "Level 1: Sentence starters / word bank.\nLevel 2: Standard response.\nLevel 3: Connect to a real-world example.",
     "mini_time": tml, "mini_activity": f"Illuminator models the core idea of {topic}: revisit prior learning, one worked example, preview task.",
     "mini_transition": f"“You will now analyze {topic} with your partner.”",
     "mini_level1": "Visual supports + framed language.", "mini_level2": "Standard.",
     "scw_time": tsw, "scw_activity": f"• Pairs (Voice Level 1) read and annotate scenarios on {topic}, answer 2–3 questions.",
     "scw_level3": f"How would {topic} change in a new context? Supports: frames, chunked text.",
     "vocabulary": f"{topic} • evidence • claim • reasoning",
     "cfu_questions": f"1. What is the most important idea about {topic}?\n2. How do you know? Cite evidence.",
     "cfu_criteria": "• Clear claim supported by evidence and reasoning",
     "differentiation": "• Sentence frames • Word bank • Visuals • Extension: design a scenario",
     "tlac": "Cold Call • Turn and Talk • Right is Right / Stretch It • Circulate",
     "exit_time": tet, "exit_activity": f"• In 4–6 sentences, explain {topic} using an example.",
     "exit_groupings": "Individual, silent. Voice Level 0.",
     "exit_mods": f"Success Criteria: clear claim • scientific language • linked to {std.splitlines()[0]}",
     "p5_objectives": f"Scholars will be able to explain {topic}.", "p5_skills": "• Explaining with evidence",
    }
    if past: d["mini_activity"] += "\n(Adapted from your past lesson.)"
    for k, v in PAUKER_ADDONS.items(): d[k] = str(d[k]) + v
    return {k: str(v) for k, v in d.items()}

PAUKER_ADDONS = {   # appended on the same line to respect the length budget
 "donow_entry": " Pauker Quick Picture: sketch + label it.",
 "mini_activity": "\nPauker model: Quick Picture → Area of Focus → Guide Questions → paragraph → Elaboration.",
 "mini_level1": " Pauker frame + Guide Questions + starters.",
 "mini_level2": " L3: Elaborate with extra evidence/counterexample.",
 "scw_activity": " Then write a Pauker paragraph using the Guide Questions: What is it? What causes it? What effect? What evidence?",
 "cfu_criteria": " Pauker paragraph answers all Guide Questions.",
 "differentiation": " • Pauker: L1 frame + starters; L2 standard; L3 elaborate",
 "exit_activity": " Write it as a Pauker paragraph; Elaborate with one more piece of evidence.",
 "p5_skills": " • Pauker Writing (Structured Writing & Thinking)",
}

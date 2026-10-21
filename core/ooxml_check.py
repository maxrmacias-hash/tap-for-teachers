"""Lightweight OOXML sanity checks Word cares about: child order in pPr/rPr, duplicate paraIds."""
import zipfile, io, collections
from lxml import etree
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
W14 = "{http://schemas.microsoft.com/office/word/2010/wordml}"
PPR = ["pStyle","keepNext","keepLines","pageBreakBefore","framePr","widowControl","numPr","suppressLineNumbers","pBdr","shd","tabs",
       "suppressAutoHyphens","kinsoku","wordWrap","overflowPunct","topLinePunct","autoSpaceDE","autoSpaceDN","bidi","adjustRightInd",
       "snapToGrid","spacing","ind","contextualSpacing","mirrorIndents","suppressOverlap","jc","textDirection","textAlignment",
       "textboxTightWrap","outlineLvl","divId","cnfStyle","rPr","sectPr","pPrChange"]
RPR = ["rStyle","rFonts","b","bCs","i","iCs","caps","smallCaps","strike","dstrike","outline","shadow","emboss","imprint","noProof",
       "snapToGrid","vanish","webHidden","color","spacing","w","kern","position","sz","szCs","highlight","u","effect","bdr","shd",
       "fitText","vertAlign","rtl","cs","em","lang","eastAsianLayout","specVanish","oMath"]
def check(docx_bytes):
    root = etree.fromstring(zipfile.ZipFile(io.BytesIO(docx_bytes)).read("word/document.xml"))
    problems = []
    for tag, order in (("pPr", PPR), ("rPr", RPR)):
        for el in root.iter(W + tag):
            idx = [order.index(c.tag[len(W):]) for c in el if c.tag.startswith(W) and c.tag[len(W):] in order]
            if idx != sorted(idx): problems.append(f"{tag} order: {[c.tag[len(W):] for c in el]}")
    ids = collections.Counter(p.get(W14 + "paraId") for p in root.iter(W + "p") if p.get(W14 + "paraId"))
    d = [k for k, v in ids.items() if v > 1]
    if d: problems.append(f"duplicate w14:paraId x{len(d)}")
    return problems

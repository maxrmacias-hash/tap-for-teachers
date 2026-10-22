import os, datetime, json
import streamlit as st
from core import template, llm, store, engine

from PIL import Image
st.set_page_config(page_title="TAP for Teachers", page_icon=Image.open("assets/owl_face.png"), layout="wide")
st.markdown("""<style>.tap-sub{color:#1B2A4A;font-size:1.25rem;font-weight:600;margin-top:-0.8rem}
.tap-tag{display:inline-block;background:#F2B51C;color:#1B2A4A;padding:2px 10px;border-radius:8px;font-weight:600}
h1{color:#1B2A4A}
.tap-steps{border:2px solid #1B2A4A;border-radius:12px;padding:10px 14px;margin:10px 0 16px;background:#F7F9FC}
.tap-steps-h{color:#1B2A4A;font-weight:700;margin-bottom:6px}
.tap-step{display:inline-flex;align-items:center;gap:6px;margin:4px 14px 4px 0;color:#1B2A4A;font-size:0.95rem}
.tap-dot{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;font-weight:700;font-size:0.85rem}</style>""", unsafe_allow_html=True)
def header():
    st.title("TAP for Teachers")
    st.markdown('<div class="tap-sub">Teacher Assistant for Planning</div><span class="tap-tag">Less Planning. More Teaching.</span>', unsafe_allow_html=True)

STEPS=["Enter your invite code","Watch the short intro","Choose New or Experienced Teacher","Fill in your lesson details","Generate & review","Download your Word lesson plan"]
def steps(cur):
    items=""
    for i,t in enumerate(STEPS,1):
        if i<cur: bg,fg,mk="#1B4F9C","#fff","✓"
        elif i==cur: bg,fg,mk="#F2B51C","#1B2A4A",str(i)
        else: bg,fg,mk="#E6ECF5","#1B2A4A",str(i)
        w="700" if i==cur else "500"
        items+=f'<div class="tap-step"><span class="tap-dot" style="background:{bg};color:{fg}">{mk}</span><span style="font-weight:{w}">{t}</span></div>'
    st.markdown(f'<div class="tap-steps"><div class="tap-steps-h">Step {cur} of {len(STEPS)} &middot; How TAP works</div>{items}</div>', unsafe_allow_html=True)

# ---- pilot access gate (settings from st.secrets, falling back to environment variables)
from zoneinfo import ZoneInfo
def _cfg(key, default=""):
    try:
        if key in st.secrets: return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)
for _k in ("XAI_API_KEY", "LLM_MODEL", "LLM_BASE_URL"):
    if _cfg(_k) and not os.getenv(_k): os.environ[_k] = _cfg(_k)
codes = [c.strip().upper() for c in _cfg("ACCESS_CODES").split(",") if c.strip()]
exp = _cfg("PILOT_EXPIRES", "2026-11-15").strip()
def _ended():
    st.image("assets/hero.jpg", width=360); header()
    st.info("The TAP for Teachers pilot has ended. Thank you so much for planning with TAP! 🦉"); st.stop()
try:
    exp_date = datetime.date.fromisoformat(exp)
except ValueError:
    exp_date = None
if exp_date and datetime.datetime.now(ZoneInfo("America/New_York")).date() > exp_date: _ended()
if codes and not st.session_state.get("ok"):
    st.image("assets/hero.jpg", width=360); header(); steps(1)
    st.markdown("**Step 1:** Type the invite code you were given, then click **Enter**.")
    c = st.text_input("Invite code", placeholder="e.g. TAP-XXXX")
    if st.button("Enter"):
        if c.strip().upper() in codes: st.session_state.ok = True; st.rerun()
        else: st.error("That invite code isn't valid. Please check it and try again.")
    st.stop()

if not st.session_state.get("intro_seen"):
    header(); steps(2)
    st.markdown("<h2 style='text-align:center'>Welcome! Meet TAP 🦉</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center'><b>Step 2:</b> Watch this short intro (about 1½ minutes), then click <b>Let's get started</b>.</p>", unsafe_allow_html=True)
    _l, _m, _r = st.columns([1, 3, 1])
    with _m:
        if st.button("Let's get started", type="primary", width='stretch', key="start_top"):
            st.session_state.intro_seen = True; st.rerun()
        st.video("assets/intro.mp4")
        if st.button("Let's get started", type="primary", width='stretch', key="start_bottom"):
            st.session_state.intro_seen = True; st.rerun()
    st.stop()

prov = llm.get_provider()
header(); steps(3 if not st.session_state.get("outs") else 5)
st.caption("Upload your school's lesson-plan template → get it filled in → download.")
if isinstance(prov, llm.DemoProvider):
    st.warning("DEMO MODE: content is placeholder text so you can test the full flow.")
if exp_date: st.info(f"Pilot access through {exp_date.strftime('%B %d, %Y').replace(' 0', ' ')}")

with st.sidebar:
    st.image("assets/owl_face.png", width=120)
    teacher = st.text_input("Your name or nickname (used only to keep your library)", "teacher")
    style = st.text_area("Your preferences / style", store.get_pref(teacher))
    if st.button("Save preferences"): store.set_pref(teacher, style); st.toast("Saved")
    st.caption("Please don't enter student names or personal information.")

if not st.session_state.get("outs"):
    h1, h2 = st.columns([1, 1])
    h1.image("assets/hero.jpg")
    with h2:
        st.markdown("## Teachers Taking Back Control.")
        st.markdown("**Hi! I'm TAP!**")
        st.markdown("Teachers didn't become teachers to spend their evenings fighting lesson-plan templates. "
                    "TAP gives teachers back something incredibly valuable: **time**.")
        if st.button("▶ Watch the intro"):
            st.session_state.intro_seen = False; st.rerun()
        st.markdown('<span class="tap-tag">AI does the planning work. Teachers make the decisions.</span>', unsafe_allow_html=True)
if "mode" not in st.session_state: st.session_state.mode = "new"
st.markdown("### Step 3: Choose how you'd like to plan")
k1, k2 = st.columns(2)
with k1:
    st.image("assets/new_teacher_card.png", width='stretch')
    if st.button("I'm a New Teacher", width='stretch', type="primary" if st.session_state.mode=="new" else "secondary"):
        st.session_state.mode = "new"; st.rerun()
    st.caption("TAP provides a starting point when planning feels overwhelming.")
with k2:
    st.image("assets/experienced_teacher_card.png", width='stretch')
    if st.button("I'm an Experienced Teacher", width='stretch', type="primary" if st.session_state.mode=="experienced" else "secondary"):
        st.session_state.mode = "experienced"; st.rerun()
    st.caption("TAP turns years of knowledge, lessons, activities, and resources into a personal teaching library you can use again and again.")
mkey = st.session_state.mode
st.markdown("### Step 4: Fill in your lesson details below, then generate (Step 5) and download your Word plan (Step 6)")
st.markdown("#### " + ("New Teacher mode — I'll walk you through objectives, standards, differentiation, timing, exit ticket and tips." if mkey=="new" else "Experienced Teacher mode — reuse and adapt your past lessons, in your voice."))
ROOT = os.path.dirname(os.path.abspath(__file__))
store.seed_samples(ROOT)
from core import capprep, pdfio

st.markdown("### 1. Template")
st.success(f"🔒 Using **{capprep.NAME}**. Logo, layout, fonts and labels stay exactly as the school's original; only lesson content is filled in.")
other = st.checkbox("Advanced: use a different school's template instead (not recommended for Capital Prep)", value=False)
data = None; fields = None
if other:
    tpl = st.file_uploader("Upload a template (.docx, or .pdf to rebuild as an editable template — best effort)", type=["docx", "pdf"])
    if not tpl: st.stop()
    data = tpl.getvalue()
    if tpl.name.lower().endswith(".pdf"):
        data = pdfio.pdf_to_template(data)
        st.download_button("Download the rebuilt DOCX template", data, "rebuilt_template.docx")
    fields = template.detect_fields(template.load(data))
    with st.expander(f"Detected {len(fields)} sections"): st.write([f["label"] for f in fields])

st.markdown("### 2. Lesson details")
c1, c2, c3, c4 = st.columns(4)
topic = c1.text_input("Topic", "Natural Selection & Adaptations"); subject = c2.text_input("Subject", "Science")
grade = c3.text_input("Grade", "8"); minutes = c4.number_input("Minutes", 20, 120, 40)
c5, c6, c7 = st.columns(3)
ldate = c5.date_input("Lesson date", datetime.date.today())
week = c6.text_input("Week of (short)", f"{(ldate - datetime.timedelta(days=ldate.weekday())).strftime('%m/%d/%y')}")
standards = c7.text_input("Standards (e.g. NGSS codes)", "MS-LS3-1, MS-LS4-4")
ctx = dict(topic=topic, subject=subject, grade=grade, minutes=minutes, teacher=teacher, style=style,
           date=ldate.strftime("%m/%d/%Y"), week_of=week, standards="\n".join(x.strip() for x in standards.split(",") if x.strip()))
days = 1
if mkey == "new":
    ctx["notes"] = st.text_area("Anything about your class? (optional, no student names)")
else:
    q = st.text_input("Search your past lessons (includes a Capital Prep sample)")
    rows = store.search(teacher, q)
    opts = {f"{r[1]} ({r[5]})": r[4] for r in rows}
    pick = st.selectbox("Adapt a saved lesson", ["(none)"] + list(opts))
    up = st.file_uploader("…or upload a past filled plan (.pdf or .docx)", type=["docx", "pdf"], key="past")
    past = opts.get(pick, "")
    if up:
        past = pdfio.pdf_text(up.getvalue()) if up.name.lower().endswith(".pdf") else template.doc_text(up.getvalue())
        if st.button("Add uploaded plan to my library"):
            store.save_lesson(teacher, up.name, subject, grade, past, None); st.toast("Added to your library")
    ctx["past_lesson"] = past[:12000]
    days = st.number_input("Number of days (multi-day sequence)", 1, 10, 1)

if st.button("3. Generate my lesson plan", type="primary"):
    outs = []
    with st.spinner("TAP is writing your lesson plan…"):
        for d in range(1, days + 1):
            ctx.update(day=d, days=days)
            try:
                if other: _, content, out = engine.run(mkey, data, ctx, prov)
                else: content, out = engine.run_capprep(mkey, ctx, prov)
            except Exception as e:
                st.error(f"AI error, falling back to demo content: {e}")
                if other: _, content, out = engine.run(mkey, data, ctx, llm.DemoProvider())
                else: content, out = engine.run_capprep(mkey, ctx, llm.DemoProvider())
            outs.append((d, content, out))
            store.save_lesson(teacher, f"{topic} day {d}", subject, grade, "\n".join(f"{k}: {v}" for k, v in content.items()), out)
    st.session_state.outs = outs
for d, content, out in st.session_state.get("outs", []):
    st.subheader(f"Day {d}")
    st.download_button(f"⬇️ Download Day {d} (.docx)", out, f"lesson_{topic}_day{d}.docx".replace(" ", "_"), key=f"dl{d}", type="primary")
    with st.expander("Preview content"):
        for k, v in content.items(): st.markdown(f"**{k}**  \n" + v.replace("\n", "  \n"))

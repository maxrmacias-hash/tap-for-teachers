# TAP for Teachers

Upload your school's lesson-plan template (.docx) → TAP for Teachers detects its sections (headings, `Label:` lines, table label/value cells) → generates content with an LLM → fills the **real** template (formatting preserved) → download .docx.

Branding: owl mascot + storyboard art in `assets/` (hero.jpg, owl_face.png, new_teacher_card.png, experienced_teacher_card.png, intro.mp4); theme in `.streamlit/config.toml`.

Two modes: **I'm a New Teacher** (scaffolded mentor: objectives, standards, differentiation, timing, exit ticket, tips) and **I'm an Experienced Teacher** (search/upload past lessons, adapt in your voice, multi-day sequences).

## Run locally
```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export XAI_API_KEY=...        # optional; without it the app runs in clearly-labeled DEMO mode
.venv/bin/streamlit run app.py
```
Optional env: `LLM_MODEL` (default `grok-4`), `LLM_BASE_URL` (default `https://api.x.ai/v1`), `OPENAI_API_KEY` (alternate provider), `LP_DB` (SQLite path, default `data/lessons.db`).

## 14-day pilot access (optional)
`ACCESS_CODES="TAP-XXXX"` requires an invite code; `PILOT_EXPIRES=2026-11-15` closes the app after that date.

## Test
`python make_sample.py && python test_flow.py` — builds `samples/sample_template.docx`, runs both modes headlessly, writes `samples/out_*.docx`.

## Deploy a stable pilot link (Streamlit Community Cloud)
1. Push this folder to a GitHub repo (exclude `.venv/`, `data/`).
2. share.streamlit.io → New app → pick repo, main file `app.py`.
3. Advanced settings → Secrets:
```
XAI_API_KEY = "..."
ACCESS_CODES = "TAP-XXXX"
PILOT_EXPIRES = "2026-11-15"
```
(Values are read from st.secrets, with environment-variable fallback. Expiry is end of day America/New_York.) 4. Share the `*.streamlit.app` URL + invite code.
Note: Community Cloud disk is ephemeral — the SQLite library can reset on restart. For durable storage use Render/Railway/Fly with a persistent volume (`streamlit run app.py --server.port $PORT --server.address 0.0.0.0`, set `LP_DB` to the volume).

## Privacy
No student PII is requested or stored; only lesson text, teacher nickname, and style preferences.

## Capital Prep Bronx (locked default template)
- Master file: `templates/capprep_master.docx` — the school's ORIGINAL Word template, used for every plan in both modes.
- `core/capprep.py` fills it **in place**: content only goes into the empty slots after each label (cloning that slot's formatting).
  The output is rebuilt from the original file byte-for-byte; only `word/document.xml` changes, so the logo, header, styles,
  fonts, numbering and theme are identical. Labels can't be renamed: the AI only returns values for 35 fixed slot IDs.
- School vocabulary is built into the prompt: Illuminator, Scholars, SWBAT, voice levels 0–3, Level 1/2/3 modifications, NGSS codes, TLAC.
- The IP Coaching scholar-grouping and IEP tables are left blank on purpose (student data).
- To use another school's template, tick "Advanced" (DOCX, or a PDF rebuilt into a DOCX template, best effort).
- Past filled plans (PDF/DOCX) can be added to the Experienced Teacher library; `samples/capprep_past_lesson.pdf` is preloaded as a sample.
- Tests: `python test_capprep.py` (both modes, every slot filled, labels unchanged, logo/header/styles byte-identical, renders PNGs to `samples/output/`), `python test_ui.py`.

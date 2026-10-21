"""SQLite storage for saved lessons + preferences (no student PII)."""
import sqlite3, os, datetime
DB = os.getenv("LP_DB", os.path.join(os.path.dirname(__file__), "..", "data", "lessons.db"))

def conn():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS lessons(id INTEGER PRIMARY KEY, teacher TEXT, title TEXT, subject TEXT, grade TEXT, body TEXT, docx BLOB, created TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS prefs(teacher TEXT PRIMARY KEY, style TEXT)")
    return c

def save_lesson(teacher, title, subject, grade, body, docx=None):
    with conn() as c:
        c.execute("INSERT INTO lessons(teacher,title,subject,grade,body,docx,created) VALUES(?,?,?,?,?,?,?)",
                  (teacher, title, subject, grade, body, docx, datetime.datetime.now().isoformat(timespec="seconds")))

def search(teacher, q=""):
    with conn() as c:
        return c.execute("SELECT id,title,subject,grade,body,created FROM lessons WHERE teacher IN (?, '__sample__') AND (title LIKE ? OR body LIKE ?) ORDER BY id DESC",
                         (teacher, f"%{q}%", f"%{q}%")).fetchall()

def get_pref(teacher):
    with conn() as c:
        r = c.execute("SELECT style FROM prefs WHERE teacher=?", (teacher,)).fetchone(); return r[0] if r else ""

def set_pref(teacher, style):
    with conn() as c:
        c.execute("INSERT OR REPLACE INTO prefs VALUES(?,?)", (teacher, style))

def seed_samples(root):
    """Add the bundled Capital Prep past lesson (PDF) as a shared sample in every library."""
    import os
    with conn() as c:
        if c.execute("SELECT 1 FROM lessons WHERE teacher='__sample__'").fetchone(): return
    pdf = os.path.join(root, "samples", "capprep_past_lesson.pdf")
    if os.path.exists(pdf):
        from .pdfio import pdf_text
        save_lesson("__sample__", "SAMPLE – Capital Prep 10/14/2026 Mutations, Traits & Survival (8th Sci)", "Science", "8",
                    pdf_text(open(pdf, "rb").read()), None)

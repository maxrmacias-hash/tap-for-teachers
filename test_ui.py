from streamlit.testing.v1 import AppTest
for m in ["new","experienced"]:
    at=AppTest.from_file("app.py",default_timeout=30); at.session_state.mode=m; at.run()
    print(m, "exceptions:", at.exception, "| title:", [t.value for t in at.title], "| buttons:", [b.label for b in at.button])
for m in ["new", "experienced"]:
    at = AppTest.from_file("app.py", default_timeout=60); at.session_state.mode = m; at.run()
    [b for b in at.button if b.label.startswith("3. Generate")][0].click().run()
    outs = at.session_state.outs; d, content, out = outs[0]
    print(m, "generate via UI: exceptions", list(at.exception), "| docx bytes", len(out), "| fields", len(content))
    assert out[:2] == b"PK" and len(content) >= 30

from core import engine, template, store
data = open("samples/sample_template.docx","rb").read()
for mode in ["new","experienced"]:
    ctx = dict(topic="Photosynthesis", subject="Science", grade="7", minutes=50, teacher="test", date="2026-10-21",
               past_lesson="Warm-up: leaf rubbings. Lab: elodea bubbles." if mode=="experienced" else "", day=1, days=2)
    f, c, out = engine.run(mode, data, ctx)
    open(f"samples/out_{mode}.docx","wb").write(out)
    txt = template.doc_text(out); missing = [x["label"] for x in f if c.get(x["label"]) and c[x["label"]].split("\n")[0][:20] not in txt]
    print(mode, "fields:", len(f), [x["label"] for x in f]); print(" missing:", missing); assert not missing
    store.save_lesson("test", "t", "s", "7", txt)
print("search:", len(store.search("test","Photo"))); print("OK")

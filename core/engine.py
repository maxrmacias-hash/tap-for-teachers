from . import template, llm
def run(mode, tpl_bytes, ctx, provider=None):
    provider = provider or llm.get_provider()
    doc = template.load(tpl_bytes); fields = template.detect_fields(doc)
    content = provider.generate(mode, fields, ctx)
    return fields, content, template.populate(tpl_bytes, fields, content)

def run_capprep(mode, ctx, provider=None):
    from . import capprep
    provider = provider or llm.get_provider()
    sys_txt = capprep.VOCAB + "\n" + capprep.BUDGET_TEXT
    content = provider.generate_schema(mode, capprep.FIELDS, ctx, sys_txt)
    content = capprep.enforce_budget({k: v for k, v in content.items() if k in capprep.FIELDS})  # only known slots
    out = capprep.populate(content)
    # if the render exceeds the master's page count, ask the AI to tighten (real providers only)
    for _ in range(2):
        if isinstance(provider, llm.DemoProvider): break
        pages = capprep.page_count(out)
        if not pages or pages <= capprep.MASTER_PAGES: break
        ctx2 = dict(ctx, previous_draft=content, instruction=f"The plan rendered to {pages} pages; the limit is "
                    f"{capprep.MASTER_PAGES}. Shorten every value ~25% while keeping all essentials.")
        content = capprep.enforce_budget({k: v for k, v in provider.generate_schema(mode, capprep.FIELDS, ctx2, sys_txt).items() if k in capprep.FIELDS})
        out = capprep.populate(content)
    return content, out

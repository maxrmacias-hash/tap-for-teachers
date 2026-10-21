"""Pluggable LLM providers. Uses xAI Grok (OpenAI-compatible) if XAI_API_KEY set, else demo."""
import os, json, re

PAUKER = (" Every lesson includes Pauker Writing (Dr. Robert Pauker's Structured Writing & Thinking Program): Quick Picture (sketch the core image), Area of Focus (one main idea per paragraph), lesson-specific Guide Questions to draft an analytical paragraph, and Elaboration (add evidence in revision). Illuminator models a Pauker paragraph; scholar work ends with a Pauker paragraph; exit ticket is a short Pauker paragraph or Elaboration. L1 paragraph frame with Guide Questions + sentence starters, L2 standard, L3 elaborate with additional evidence/counterexample.")
NEW_SYS = ("You are a warm, supportive mentor for a new teacher. Produce a complete, well-scaffolded lesson: "
           "measurable objectives, standards alignment, differentiation (ELL, IEP/504, advanced), minute-by-minute timing, "
           "exit ticket, and practical instructional tips. Briefly explain why where helpful.")
EXP_SYS = ("You are an efficient colleague to an experienced teacher. Be concise. Preserve the teacher's own voice, "
           "activities and phrasing from their past lessons; adapt rather than rewrite. Support multi-day sequencing.")

NEW_SYS += PAUKER; EXP_SYS += PAUKER

def _prompt(fields, ctx):
    labels = [f["label"] for f in fields]
    return (f"Lesson context:\n{json.dumps(ctx, indent=1)}\n\nFill EVERY one of these template sections: {labels}.\n"
            "Return ONLY a JSON object mapping each exact section label to plain-text content (use \\n for line breaks, '- ' bullets). "
            "No student names or personal data.")

def _schema_prompt(fields, ctx):
    return (f"Lesson context:\n{json.dumps(ctx, indent=1)}\n\nWrite content for EVERY key below (descriptions in values):\n"
            f"{json.dumps(fields, indent=1)}\nReturn ONLY a JSON object with exactly these keys and plain-text values "
            "(use \\n for line breaks, '• ' bullets). Do not repeat the label text in values. Time values are numbers of minutes "
            "that add up to the lesson length.")

class DemoProvider:
    name = "Demo (offline, no AI) "
    def generate_schema(self, mode, fields, ctx, school_sys=""):
        from . import capprep
        return capprep.demo_content(ctx)
    def generate(self, mode, fields, ctx):
        topic, grade, subj = ctx.get("topic", "the topic"), ctx.get("grade", ""), ctx.get("subject", "")
        mins = int(ctx.get("minutes") or 50); past = ctx.get("past_lesson", "")
        out = {}
        for f in fields:
            l = f["label"].lower()
            if "objective" in l: v = f"- Students will explain key ideas of {topic}.\n- Students will apply {topic} to a short task."
            elif "standard" in l: v = f"[DEMO] Align to your state {subj} standard for grade {grade} on {topic}."
            elif "differen" in l or "accommodat" in l: v = "- ELL: visuals + sentence frames\n- IEP/504: chunked steps, extra time\n- Advanced: extension challenge"
            elif "date" in l: v = str(ctx.get("date", ""))
            elif "tim" in l or "procedure" in l or "agenda" in l or "activit" in l:
                a = mins // 5
                v = f"- Warm-up ({a} min)\n- Direct instruction ({a} min)\n- Guided practice ({a} min)\n- Independent practice ({a} min)\n- Exit ticket ({mins-4*a} min)"
            elif "exit" in l or "assess" in l: v = f"Exit ticket: In 2 sentences, summarize one thing you learned about {topic}."
            elif "material" in l or "resource" in l: v = "- Slides\n- Handout\n- Whiteboard"
            elif "reflect" in l: v = "What worked? What would you change next time?"
            elif "duration" in l: v = f"{mins} minutes"
            elif "unit" in l: v = f"{subj}: {topic}"
            elif "tip" in l or "note" in l: v = "Tip: model one example aloud before practice; circulate during work time."
            elif "topic" in l or "title" in l or "lesson" == l: v = topic
            elif "grade" in l: v = str(grade)
            elif "subject" in l: v = subj
            elif "date" in l: v = str(ctx.get("date", ""))
            elif "teacher" in l: v = ctx.get("teacher", "")
            elif "day" in l or "sequence" in l: v = f"Day {ctx.get('day',1)} of {ctx.get('days',1)}"
            else: v = f"[DEMO] {f['label']} for {topic}."
            if mode == "experienced" and past and ("procedure" in l or "activit" in l):
                v += "\n(Adapted from your past lesson.)"
            if mode == "new" and ("objective" in l): v += "\nMentor note: good objectives are measurable—use verbs like explain, compare, solve."
            out[f["label"]] = v
        return out

class OpenAICompatProvider:
    def __init__(self, api_key, base_url, model, name):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url); self.model = model; self.name = name
    def _chat(self, sys, user):
        r = self.client.chat.completions.create(model=self.model, temperature=0.4,
            messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}])
        txt = r.choices[0].message.content; m = re.search(r"\{.*\}", txt, re.S)
        data = json.loads(m.group(0)) if m else {}
        return {k: (v if isinstance(v, str) else "\n".join(map(str, v)) if isinstance(v, list) else str(v)) for k, v in data.items()}
    def generate_schema(self, mode, fields, ctx, school_sys=""):
        sys = (NEW_SYS if mode == "new" else EXP_SYS) + "\n" + school_sys
        if ctx.get("style"): sys += f"\nTeacher preferences: {ctx['style']}"
        return self._chat(sys, _schema_prompt(fields, ctx))
    def generate(self, mode, fields, ctx):
        sys = NEW_SYS if mode == "new" else EXP_SYS
        if ctx.get("style"): sys += f"\nTeacher preferences: {ctx['style']}"
        r = self.client.chat.completions.create(model=self.model, temperature=0.4,
            messages=[{"role": "system", "content": sys}, {"role": "user", "content": _prompt(fields, ctx)}])
        txt = r.choices[0].message.content
        m = re.search(r"\{.*\}", txt, re.S)
        data = json.loads(m.group(0)) if m else {}
        return {k: (v if isinstance(v, str) else "\n".join(map(str, v)) if isinstance(v, list) else json.dumps(v)) for k, v in data.items()}

def get_provider():
    if os.getenv("XAI_API_KEY"):
        return OpenAICompatProvider(os.environ["XAI_API_KEY"], os.getenv("LLM_BASE_URL", "https://api.x.ai/v1"),
                                    os.getenv("LLM_MODEL", "grok-4"), "xAI Grok")
    if os.getenv("OPENAI_API_KEY"):
        return OpenAICompatProvider(os.environ["OPENAI_API_KEY"], os.getenv("LLM_BASE_URL"), os.getenv("LLM_MODEL", "gpt-4o-mini"), "OpenAI")
    return DemoProvider()

"""Expert advice: grounded LLM guidance for one machine. Inputs are only the asset's own diagnosis, fingerprint, fix plan,
history and outlook plus our notes in backend/knowledge/. Cached by (asset, at, lang); fixtures answer the demo bookmarks."""
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic import BaseModel, ValidationError

from backend import state
from backend.advice import llm
from backend.api.models import AdviceOut, AdviceSection, AdviceSource

ROOT = Path(__file__).resolve().parents[2]
KNOW = ROOT / "backend" / "knowledge"
FIX = ROOT / "contracts" / "fixtures"
HEADINGS = {"en": ["Check first", "Step by step", "Safety", "Parts and tools", "Call the manufacturer if"],
            "ms": ["Semak dahulu", "Langkah demi langkah", "Keselamatan", "Alat dan alat ganti", "Hubungi pengilang jika"]}
DISCLAIMER = {"en": "AI-generated guidance — check against the manufacturer's manual and your SOP",
              "ms": "Panduan dijana AI — semak dengan manual pengilang dan SOP anda"}
LOTO = {"en": "Lock out and tag out the machine before you open or touch it, and test that it cannot start.",
        "ms": "Kunci dan tag (lock-out/tag-out) mesin sebelum membuka atau menyentuhnya, dan uji bahawa ia tidak boleh bermula."}
LOTO_WORD = {"en": "lock", "ms": "kunci"}
UNAVAILABLE = {"en": ("Detailed advice is not available", "Detailed advice is not available right now. The fix plan above still applies."),
               "ms": ("Nasihat terperinci tidak tersedia", "Nasihat terperinci tidak tersedia sekarang. Pelan pembaikan di atas masih terpakai.")}
NO_FAULT = {"en": ("No advice needed", "There is no fault to advise on for this machine right now."),
            "ms": ("Tiada nasihat diperlukan", "Tiada kerosakan untuk dinasihatkan bagi mesin ini sekarang.")}
LANGUAGE = {"en": "English", "ms": "Bahasa Malaysia"}
SYSTEM = """You are a maintenance advisor for a palm-oil mill, writing for a night-shift supervisor.
Rules:
- Use ONLY the facts in the inputs and the notes below. Do not invent manufacturer part numbers, torque values, clearances, pressures, oil grades or procedures. When a number is needed, say it must come from the manufacturer's manual or the mill's SOP.
- If a machine stop is needed, the Safety section must start with lock-out/tag-out.
- Plain, short sentences a supervisor can act on. Explain any technical word once.
- Write everything in {language}.
- Return ONLY a JSON object, no markdown: {{"title": string, "sections": [{{"heading": string, "items": [string, ...]}}, ...]}}
- Exactly 5 sections, in this order, with these headings: {headings}.
- 2 to 6 short items per section."""


class Generated(BaseModel):
    title: str
    sections: list[AdviceSection]


def now_iso():
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def notes(fault_class):
    """-> (text of general + fault notes, sources parsed from their 'Sources:' lists)"""
    text, sources = [], []
    for name in ("general", fault_class):
        f = KNOW / f"{name}.md"
        if not f.exists():
            continue
        body = f.read_text()
        text.append(body)
        for m in re.finditer(r"^- (.+?) \| (https?://\S+)\s*$", body, re.M):
            if not any(s.url == m.group(2) for s in sources):
                sources.append(AdviceSource(label=m.group(1), url=m.group(2)))
    return "\n\n".join(text), sources


def inputs(d):
    diag, fix, act, out = d["diagnosis"], d["fix"], d["action"], d["outlook"]
    return dict(
        machine=d["asset"]["name"], status=d["status"], risk_pct=d["risk_pct"],
        diagnosis=dict(fault=diag["name_en"], confidence_pct=diag["confidence_pct"], plain=diag["plain_en"],
                       alternatives=[a["fault_class"] + f" {a['confidence_pct']:.0f}%" for a in diag["alternatives"]],
                       fingerprint=[dict(sign=c["label_en"], expected=c["expected"], seen=c["observed_en"], matches=c["matches"]) for c in diag["fingerprint"]]),
        fix_plan=fix and dict(title=fix["title_en"], steps=fix["steps_en"], parts=[f"{p['name_en']} x{p['qty']}" for p in fix["parts"]],
                              crew=fix["crew"], est_hours=fix["est_hours"], needs_stop=fix["needs_stop"], stop=fix["stop"]),
        money=dict(expected_loss_if_wait_rm=out["rm_at_risk"], cost_to_act_rm=out["rm_cost_to_act"], saved_if_acted_rm=out["rm_saved_if_acted"]),
        recent_history=[dict(when=h["t"][:10], what=h["what_en"], predicted=h["was_predicted"]) for h in d["history"][:5]],
        last_service=d["last_service"]["what_en"], hours_since_service=d["last_service"]["hours_since"])


def parse(raw):
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
    return Generated(**json.loads(raw))


def shape(g, lang, needs_stop, fault_class, src, model_name):
    secs = [AdviceSection(heading=h, items=[i for i in s.items if i.strip()]) for h, s in zip(HEADINGS[lang], g.sections)]
    safety = secs[2]
    if needs_stop and not any(LOTO_WORD[lang] in i.lower() for i in safety.items[:1]):
        safety.items.insert(0, LOTO[lang])
    return AdviceOut(title=g.title, sections=secs, sources=src, disclaimer=DISCLAIMER[lang], generated_at=now_iso(),
                     cached=False, model=model_name)


def unavailable(lang, kind=UNAVAILABLE):
    t, m = kind[lang]
    return AdviceOut(title=t, sections=[], sources=[], disclaimer=DISCLAIMER[lang], generated_at=now_iso(), cached=False, model="", message=m)


def key(svc, aid, at, lang):
    return f"{aid}|{svc.clamp_time(at).isoformat()}|{lang}"


def fixture_name(aid, at, lang):
    idx = json.loads((FIX / "bookmarks.json").read_text())
    d = (at or "")[:10]
    suffix = {idx["quiet"][:10]: "_quiet", idx["act"][:10]: "_act", idx["both"][:10]: ""}.get(d)
    return None if suffix is None else FIX / f"advice_{aid}{suffix}_{lang}.json"


def from_fixture(aid, at, lang):
    try:
        f = fixture_name(aid, at, lang)
        if f and f.exists():
            return AdviceOut(**{**json.loads(f.read_text()), "cached": True})
    except Exception:
        pass
    return None


def load_cache():
    try:
        return state.db().get("advice_cache") or {}
    except Exception:
        return {}


def advise(svc, aid, at, lang="en", use_cache=True) -> AdviceOut:
    """Never raises: any problem becomes an unavailable answer."""
    try:
        d = svc.asset(aid, at)
        if d is None:
            return unavailable(lang)
        if not d["diagnosis"]:
            return unavailable(lang, NO_FAULT)
        k = key(svc, aid, at, lang)
        if use_cache:
            hit = load_cache().get(k) or from_fixture(aid, svc.clamp_time(at).strftime("%Y-%m-%d"), lang)
            if hit:
                return AdviceOut(**{**(hit if isinstance(hit, dict) else hit.model_dump()), "cached": True})
        if not llm.configured():
            return unavailable(lang)
        fc = d["diagnosis"]["fault_class"]
        text, src = notes(fc)
        system = SYSTEM.format(language=LANGUAGE[lang], headings=", ".join(HEADINGS[lang])) + "\n\nNotes (our own words):\n" + text
        user = "Machine inputs (JSON):\n" + json.dumps(inputs(d), ensure_ascii=False) + f"\n\nWrite the advice in {LANGUAGE[lang]}."
        needs_stop = d["fix"] is None or d["fix"]["needs_stop"]
        for attempt in range(2):   # one retry, for network errors and for invalid JSON
            try:
                out = shape(parse(llm.complete(system, user)), lang, needs_stop, fc, src, llm.model())
                break
            except (ValidationError, json.JSONDecodeError, ValueError):
                out = None
            except Exception as e:   # provider or network; do not print details (they could echo settings)
                print("advice: provider call failed:", type(e).__name__)
                out = None
        if out is None or len(out.sections) != 5:
            return unavailable(lang)
        c = load_cache(); c[k] = out.model_dump(mode="json"); state.db().set("advice_cache", c)
        return out
    except Exception as e:
        print("advice: failed:", type(e).__name__)
        return unavailable(lang)

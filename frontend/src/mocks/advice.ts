// Placeholder for POST /api/advice until the backend ships the contract (MASTER_PLAN.md §14, v1.10).
// Shape copied from the plan; delete this file once contracts/api.ts and advice_* fixtures exist.
// Content restates our own fix plan in other words: no manufacturer part numbers, torques or procedures.

export interface AdviceIn { asset_id: string; at: string; lang: "en" | "ms" }
export interface AdviceSection { heading: string; items: string[] }
export interface Advice {
  title: string;
  sections: AdviceSection[]; // Check first, Step by step, Safety, Parts and tools, Call the manufacturer if
  sources: { label: string; url?: string }[];
  disclaimer: string;
  generated_at: string;
  cached: boolean;
  model: string;
}

const MODEL = "placeholder (frontend mock, not a model)";

const press2: Record<"en" | "ms", Advice> = {
  en: {
    title: "Press 2: cone hydraulic fault",
    sections: [
      { heading: "Check first", items: ["Hydraulic oil level and any leaks on hoses and fittings.", "Whether the cone pressure gauge swings while the press runs."] },
      { heading: "Step by step", items: ["Stop and isolate the press.", "Replace leaking hoses and worn seals.", "Change the hydraulic filter and top up with the oil grade in your manual.", "Test cone pressure under load before handing back."] },
      { heading: "Safety", items: ["Lock out and tag out the press before opening anything.", "Release stored hydraulic pressure before disconnecting hoses."] },
      { heading: "Parts and tools", items: ["Hydraulic hose ×2", "Seal kit ×1", "Hydraulic filter ×1"] },
      { heading: "Call the manufacturer if", items: ["Pressure still swings after hoses, seals and filter are changed.", "You see damage to the cylinder or the cone itself."] },
    ],
    sources: [{ label: "MillGuard fault guide: cone hydraulic fault" }, { label: "Screw press FMEA studies cited in the plan" }],
    disclaimer: "AI-generated guidance. Check against the manufacturer's manual and your SOP.",
    generated_at: "2025-09-29T15:00:00+08:00", cached: true, model: MODEL,
  },
  ms: {
    title: "Penekan 2: kerosakan hidraulik kon",
    sections: [
      { heading: "Semak dahulu", items: ["Paras minyak hidraulik dan kebocoran pada hos dan penyambung.", "Sama ada tolok tekanan kon berayun semasa penekan berjalan."] },
      { heading: "Langkah demi langkah", items: ["Hentikan dan asingkan penekan.", "Tukar hos bocor dan sesendal haus.", "Tukar penapis hidraulik dan tambah minyak gred mengikut manual anda.", "Uji tekanan kon dengan beban sebelum diserahkan semula."] },
      { heading: "Keselamatan", items: ["Kunci dan tag penekan sebelum membuka apa-apa.", "Lepaskan tekanan hidraulik tersimpan sebelum menanggalkan hos."] },
      { heading: "Alat ganti dan peralatan", items: ["Hos hidraulik ×2", "Set sesendal ×1", "Penapis hidraulik ×1"] },
      { heading: "Hubungi pengeluar jika", items: ["Tekanan masih berayun selepas hos, sesendal dan penapis ditukar.", "Anda nampak kerosakan pada silinder atau kon."] },
    ],
    sources: [{ label: "Panduan kerosakan MillGuard: kerosakan hidraulik kon" }, { label: "Kajian FMEA penekan skru yang dipetik dalam pelan" }],
    disclaimer: "Panduan dijana AI. Semak dengan manual pengeluar dan SOP anda.",
    generated_at: "2025-09-29T15:00:00+08:00", cached: true, model: MODEL,
  },
};

const boiler1: Record<"en" | "ms", Advice> = {
  en: {
    title: "Boiler 1: feed-water quality drift",
    sections: [
      { heading: "Check first", items: ["Feed-water conductivity and hardness.", "Whether the softener or resin bed is due for regeneration."] },
      { heading: "Step by step", items: ["Increase blowdown until conductivity returns to normal.", "Check chemical dosing rates against your water-treatment plan.", "Plan a tube inspection at the next planned stop if it keeps rising."] },
      { heading: "Safety", items: ["Follow your boiler blowdown procedure; blowdown water is hot and under pressure.", "Lock out and tag out before any tube inspection."] },
      { heading: "Parts and tools", items: ["Resin or softener salt ×1", "Test reagent kit ×1"] },
      { heading: "Call the manufacturer if", items: ["Conductivity keeps rising after blowdown and dosing are corrected.", "You suspect a tube leak."] },
    ],
    sources: [{ label: "MillGuard fault guide: feed-water quality drift" }],
    disclaimer: "AI-generated guidance. Check against the manufacturer's manual and your SOP.",
    generated_at: "2025-09-14T03:00:00+08:00", cached: true, model: MODEL,
  },
  ms: {
    title: "Dandang 1: sisihan kualiti air suapan",
    sections: [
      { heading: "Semak dahulu", items: ["Kekonduksian dan kekerasan air suapan.", "Sama ada pelembut atau lapisan resin perlu dijana semula."] },
      { heading: "Langkah demi langkah", items: ["Tambah blowdown sehingga kekonduksian kembali normal.", "Semak kadar dos bahan kimia mengikut pelan rawatan air.", "Rancang pemeriksaan tiub pada henti terancang seterusnya jika terus meningkat."] },
      { heading: "Keselamatan", items: ["Ikut prosedur blowdown dandang anda; air blowdown panas dan bertekanan.", "Kunci dan tag sebelum sebarang pemeriksaan tiub."] },
      { heading: "Alat ganti dan peralatan", items: ["Resin atau garam pelembut ×1", "Set reagen ujian ×1"] },
      { heading: "Hubungi pengeluar jika", items: ["Kekonduksian terus naik selepas blowdown dan dos dibetulkan.", "Anda mengesyaki kebocoran tiub."] },
    ],
    sources: [{ label: "Panduan kerosakan MillGuard: sisihan kualiti air suapan" }],
    disclaimer: "Panduan dijana AI. Semak dengan manual pengeluar dan SOP anda.",
    generated_at: "2025-09-14T03:00:00+08:00", cached: true, model: MODEL,
  },
};

// Keyed like the planned fixtures: advice_<asset>[_act|_quiet]_<lang>
export const MOCK_ADVICE: Record<string, Advice> = {
  press_2_act_en: press2.en, press_2_act_ms: press2.ms,
  boiler_1_en: boiler1.en, boiler_1_ms: boiler1.ms,
};

"""All user-facing strings (EN + BM). Edit here when the design's final wording arrives."""

BOILER_1 = dict(
    headline_en="Boiler 1: steam temperature drifting. Check feed-water dosing and blowdown now.",
    headline_ms="Dandang 1: suhu stim menyimpang. Semak dos air suapan dan blowdown sekarang.",
    reasons=[
        ("steam_temp", "down", 0.47,
         "Steam temperature has sat below its normal 530–545 °C band for 4 hours",
         "Suhu stim berada di bawah julat biasa 530–545 °C selama 4 jam"),
        ("steam_pressure", "up", 0.33,
         "Steam pressure is swinging twice as much as usual",
         "Tekanan stim berayun dua kali ganda daripada biasa"),
        ("feedwater_flow", "down", 0.20,
         "Feed-water flow is falling while the mill load is steady",
         "Aliran air suapan menurun walaupun beban kilang stabil")],
    why_rank_en="Boiler stops the whole mill, so it comes first",
    why_rank_ms="Dandang menghentikan seluruh kilang, jadi ia diutamakan")

PRESS_2_WORM = dict(
    headline_en="Press 2: worm wear. Change the worm at tomorrow's 06:00 stop.",
    headline_ms="Penekan 2: haus skru cacing. Tukar skru pada henti terancang esok jam 06:00.",
    reasons=[
        ("current_per_tonne", "up", 0.46,
         "Motor current per tonne is 9% above Press 2's normal for 5 days",
         "Arus motor setiap tan 9% lebih tinggi daripada biasa bagi Penekan 2 selama 5 hari"),
        ("fibre_oil_loss", "up", 0.31,
         "Oil lost in fibre rose to 3.6% (alarm line is 4%)",
         "Kehilangan minyak dalam serabut meningkat kepada 3.6% (garis amaran 4%)"),
        ("hours_since_service", "up", 0.23,
         "Worm has run 1,310 h since the last change; typical life is about 1,200 h",
         "Skru cacing telah beroperasi 1,310 jam sejak penggantian terakhir; hayat biasa kira-kira 1,200 jam")],
    why_rank_en="Costs less than the boiler, and the fix fits the planned stop",
    why_rank_ms="Kos lebih rendah daripada dandang, dan pembaikan muat dalam henti terancang")

MARKERS = dict(
    quiet_en="Quiet night: nothing needs you", quiet_ms="Malam tenang: tiada tindakan diperlukan",
    onset_en="Press 2 worm-wear alert begins", onset_ms="Amaran haus skru cacing Penekan 2 bermula",
    both_en="Boiler and press alerts on the same night", both_ms="Amaran dandang dan penekan pada malam yang sama",
    alert_en="{asset}: MillGuard alert", alert_ms="{asset}: amaran MillGuard",
    breakdown_en="{asset}: breakdown", breakdown_ms="{asset}: kerosakan")

SERIES = {
    "steam_temp": ("Steam temperature", "Suhu stim", "°C"),
    "steam_pressure": ("Steam pressure", "Tekanan stim", "bar"),
    "feedwater_flow": ("Feed-water flow", "Aliran air suapan", "t/h"),
    "current_per_tonne": ("Motor current per tonne", "Arus motor setiap tan", "A/t"),
    "vibration_kurtosis": ("Vibration kurtosis", "Kurtosis getaran", ""),
    "gearbox_oil_temp": ("Gearbox oil temperature", "Suhu minyak gear", "°C"),
}

# ---- engine templates (SHAP reasons, headlines, rank explanations) ----
SIGNAL_LABEL = {   # signal -> (EN, MS)
    "current_per_tonne": ("Motor current per tonne", "Arus motor setiap tan"),
    "motor_current": ("Motor current", "Arus motor"),
    "cone_pressure": ("Cone hydraulic pressure", "Tekanan hidraulik kon"),
    "gearbox_oil_temp": ("Gearbox oil temperature", "Suhu minyak gear"),
    "vib_rms": ("Vibration level (RMS)", "Tahap getaran (RMS)"),
    "vib_kurtosis": ("Vibration spikiness (kurtosis)", "Kemuncakan getaran (kurtosis)"),
    "fibre_oil_loss": ("Oil lost in fibre", "Kehilangan minyak dalam serabut"),
    "steam_temp": ("Steam temperature", "Suhu stim"),
    "steam_pressure": ("Steam pressure", "Tekanan stim"),
    "feedwater_flow": ("Feed-water flow", "Aliran air suapan"),
    "feedwater_cond": ("Feed-water conductivity", "Kekonduksian air suapan"),
}
REASON_REL_EN = "{label} is {pct:.0f}% {word} {asset}'s normal"
REASON_REL_MS = "{label} {pct:.0f}% {word} biasa bagi {asset}"
WORD_EN = {"up": "above", "down": "below"}
WORD_MS = {"up": "lebih tinggi daripada", "down": "lebih rendah daripada"}
REASON_FIBRE_EN = "Oil lost in fibre is {v:.1f}% (alarm line is 4%)"
REASON_FIBRE_MS = "Kehilangan minyak dalam serabut ialah {v:.1f}% (garis amaran 4%)"
REASON_SERVICE_EN = "{h:,.0f} h since the last logged service on {asset}"
REASON_SERVICE_MS = "{h:,.0f} jam sejak servis terakhir direkodkan bagi {asset}"
REASON_ALARMS_EN = "{n:.0f} controller alarms on {asset} in the last 24 h"
REASON_ALARMS_MS = "{n:.0f} penggera pengawal pada {asset} dalam 24 jam lepas"
REASON_LOAD_EN = "Recent load on {asset} differs from its usual pattern"
REASON_LOAD_MS = "Beban terkini pada {asset} berbeza daripada corak biasa"

FAULT_LABEL = {   # class -> (EN, MS)
    "worm_wear": ("worm wear", "haus skru cacing"), "bearing": ("bearing wear", "haus galas"),
    "gearbox_shaft": ("gearbox or shaft fault", "kerosakan gear atau aci"),
    "hydraulic_cone": ("cone hydraulic fault", "kerosakan hidraulik kon"),
    "electrical": ("electrical fault", "kerosakan elektrik"),
    "boiler_steam": ("steam temperature drift", "sisihan suhu stim"),
    "boiler_water": ("feed-water quality drift", "sisihan kualiti air suapan"),
    "unknown": ("unusual behaviour", "tingkah laku luar biasa"),
}
FIX_PHRASE = {
    "worm_wear": ("Change the worm", "Tukar skru cacing"), "bearing": ("Replace the bearing", "Tukar galas"),
    "gearbox_shaft": ("Inspect the gearbox and shaft", "Periksa gear dan aci"),
    "hydraulic_cone": ("Check the cone hydraulics", "Semak hidraulik kon"),
    "electrical": ("Check the motor and wiring", "Semak motor dan pendawaian"),
    "boiler_steam": ("Check feed-water dosing and blowdown", "Semak dos air suapan dan blowdown"),
    "boiler_water": ("Check water treatment and boiler tubes", "Semak rawatan air dan tiub dandang"),
    "unknown": ("Inspect the machine", "Periksa mesin"),
}
HEADLINE_FIX_EN = "{asset}: {fault}. {phrase} now."
HEADLINE_FIX_MS = "{asset}: {fault}. {phrase} sekarang."
HEADLINE_SCHED_EN = "{asset}: {fault}. {phrase} at {when}."
HEADLINE_SCHED_MS = "{asset}: {fault}. {phrase} pada {when}."
WHEN_TOMORROW = ("tomorrow's 06:00 stop", "henti terancang esok jam 06:00")
WHEN_DAY = ("the {day} 06:00 stop", "henti terancang {day} jam 06:00")
WHY_WHOLE_EN = "Boiler stops the whole mill, so it comes first"
WHY_WHOLE_MS = "Dandang menghentikan seluruh kilang, jadi ia diutamakan"
WHY_TOP_EN = "Biggest ringgit saving tonight"
WHY_TOP_MS = "Penjimatan ringgit terbesar malam ini"
WHY_PARTIAL_EN = "One press is a quarter of the mill, so it ranks below the boiler"
WHY_PARTIAL_MS = "Satu penekan ialah suku kilang, jadi ia di bawah dandang"
WHY_LOWER_EN = "Smaller saving than the actions above it"
WHY_LOWER_MS = "Penjimatan lebih kecil daripada tindakan di atas"

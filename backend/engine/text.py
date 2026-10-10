"""All user-facing strings (EN + BM). Edit here when the design's final wording arrives."""

MS_TERM = {"Press": "Penekan", "Boiler": "Dandang"}   # the one place for Malay machine terms (native-speaker check may change it)
UNIT_MS = {"hours": "jam", "alarms": "penggera"}


def name_ms(name):
    for en, ms in MS_TERM.items():
        name = name.replace(en, ms)
    return name


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
    act_en="{asset}: {fault}, act now", act_ms="{asset}: {fault}, bertindak sekarang",
    both_en="Boiler alert: the whole mill is at risk", both_ms="Amaran dandang: seluruh kilang berisiko",
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
    "vib_rms": ("Vibration level (root mean square)", "Tahap getaran (punca min kuasa dua)"),
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
REASON_SERVICE_EN = "{h:,.0f} hours since the last logged service on {asset}"
REASON_SERVICE_MS = "{h:,.0f} jam sejak servis terakhir direkodkan bagi {asset}"
REASON_ALARMS_EN = "{n:.0f} controller alarms on {asset} in the last 24 hours"
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

# ---- v1.5 fault playbook: one static entry per fault class (generic maintenance steps, not manufacturer procedures) ----
# signs: (signal, expected). Directions match what the simulator and published FMEA studies describe.
FAULTS = {
    "worm_wear": dict(
        name=("Worm wear", "Haus skru cacing"),
        plain=("The screw that squeezes the fruit is wearing thin, so the motor works harder and more oil stays in the fibre.",
               "Skru yang memerah buah semakin haus, jadi motor bekerja lebih kuat dan lebih banyak minyak tertinggal dalam serabut."),
        why=("Fruit fibre and sand grind the worm and cone surfaces over about 700 to 1,300 running hours.",
             "Serabut buah dan pasir mengikis permukaan skru dan kon selepas kira-kira 700 hingga 1,300 jam operasi."),
        signs=[("current_per_tonne", "up"), ("fibre_oil_loss", "up"), ("motor_current", "up"), ("vib_rms", "up")],
        steps=(["Plan the change for the next planned stop and tell the crew.",
                "Isolate and lock out the press, then open the press cage.",
                "Measure the worm and cone clearance and compare with the worn limit.",
                "Replace the worm and the cone liner if worn; check the shaft seat.",
                "Close up, run empty for 10 minutes, then check current per tonne."],
               ["Rancang penggantian pada henti terancang seterusnya dan maklumkan krew.",
                "Asingkan dan kunci penekan, kemudian buka sangkar penekan.",
                "Ukur sela skru dan kon, bandingkan dengan had haus.",
                "Tukar skru dan lapik kon jika haus; semak dudukan aci.",
                "Tutup, jalankan kosong 10 minit, kemudian semak arus setiap tan."]),
        parts=[(("Press worm (screw)", "Skru penekan"), 1), (("Cone liner set", "Set lapik kon"), 1)],
        crew=3, hours=4.0, needs_stop=True, onset="gradual", downtime=6, cost=6000),
    "bearing": dict(
        name=("Bearing wear", "Haus galas"),
        plain=("A bearing that carries the shaft is roughening, which shows up as sharper vibration and extra heat.",
               "Galas yang menyokong aci semakin kasar, ditunjukkan oleh getaran yang lebih tajam dan haba tambahan."),
        why=("Poor lubrication, contamination or misalignment slowly damages the rolling surfaces.",
             "Pelinciran yang lemah, pencemaran atau ketidaklurusan merosakkan permukaan galas secara perlahan."),
        signs=[("vib_kurtosis", "up"), ("vib_rms", "up"), ("gearbox_oil_temp", "up")],
        steps=(["Check grease or oil level and condition at the bearing.",
                "Listen and feel for roughness and heat with the press running.",
                "At the stop, lock out and remove the bearing housing cover.",
                "Replace the bearing and seals; clean and re-grease the housing.",
                "Restart and compare vibration with the earlier reading."],
               ["Semak paras dan keadaan gris atau minyak pada galas.",
                "Dengar dan rasa kekasaran serta haba semasa penekan berjalan.",
                "Pada waktu henti, kunci dan buka penutup rumah galas.",
                "Tukar galas dan sesendal; bersihkan dan gris semula rumah galas.",
                "Mulakan semula dan bandingkan getaran dengan bacaan sebelum ini."]),
        parts=[(("Shaft bearing", "Galas aci"), 2), (("Seal kit", "Set sesendal"), 1), (("Bearing grease (kg)", "Gris galas (kg)"), 1)],
        crew=2, hours=3.0, needs_stop=True, onset="gradual", downtime=8, cost=4500),
    "gearbox_shaft": dict(
        name=("Gearbox or shaft fault", "Kerosakan gear atau aci"),
        plain=("The gearbox or drive shaft is running hotter and rougher than normal, often from worn gear teeth or low oil.",
               "Kotak gear atau aci pemacu lebih panas dan kasar daripada biasa, selalunya kerana gigi gear haus atau minyak rendah."),
        why=("Worn gear teeth, shaft misalignment or degraded gear oil raise friction and heat.",
             "Gigi gear haus, aci tidak sejajar atau minyak gear merosot meningkatkan geseran dan haba."),
        signs=[("gearbox_oil_temp", "up"), ("vib_rms", "up"), ("current_per_tonne", "up")],
        steps=(["Check the gearbox oil level and take an oil sample.",
                "Look for metal particles on the magnetic plug.",
                "At the stop, check shaft alignment and coupling bolts.",
                "Change the gear oil and filter; inspect gear teeth through the inspection port.",
                "Replace the gear set or shaft if damage is found; log the findings."],
               ["Semak paras minyak kotak gear dan ambil sampel minyak.",
                "Cari serpihan logam pada palam magnet.",
                "Pada waktu henti, semak penjajaran aci dan bolt gandingan.",
                "Tukar minyak gear dan penapis; periksa gigi gear melalui lubang pemeriksaan.",
                "Tukar set gear atau aci jika rosak; catat penemuan."]),
        parts=[(("Gear oil (litres)", "Minyak gear (liter)"), 40), (("Oil filter", "Penapis minyak"), 1), (("Coupling bolt set", "Set bolt gandingan"), 1)],
        crew=3, hours=6.0, needs_stop=True, onset="gradual", downtime=14, cost=9000),
    "hydraulic_cone": dict(
        name=("Cone hydraulic fault", "Kerosakan hidraulik kon"),
        plain=("The hydraulic system that holds the pressing cone is unstable, so the squeeze on the fruit swings up and down.",
               "Sistem hidraulik yang menahan kon penekan tidak stabil, jadi tekanan pada buah berayun naik turun."),
        why=("Oil leaks, worn seals or a tired pump let the cone pressure wander.",
             "Kebocoran minyak, sesendal haus atau pam letih menyebabkan tekanan kon berubah-ubah."),
        signs=[("cone_pressure", "unstable"), ("cone_pressure", "up"), ("cone_pressure", "spike")],   # fingerprint rule v2: all on cone pressure (the signal the fault acts on)
        steps=(["Check the hydraulic oil level and look for leaks on hoses and fittings.",
                "Watch the cone pressure gauge for swings while running.",
                "At the stop, replace leaking hoses and worn seals.",
                "Change the hydraulic filter and top up with the right oil grade.",
                "Test the cone pressure under load before handing back."],
               ["Semak paras minyak hidraulik dan cari kebocoran pada hos dan penyambung.",
                "Perhatikan tolok tekanan kon untuk ayunan semasa berjalan.",
                "Pada waktu henti, tukar hos bocor dan sesendal haus.",
                "Tukar penapis hidraulik dan tambah minyak gred yang betul.",
                "Uji tekanan kon dengan beban sebelum diserahkan semula."]),
        parts=[(("Hydraulic hose", "Hos hidraulik"), 2), (("Seal kit", "Set sesendal"), 1), (("Hydraulic filter", "Penapis hidraulik"), 1)],
        crew=2, hours=3.0, needs_stop=True, onset="gradual", downtime=5, cost=3500),
    "electrical": dict(
        name=("Electrical fault", "Kerosakan elektrik"),
        plain=("The motor current is jumping around, which usually means a loose connection, worn contactor or failing motor winding.",
               "Arus motor melonjak-lonjak, biasanya akibat sambungan longgar, kontaktor haus atau belitan motor rosak."),
        why=("Heat cycling loosens terminals and ageing insulation or contactors cause intermittent faults.",
             "Kitaran haba melonggarkan terminal, dan penebat atau kontaktor yang tua menyebabkan kerosakan berselang-seli."),
        signs=[("current_per_tonne", "unstable"), ("current_per_tonne", "spike"), ("motor_current", "spike")],   # v2: load-normalised current; raw current swings with load
        steps=(["Check the controller alarm log for the last 24 hours.",
                "Inspect terminals and cable ends for heat marks; tighten loose ones.",
                "Check the contactor and overload relay for pitting or wear.",
                "Measure insulation resistance of the motor windings.",
                "Replace the faulty part and run a load test."],
               ["Semak log penggera pengawal untuk 24 jam lepas.",
                "Periksa terminal dan hujung kabel untuk kesan haba; ketatkan yang longgar.",
                "Semak kontaktor dan geganti beban lampau untuk lekuk atau haus.",
                "Ukur rintangan penebat belitan motor.",
                "Tukar bahagian yang rosak dan jalankan ujian beban."]),
        parts=[(("Contactor", "Kontaktor"), 1), (("Terminal and lug kit", "Set terminal dan lug"), 1)],
        crew=2, hours=2.0, needs_stop=True, onset="sudden", downtime=4, cost=2500),
    "boiler_steam": dict(
        name=("Steam temperature drift", "Sisihan suhu stim"),
        plain=("The boiler's steam is leaving the normal temperature band, often because of fouled tubes or poor feed-water control.",
               "Stim dandang keluar daripada julat suhu biasa, selalunya kerana tiub kotor atau kawalan air suapan lemah."),
        why=("Scale or ash on tubes, or wrong feed-water dosing, upsets heat transfer.",
             "Kerak atau abu pada tiub, atau dos air suapan yang salah, mengganggu pemindahan haba."),
        signs=[("steam_temp", "down"), ("steam_pressure", "unstable"), ("feedwater_flow", "down")],
        steps=(["Check feed-water dosing pump and chemical levels.",
                "Do a bottom blowdown and a water-glass check.",
                "Check the feed-water flow meter and control valve.",
                "Inspect soot blowers and look for tube fouling.",
                "Watch steam temperature for 30 minutes; call the boiler engineer if it keeps drifting."],
               ["Semak pam dos air suapan dan paras bahan kimia.",
                "Lakukan blowdown bawah dan semakan kaca paras air.",
                "Semak meter aliran air suapan dan injap kawalan.",
                "Periksa penghembus jelaga dan cari tiub yang kotor.",
                "Pantau suhu stim 30 minit; hubungi jurutera dandang jika masih menyimpang."]),
        parts=[(("Dosing chemicals", "Bahan kimia dos"), 1), (("Control valve gasket", "Gasket injap kawalan"), 1)],
        crew=2, hours=2.0, needs_stop=False, onset="gradual", downtime=8, cost=3000),
    "boiler_water": dict(
        name=("Feed-water quality drift", "Sisihan kualiti air suapan"),
        plain=("The water going into the boiler is getting dirtier, which can scale the tubes and lead to a tube leak.",
               "Air yang masuk ke dandang semakin kotor, boleh menyebabkan kerak pada tiub dan kebocoran tiub."),
        why=("A tired water-treatment plant or too little blowdown lets dissolved solids build up.",
             "Loji rawatan air yang letih atau blowdown terlalu sedikit menyebabkan pepejal terlarut bertambah."),
        signs=[("feedwater_cond", "up"), ("feedwater_cond", "unstable"), ("steam_temp", "down")],   # v2: pressure is not a water-quality sign; scale lowers steam temperature
        steps=(["Test feed-water conductivity and hardness.",
                "Check the softener or resin bed and regenerate if due.",
                "Increase blowdown until conductivity returns to normal.",
                "Check chemical dosing rates against the water-treatment plan.",
                "Plan a tube inspection at the next planned stop if it keeps rising."],
               ["Uji kekonduksian dan kekerasan air suapan.",
                "Semak pelembut atau lapisan resin dan jana semula jika sampai masa.",
                "Tambah blowdown sehingga kekonduksian kembali normal.",
                "Semak kadar dos bahan kimia mengikut pelan rawatan air.",
                "Rancang pemeriksaan tiub pada henti terancang seterusnya jika terus meningkat."]),
        parts=[(("Resin or softener salt", "Resin atau garam pelembut"), 1), (("Test reagent kit", "Set reagen ujian"), 1)],
        crew=2, hours=2.0, needs_stop=False, onset="gradual", downtime=8, cost=3000),
    "unknown": dict(
        name=("Unusual behaviour", "Tingkah laku luar biasa"),
        plain=("This machine is behaving differently from its own normal, but the pattern does not match a known fault yet.",
               "Mesin ini berkelakuan berbeza daripada normalnya sendiri, tetapi coraknya belum sepadan dengan kerosakan yang diketahui."),
        why=("Several signals moved at once without a clear single cause.",
             "Beberapa isyarat berubah serentak tanpa satu punca yang jelas."),
        signs=[("motor_current", "up"), ("cone_pressure", "up"), ("gearbox_oil_temp", "up"), ("vib_rms", "up")],   # v2: unknown = any one of the four rises
        steps=(["Walk around the machine and look, listen and smell for anything unusual.",
                "Check oil levels, guards and fasteners.",
                "Compare the readings with a healthy press running the same load.",
                "Inspect at the next planned stop and log what you find."],
               ["Berjalan mengelilingi mesin dan lihat, dengar dan hidu apa-apa yang luar biasa.",
                "Semak paras minyak, pengadang dan pengikat.",
                "Bandingkan bacaan dengan penekan sihat pada beban yang sama.",
                "Periksa pada henti terancang seterusnya dan catat penemuan."]),
        parts=[],
        crew=2, hours=2.0, needs_stop=True, onset="sudden", downtime=4, cost=3000),
}
SUMMARY = {   # line card summary per fault class (EN, MS); normal state below
    "worm_wear": ("Worm wearing", "Skru cacing haus"), "bearing": ("Bearing wearing", "Galas haus"),
    "gearbox_shaft": ("Gearbox running hot", "Kotak gear panas"), "hydraulic_cone": ("Cone pressure unstable", "Tekanan kon tidak stabil"),
    "electrical": ("Electrical fault", "Kerosakan elektrik"), "boiler_steam": ("Steam temperature drifting", "Suhu stim menyimpang"),
    "boiler_water": ("Feed-water drifting", "Air suapan menyimpang"), "unknown": ("Unusual behaviour", "Tingkah laku luar biasa")}
SUMMARY_OK = ("Normal", "Normal")
EXPECT_EN = {"up": "should rise", "down": "should fall", "unstable": "should swing more", "spike": "should show spikes"}
OBSERVED = {   # (kind) -> (EN, MS) templates; "normal" = the machine's own 30 days before the 5-day window
    "up": ("Up {pct:.0f}% compared with normal, in the last 5 days", "Naik {pct:.0f}% berbanding biasa dalam 5 hari lepas"),
    "down": ("Down {pct:.0f}% compared with normal, in the last 5 days", "Turun {pct:.0f}% berbanding biasa dalam 5 hari lepas"),
    "flat": ("No clear change compared with normal ({pct:+.0f}%)", "Tiada perubahan jelas berbanding biasa ({pct:+.0f}%)"),
    "unstable": ("Swinging {x:.1f}x more than normal", "Berayun {x:.1f}x lebih daripada biasa"),
    "steady": ("As steady as normal ({x:.1f}x)", "Sama stabil seperti biasa ({x:.1f}x)"),
    "spike": ("{n} spikes in 5 days", "{n} lonjakan dalam 5 hari"),
    "nospike": ("No spikes in 5 days", "Tiada lonjakan dalam 5 hari"),
    "nodata": ("Not enough data", "Data tidak mencukupi")}
HISTORY_WHAT = {
    True: ("{fault}: MillGuard warned before it failed", "{fault}: MillGuard memberi amaran sebelum rosak"),
    False: ("{fault}: broke down with no warning", "{fault}: rosak tanpa amaran")}

NOT_YET = ("Not yet: ", "Belum lagi: ")
STEADY_OBS = ("Holding steady ({pct:+.0f}%)", "Kekal stabil ({pct:+.0f}%)")
# ---- v1.7 labels
DAY_PART = {"today": ("today", "hari ini"), "tomorrow": ("tomorrow", "esok")}
DEADLINE_NOW = ("within {h} hours, by {clock}", "dalam {h} jam, sebelum {clock}")
DEADLINE_STOP_TOMORROW = ("tomorrow's 06:00 planned stop", "henti terancang esok jam 06:00")
DEADLINE_STOP_DAY = ("the {day} 06:00 planned stop", "henti terancang {day} jam 06:00")
WINDOW_NEXT = ("before the next planned stop, {day} 06:00", "sebelum henti terancang seterusnya, {day} jam 06:00")
WINDOW_AFTER = ("before the planned stop after next, {day} 06:00 (counted up to 168 hours)",
                "sebelum henti terancang selepas yang seterusnya, {day} jam 06:00 (dikira sehingga 168 jam)")
LAST_SERVICE = {"press": ("Last repair logged on {asset}: {fault}", "Pembaikan terakhir direkodkan bagi {asset}: {fault}"),
                "none": ("No repair logged yet this year", "Tiada pembaikan direkodkan setakat ini tahun ini")}
NEXT_CHECK = ("Next planned stop", "Henti terancang seterusnya")
SERIES_SUMMARY = ("{a} to {b} {unit} over {days} days", "{a} kepada {b} {unit} dalam {days} hari")
SERIES_LIMIT = {"fibre_oil_loss": 4.0, "gearbox_oil_temp": 80.0, "vib_rms": 3.2, "cone_pressure": 57.0, "steam_temp": 530.0}
SERIES_LABEL = {"feedwater_flow": (("Feed-water flow per tonne of fruit", "Aliran air suapan setiap tan buah"), "t/t")}
OUTLOOK_NOTE = ("Looks 168 hours (7 days) ahead, further than the alert rule. Not confirmed yet, so no alert.",
                "Melihat 168 jam (7 hari) ke hadapan, lebih jauh daripada peraturan amaran. Belum disahkan, jadi tiada amaran.")
OUTLOOK_HANDLED = ("Already handled on {day} at {clock}. No new alert until the risk clears; the figures restart from zero.",
                   "Sudah ditangani pada {day} jam {clock}. Tiada amaran baharu sehingga risiko reda; angka bermula semula dari sifar.")
EXTRA_SERIES = {   # reason signals that are not raw telemetry: label (EN, MS), unit
    "hours_since_service": (("Hours since the last logged repair", "Jam sejak pembaikan terakhir direkodkan"), "hours"),
    "alarms": (("Controller alarms per day", "Penggera pengawal setiap hari"), "alarms"),
    "load": (("Mill load", "Beban kilang"), "t/h")}
COST_EXPLAIN_PRESS = ("A press breakdown costs {h} hours x RM{per_press_h:,.0f} per press-hour x {share:.0%} truly lost + repair cost x {mult} "
                      "(about RM{total:,.0f} for worm wear)",)
COST_EXPLAIN_BOILER = ("A boiler breakdown costs {h} hours x RM{per_mill_h:,.0f} per mill-hour (the whole mill stops) x {share:.0%} truly lost + repair cost x {mult} "
                       "(about RM{total:,.0f})",)

# ---- v1.8 Telegram messages (same facts as the app; EN and BM per subscriber) ----
NOTIFY = {
    "alert": ("⚠️ {asset} · {fault} · {risk}% chance it fails {window} · {rec} · Protects RM{saved:,}\nWhy: {reason}\nWhen: {deadline}",
              "⚠️ {asset} · {fault} · {risk}% kemungkinan rosak {window} · {rec} · Melindungi RM{saved:,}\nSebab: {reason}\nBila: {deadline}"),
    "rec_fix_now": ("Fix now", "Baiki sekarang"),
    "rec_schedule": ("Schedule for {deadline}", "Jadualkan untuk {deadline}"),
    "brief_head": ("🌙 MillGuard · {shift} shift brief · {clock}", "🌙 MillGuard · ringkasan syif {shift} · {clock}"),
    "shift": {"night": ("night", "malam"), "day": ("day", "siang")},
    "brief_line": ("{i}. {asset} · {fault} · {risk}% · {rec} · Protects RM{saved:,}",
                   "{i}. {asset} · {fault} · {risk}% · {rec} · Melindungi RM{saved:,}"),
    "brief_total": ("Total protected: RM{total:,}", "Jumlah dilindungi: RM{total:,}"),
    "brief_none": ("✅ Nothing needs you {when}. Watching {w} machine(s).", "✅ Tiada tindakan diperlukan {when}. Memantau {w} mesin."),
    "when": {"night": ("tonight", "malam ini"), "day": ("today", "hari ini")},
    "buttons": {"fix_now": ("Fix now", "Baiki sekarang"), "schedule_next_stop": ("Schedule", "Jadualkan"),
                "monitor": ("Keep watching", "Terus pantau")},
    "scheduled": ("📅 Scheduled by the shift supervisor — {asset}: {fault}. Do it at {deadline} (planned stop). Expected loss avoided: RM{saved:,}. Engineers on this group have been notified.",
                  "📅 Dijadualkan oleh penyelia syif — {asset}: {fault}. Buat pada {deadline} (henti terancang). Kerugian dielakkan: RM{saved:,}. Jurutera dalam kumpulan ini telah dimaklumkan."),
    "recorded": ("Recorded: {choice}. Thank you.", "Direkodkan: {choice}. Terima kasih."),
    "start": ("Subscribed to MillGuard alerts (English). Use /bm for Bahasa Malaysia, /brief for the current brief.",
              "Dilanggan kepada amaran MillGuard (Bahasa Malaysia). Guna /en untuk bahasa Inggeris, /brief untuk ringkasan semasa."),
    "lang_set": ("Language set to English.", "Bahasa ditetapkan kepada Bahasa Malaysia."),
    "not_allowed": ("This chat is not on the allowed list.", "Sembang ini tiada dalam senarai dibenarkan."),
    "budget": ("(Alert limit for this shift reached; more are in the app.)", "(Had amaran untuk syif ini dicapai; selebihnya ada dalam aplikasi.)"),
}

ASSUMPTION_LABEL = {
    "economics.throughput_tph": "Mill throughput (tonnes of fruit per hour)",
    "economics.presses": "Number of screw presses",
    "economics.press_throughput_tph": "Throughput of one press (tonnes of fruit per hour)",
    "economics.oer": "Oil extraction rate (OER)",
    "economics.cpo_price_rm_per_t": "CPO price (RM per tonne)",
    "economics.cpo_price_slider_min": "Lowest CPO price on the slider (RM per tonne)",
    "economics.cpo_price_slider_max": "Highest CPO price on the slider (RM per tonne)",
    "economics.rm_per_mill_hour": "Value of one mill-hour (RM per hour)",
    "economics.rm_per_press_hour": "Value of one press-hour (RM per hour)",
    "economics.unplanned_press_stop_h": "Hours a press is down after a breakdown",
    "economics.unplanned_boiler_stop_h": "Hours the mill is down after a boiler breakdown",
    "economics.planned_repair_extra_lost_h": "Extra production hours lost by a planned repair",
    "economics.repair_stop_h_press": "Press stop needed for a fix-now repair (hours)",
    "economics.repair_stop_h_boiler": "Boiler stop needed for a fix-now repair (hours)",
    "economics.unplanned_repair_multiplier": "Parts cost multiplier for an unplanned breakdown",
    "economics.lost_share": "Share of stopped production truly lost (base case)",
    "economics.lost_share_low": "Share of stopped production truly lost (low case)",
    "economics.lost_share_high": "Share of stopped production truly lost (high case)",
    "economics.false_alarm_cost_rm": "Cost of checking a machine after a false alarm (RM)",
    "economics.miss_cost_mult": "Breakdown cost multiplier (slider)",
    "economics.criticality_boiler": "Share of the mill stopped when the boiler fails",
    "economics.criticality_press": "Share of the mill stopped when one press fails",
    "repair_cost_rm.worm_wear": "Planned repair cost: worm wear (RM)",
    "repair_cost_rm.bearing": "Planned repair cost: bearing wear (RM)",
    "repair_cost_rm.gearbox_shaft": "Planned repair cost: gearbox or shaft (RM)",
    "repair_cost_rm.hydraulic_cone": "Planned repair cost: cone hydraulics (RM)",
    "repair_cost_rm.electrical": "Planned repair cost: electrical (RM)",
    "repair_cost_rm.boiler_steam": "Planned repair cost: steam temperature drift (RM)",
    "repair_cost_rm.boiler_water": "Planned repair cost: feed-water quality (RM)",
    "repair_cost_rm.unknown": "Planned repair cost: unknown fault (RM)",
    "simulator.n_mills": "Simulated mills",
    "simulator.months": "Simulated months",
    "simulator.step_h": "Simulation time step (hours)",
    "simulator.life_mu_worm_wear": "Worm life, lognormal mu (ln running hours)",
    "simulator.life_sigma_worm_wear": "Worm life, lognormal sigma",
    "simulator.life_mu_bearing": "Bearing life, lognormal mu (ln running hours)",
    "simulator.life_sigma_bearing": "Bearing life, lognormal sigma",
    "simulator.life_mu_gearbox_shaft": "Gearbox or shaft life, lognormal mu (ln running hours)",
    "simulator.life_sigma_gearbox_shaft": "Gearbox or shaft life, lognormal sigma",
    "simulator.life_h_min_hydraulic_cone": "Shortest cone hydraulics life (running hours)",
    "simulator.life_h_max_hydraulic_cone": "Longest cone hydraulics life (running hours)",
    "simulator.life_min_margin_h": "Minimum life above the warning period (hours)",
    "simulator.reference_breakdowns_7_months": "Real North Sumatra mill: press breakdowns in 7 months",
    "simulator.cone_pressure_max_bar": "Cone hydraulic pressure limit (bar)",
    "simulator.fibre_oil_loss_alarm": "Oil-in-fibre alarm line",
    "simulator.target_stops_per_mill_year": "Target unplanned stops per mill per year (range)",
    "simulator.messy_work_order_share": "Share of work orders with unclear fault class",
    "simulator.weekly_planned_stop_h": "Weekly planned stop length (hours)",
    "simulator.missing_reading_rate": "Share of sensor readings missing",
    "simulator.crop_index_2025": "Crop index by month (relative to the annual mean)",
    "simulator.pf_h_worm_wear": "Warning period before worm failure (running hours)",
    "simulator.pf_h_gearbox_shaft": "Warning period before gearbox or shaft failure (running hours)",
    "simulator.pf_h_bearing": "Warning period before bearing failure (running hours)",
    "simulator.bearing_rms_rise": "Bearing wear: rise of vibration level at failure (fraction of normal)",
    "simulator.bearing_kurtosis_rise": "Bearing wear: rise of vibration spikiness at failure (kurtosis points)",
    "simulator.bearing_ramp_shape": "Bearing wear ramp shape (measured on run-to-failure bearings)",
    "simulator.pf_h_hydraulic_cone": "Warning period before cone hydraulic failure (running hours)",
    "alerting.persistence_h": "Hours risk must stay above the line before alerting",
    "alerting.max_per_shift": "Maximum alerts per shift",
    "alerting.horizon_h": "Alert look-ahead (hours)",
    "alerting.hysteresis_ratio": "Alert stays open until risk falls below this share of the line",
    "alerting.inspection_finds_wrong_class": "Chance an inspection still finds the fault when the predicted class is wrong",
    "alerting.fix_now_response_h": "Time to start a fix-now repair (hours)",
    "alerting.clear_hours": "Hours below the line before an alert clears",
    "alerting.min_lead_h": "Shortest useful lead time before a stop (hours)",
    "fixed_schedule.interval_h_worm_wear": "Fixed schedule: replace worm every (running hours, published RCM)",
    "fixed_schedule.interval_h_bearing": "Fixed schedule: replace bearing every (running hours, published RCM)",
    "fixed_schedule.interval_h_gearbox_shaft": "Fixed schedule: service gearbox or shaft every (running hours, published RCM)",
    "fixed_schedule.hydraulic_cone_electrical": "Fixed schedule: cone hydraulics and electrical have no published interval",
}
POLICY_LABEL = {"fixed_interval": ("Fixed schedule (published RCM intervals)", "Jadual tetap (selang RCM terbitan)")}
BACKTEST_APPROX = ("After an early repair, the part is treated as renewed; its slightly earlier next wear-out is not modelled "
                   "(median warning about 70 h vs average part lives of 600–1,000 h).")


# ---- v1.14 sensor alerts (never machine alerts) ----
SENSOR_NAME = {"current": ("motor current", "arus motor"), "vibration": ("vibration", "getaran"), "oil_temp": ("gearbox oil temperature", "suhu minyak gear"),
               "cone_pressure": ("cone pressure", "tekanan kon"), "steam_temp": ("steam temperature", "suhu stim"),
               "steam_pressure": ("steam pressure", "tekanan stim"), "feedwater_flow": ("feed-water flow", "aliran air suapan"),
               "feedwater_cond": ("feed-water conductivity", "kekonduksian air suapan"), "fibre": ("oil-in-fibre lab", "makmal minyak dalam serabut"),
               "throughput": ("throughput", "kadar suapan")}
SENSOR_MSG = {
    "stuck": ("{asset} {sensor} sensor looks faulty: the reading is frozen. Check the sensor, not the machine",
              "Penderia {sensor} {asset} nampak rosak: bacaan beku. Periksa penderia, bukan mesin"),
    "spike": ("{asset} {sensor} sensor looks faulty: a reading jumped far outside its normal range. Check the sensor, not the machine",
              "Penderia {sensor} {asset} nampak rosak: bacaan melonjak jauh di luar julat biasa. Periksa penderia, bukan mesin"),
    "out_of_range": ("{asset} {sensor} sensor looks faulty: the reading is outside what is physically possible. Check the sensor, not the machine",
                     "Penderia {sensor} {asset} nampak rosak: bacaan di luar julat yang mungkin. Periksa penderia, bukan mesin"),
    "missing": ("{asset} {sensor} sensor has stopped reporting. Check the sensor and its cable, not the machine",
                "Penderia {sensor} {asset} berhenti melapor. Periksa penderia dan kabelnya, bukan mesin")}
NOTIFY["sensor"] = ("🔧 Sensor check: {msg}", "🔧 Semakan penderia: {msg}")

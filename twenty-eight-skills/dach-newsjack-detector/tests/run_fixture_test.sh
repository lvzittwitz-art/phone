#!/usr/bin/env bash
# Fixture-Test für detector_de.py: zwei Läufe gegen lokale Feeds, Asserts auf candidates.json.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT
NOW="2026-11-06T09:00:00Z"

RUN1="$(python3 -I scripts/detector_de.py run --profile tests/profile.fixture.json --fixture-dir tests/fixtures --out "$OUT" --now "$NOW")"
python3 -I - "$RUN1/candidates.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
cands = {c["headline"]: c for c in d["candidates"]}
rej = {r["headline"]: r for r in d["rejected"]}
blocked = {b["headline"]: b for b in d["brand_safety_blocks"]}
errors = {e["feed_id"]: e for e in d["feed_errors"]}
def ok(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond: sys.exit(1)

# Duplikat über zwei Feeds (Umlaut-Variante) -> ein Cluster mit zwei Quellen, first_seen vom IAB-Eintrag
dup = [c for c in d["candidates"] if "jede dritte firma" in c["headline"].lower()]
ok(len(dup) == 1, "Duplikat Fachkräftemangel/Fachkraeftemangel zu einem Cluster zusammengefasst")
ok(dup[0]["source_count"] == 2 and set(dup[0]["sources"]) == {"tagesschau", "iab"}, "Cluster hat source_count 2 (tagesschau + iab)")
ok(dup[0]["first_seen"].startswith("2026-11-06T05:50"), "first_seen ist die früheste Veröffentlichung (05:50Z)")
ok(dup[0]["age_bucket"] == "4h", "Alter 3h10 -> Bucket 4h")
ok("Fachkräfte" in dup[0]["term_hits"] and "Azubi" in dup[0]["term_hits"], "umlaut-tolerante Treffer: Fachkräfte, Azubi")

# Gleiche kanonische URL (utm entfernt) über zwei Feeds
al = [c for c in d["candidates"] if c["headline"].startswith("Arbeitslosenzahl im Oktober")]
ok(len(al) == 1 and al[0]["source_count"] == 2, "URL-Dedupe: utm-Parameter entfernt, tagesschau + presseportal ein Cluster")
ok(al[0]["age_bucket"] == "30min", "Arbeitslosenzahl 08:40Z -> Bucket 30min")
ok(al[0]["queue_priority"] <= 2, "Frischester Leitmedien-Treffer mit zwei Quellen steht in den Top 2")

# Brand-Safety
ok(any("Messerangriff" in h for h in blocked), "Messerangriff/Tote im brand_safety_blocks")
ok(not any("Messerangriff" in h for h in cands), "Safety-Item nicht in candidates")
ok(any("Wer kriegt den Job" in h for h in cands), "'kriegt' und 'gewaltiger' lösen keinen Safety-Block aus")

# Ausschluss
ok(any("Bundesliga" in h and r["reject_reason"].startswith("Ausschluss") for h, r in rej.items()), "Bundesliga-Item per Ausschlussbegriff verworfen")
ok(any("Gewinnspiel" in h and r["reject_reason"].startswith("Ausschluss") for h, r in rej.items()), "Gewinnspiel-PR per Ausschlussbegriff verworfen")

# Alter
old = rej.get("Studie: Homeoffice-Anteil stagniert bei einem Viertel")
ok(old is not None and old["age_bucket"] == "monat" and old["reject_reason"].startswith("zu alt"), "17 Tage altes Item -> Bucket monat, verworfen")
ka = cands.get("Kurzarbeit steigt in der Industrie deutlich")
ok(ka is not None and ka["age_bucket"] == "24h", "21h altes Item -> Bucket 24h")
hw = [c for c in d["candidates"] if c["headline"].startswith("Handwerk warnt")]
ok(len(hw) == 1 and hw[0]["age_bucket"] == "woche", "5 Tage altes Item -> Bucket woche, bleibt Kandidat")

# Wettbewerber
ss = [c for c in d["candidates"] if c["headline"].startswith("StepStone")]
ok(len(ss) == 1 and ss[0]["competitor_hits"] == ["StepStone"], "StepStone als competitor_hit markiert")

# Irrelevantes
ok(rej["Wetter: Sonniger Herbst hält bis zum Wochenende"]["reject_reason"] == "kein Profilbegriff getroffen", "Wetter ohne Begriffstreffer verworfen")

# Feed-Fehler
ok("missing-feed" not in errors and d["run_meta"]["feeds_total"] == 3, "Unbekannte feed_id wird mit Warnung übersprungen")
ok(all(0 <= c["mechanical_score"] <= 100 for c in d["candidates"]), "Scores im Bereich 0-100")
ok(all(c["new_or_grown"] == "neu" for c in d["candidates"]), "Erster Lauf: alle Kandidaten 'neu'")
print(f"Lauf 1: {len(d['candidates'])} Kandidaten, {len(d['rejected'])} verworfen, {len(d['brand_safety_blocks'])} geblockt")
PY
test -f "$RUN1/run.md" && echo "PASS run.md geschrieben"
test -f "$OUT/seen.json" && echo "PASS seen.json geschrieben"

RUN2="$(python3 -I scripts/detector_de.py run --profile tests/profile.fixture.json --fixture-dir tests/fixtures --out "$OUT" --now "2026-11-06T09:30:00Z")"
python3 -I - "$RUN2/candidates.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
seen = sum(1 for r in d["rejected"] if r["reject_reason"].startswith("bereits gesehen"))
if d["candidates"]:
    print("FAIL Zweiter Lauf ohne neue Items liefert Kandidaten:", [c["headline"] for c in d["candidates"]]); sys.exit(1)
print(f"PASS Zweiter Lauf: 0 neue Kandidaten, {seen} als 'bereits gesehen' verworfen")
PY
echo "ALLE TESTS BESTANDEN"

#!/usr/bin/env bash
# Selbsttest für geo-content-optimizer-v2. Aufruf aus dem Skill-Ordner: bash tests/run_tests.sh
set -euo pipefail
cd "$(dirname "$0")/.."
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fail=0
ok() { echo "PASS  $1"; }
ko() { echo "FAIL  $1"; fail=1; }

# 1. html_to_md
python3 -I scripts/html_to_md.py tests/fixture_page.html > "$TMP/page.md"
grep -q '^# GEO PR' "$TMP/page.md" && ok "html_to_md: H1 erkannt" || ko "html_to_md: H1 fehlt"
grep -q 'Newsletter' "$TMP/page.md" && ko "html_to_md: aside nicht entfernt" || ok "html_to_md: aside/nav/footer entfernt"
grep -q 'Ähnliche Beiträge' "$TMP/page.md" && ko "html_to_md: related nicht entfernt" || ok "html_to_md: class=related entfernt"
grep -q '| Kriterium | SEO |' "$TMP/page.md" && ok "html_to_md: Tabelle konvertiert" || ko "html_to_md: Tabelle fehlt"
grep -q '\[Peec AI\](https://www.peec.ai/)' "$TMP/page.md" && ok "html_to_md: Link erhalten" || ko "html_to_md: Link fehlt"

# 2. analyze_de
python3 -I scripts/analyze_de.py tests/fixture_original.md --html tests/fixture_page.html --today 2026-11-06 > "$TMP/vorher.json"
python3 -I scripts/analyze_de.py tests/fixture_revised.md --today 2026-11-06 > "$TMP/nachher.json"
python3 -I - "$TMP/vorher.json" "$TMP/nachher.json" <<'EOF' && ok "analyze_de: Vorher/Nachher plausibel" || ko "analyze_de: Erwartungen verletzt"
import json, sys
v = json.load(open(sys.argv[1])); n = json.load(open(sys.argv[2]))
assert v["meta"]["sprache"] == "de"
assert len(v["POS-DOC"]["fluff_im_einstieg"]) >= 3 and n["POS-DOC"]["fluff_im_einstieg"] == []
assert v["QA"]["frage_headings"] == 0 and n["QA"]["frage_headings"] >= 3
assert v["TAKEAWAYS"]["pass"] is False and n["TAKEAWAYS"]["pass"] is True
assert v["DEFINITIVE"]["hedges_gesamt"] >= 5 and n["DEFINITIVE"]["hedges_gesamt"] == 0
assert n["KONKRETHEIT"]["dichte_pct"] > v["KONKRETHEIT"]["dichte_pct"]
assert v["FRESH"]["date_modified"] == "2025-09-02" and v["FRESH"]["tage_seit_update"] == 430
assert v["FRESH"]["veraltete_jahresangabe"] is True
assert v["TABLE"]["html_tabellen"] == 1 and n["TABLE"]["markdown_tabellen"] == 1
assert "Article" in v["SCHEMA"]["json_ld_typen"] and v["SCHEMA"]["hreflang_alternates"] == 1
assert v["READ"]["lix"] and v["READ"]["wiener_sachtextformel_1"]
assert "Studien zeigen" in v["KONKRETHEIT"]["generische_referenzen"]
EOF

# 3. check_rewrite_de
if python3 -I scripts/check_rewrite_de.py tests/fixture_original.md tests/fixture_revised.md --allow-placeholders > "$TMP/cr.txt"; then ok "check_rewrite: PASS mit Platzhalter-Erlaubnis"; else ko "check_rewrite: unerwarteter FAIL"; cat "$TMP/cr.txt"; fi
grep -q 'frage      H2 Grundlagen' "$TMP/cr.txt" && ok "check_rewrite: Frage-Umformulierung erkannt" || ko "check_rewrite: Frage-Umformulierung nicht erkannt"
grep -q 'erlaubt    H2 Das Wichtigste' "$TMP/cr.txt" && ok "check_rewrite: Takeaway-Heading erlaubt" || ko "check_rewrite: Takeaway-Heading nicht erlaubt"
grep -q 'NEU, vor Veröffentlichung belegen' "$TMP/cr.txt" && ok "check_rewrite: neue Zahlen gelistet" || ko "check_rewrite: neue Zahlen fehlen"
if python3 -I scripts/check_rewrite_de.py tests/fixture_original.md tests/fixture_revised.md > "$TMP/cr2.txt"; then ko "check_rewrite: Platzhalter nicht beanstandet"; else grep -q 'Platzhalter' "$TMP/cr2.txt" && ok "check_rewrite: Platzhalter führt zu FAIL" || ko "check_rewrite: FAIL ohne Platzhalter-Grund"; fi
# Zahl entfernen → FAIL
sed 's/Im Jahr 2024/Vor einiger Zeit/' tests/fixture_revised.md > "$TMP/drop.md"
if python3 -I scripts/check_rewrite_de.py tests/fixture_original.md "$TMP/drop.md" --allow-placeholders > "$TMP/cr3.txt"; then ko "check_rewrite: fehlende Zahl nicht erkannt"; else grep -q 'FEHLEN im neuen Text: 2024' "$TMP/cr3.txt" && ok "check_rewrite: fehlende Zahl erkannt" || ko "check_rewrite: FAIL ohne Zahlengrund"; fi
# Überschrift gelöscht → FAIL
grep -v '^## Fazit' tests/fixture_revised.md > "$TMP/noh.md"
if python3 -I scripts/check_rewrite_de.py tests/fixture_original.md "$TMP/noh.md" --allow-placeholders > /dev/null; then ko "check_rewrite: gelöschte Überschrift nicht erkannt"; else ok "check_rewrite: gelöschte Überschrift erkannt"; fi
# frei-Politik → kein FAIL wegen Überschriften
python3 -I scripts/check_rewrite_de.py tests/fixture_original.md "$TMP/noh.md" --allow-placeholders --heading-policy frei > /dev/null && ok "check_rewrite: Politik frei berichtet nur" || ko "check_rewrite: Politik frei schlägt fehl"

# 4. build_doc
python3 -I scripts/build_doc.py tests/audit.example.json > "$TMP/audit.html"
grep -q '<!DOCTYPE html>' "$TMP/audit.html" && grep -q 'Vorher / Nachher' "$TMP/audit.html" && grep -q 'Überarbeitete Fassung' "$TMP/audit.html" && grep -q '#2E1214' "$TMP/audit.html" && ok "build_doc: HTML mit allen Sektionen und CI-Farbe" || ko "build_doc: Sektionen fehlen"
grep -q '<table><tr><th>Kriterium</th>' "$TMP/audit.html" && ok "build_doc: Markdown-Tabelle des Artikels gerendert" || ko "build_doc: Artikel-Tabelle fehlt"

echo
if [ "$fail" -eq 0 ]; then echo "ALLE TESTS BESTANDEN"; else echo "TESTS FEHLGESCHLAGEN"; exit 1; fi

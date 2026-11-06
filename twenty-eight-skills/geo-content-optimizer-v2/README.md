# geo-content-optimizer-v2

Nachfolger des Skills `geo-content-optimizer` von Twenty-Eight. Gleiche 12 Kriterien, gleiche Stimme, neu dazu: Messung, Schutzprüfung, Evidenzbasis mit Status, Kundendokument.

## Was v2 anders macht

| | v1 | v2 |
|---|---|---|
| Audit | Urteil | Urteil plus Messwerte aus `analyze_de.py`, Vorher/Nachher |
| Belege | Zahlen aus Guides ohne Status | `references/evidenz.md` mit primär / sekundär / Hausregel, nur primär im Kundendokument |
| Überarbeitung | frei | `check_rewrite_de.py`: Überschriften nur als Frage umformulieren, Zahlen und Links müssen erhalten bleiben, Platzhalter blockieren die Auslieferung |
| Lieferung | Dateien | Google Doc im Twenty-Eight-Look über `build_doc.py`, plus Markdown |
| Seitenauswahl | manuell | optional über Peec-AI-Actions |

## Herkunft

Architektur und Faktor-IDs übernommen aus `aeo-content-structure-optimizer` von Nectiv Digital (github.com/Nectiv-Digital/nectiv-claude-skills, MIT). Alle Skripte neu geschrieben für Deutsch:

- **Konkretheit statt Entity-Dichte.** Die englische Heuristik zählt großgeschriebene Wörter. Im Deutschen sind alle Nomen groß. `analyze_de.py` zählt Zahlen, Jahre, Prozent, Währung, Akronyme, Binnenmajuskeln, Firmen mit Rechtsform, Domains und per `--entities` gelistete Kundennamen.
- **Lesbarkeit**: LIX und Wiener Sachtextformel 1 statt Flesch-Kincaid.
- **Frage-Überschriften** auch ohne Fragezeichen (Was, Wie, Warum, Welche, Lohnt sich, Kann …).
- **Deutsche Lexika** für Hedges, vage Quantoren, Floskel-Einstiege, generische Referenzen, Takeaway-Überschriften, Pronomen-Einstiege, CTA.
- **Deutsche Datumsformate** (12.03.2026, 12. März 2026, Stand: März 2026) plus JSON-LD, Meta und `<time>`.
- **Rewrite-Check** prüft zusätzlich Zahlen, Links, neue Zahlen und Platzhalter; Überschriften-Politik wählbar (strict / fragen / frei).
- **Answer-Capsule-Messung** (40–60 Wörter unter jeder H2/H3) und **CTA-Verteilung** als Twenty-Eight-Hausregeln.

## Installation

Ordner in die Skill-Synchronisation (Cowork) oder nach `~/.claude/skills/` kopieren. Die Skripte brauchen Python 3.10+ und keine Fremdpakete. Für URL-Audits zusätzlich `curl`.

## Selbsttest

```bash
bash tests/run_tests.sh
```

## Nutzung in Kurzform

```bash
curl -sSL -A "Mozilla/5.0" "https://kunde.de/seite" -o seite.html
python3 -I scripts/html_to_md.py seite.html > seite.md
python3 -I scripts/analyze_de.py seite.md --html seite.html --entities entities.txt > vorher.json
# … Audit, Überarbeitung nach SKILL.md …
python3 -I scripts/check_rewrite_de.py seite.md ueberarbeitet.md --allow-placeholders
python3 -I scripts/analyze_de.py ueberarbeitet.md --entities entities.txt > nachher.json
python3 -I scripts/build_doc.py audit.json > audit.html   # → Google Drive hochladen
```

## Offene Punkte

- Die Tabelle „Offen“ in `references/evidenz.md` listet sieben kursierende Zahlen ohne gesicherte Primärquelle. Beim nächsten Online-Lauf verifizieren oder streichen.
- Konkretheits-Schwellen (≥ 8 % gesamt, ≥ 12 % Einstieg) sind erste Richtwerte. Nach zehn Audits mit echten Kundenseiten kalibrieren.
- Satztrennung und Silbenzählung sind regelbasiert. Für Fachtexte mit vielen Abkürzungen stichprobenartig prüfen.

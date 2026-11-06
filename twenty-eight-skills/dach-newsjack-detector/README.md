# dach-newsjack-detector

Reaktives PR-Monitoring für den deutschsprachigen Raum: deutsche RSS/Atom-Feeds einlesen, gleiche Geschichten clustern, grob nach Kundenprofil filtern, Kandidaten für die Pitch-Triage ausgeben. Erstes Profil: Indeed (Arbeitsmarkt).

## Herkunft

Die Architektur (Sammeln, Clustern, Story-Origin, Frische-Gate, Standing-Triage, Seen-State, Slack-Zustellung) stammt aus den Skills `newsjack-detector` und `newsjack-monitor-setup` des Projekts [elvisun/newsjack](https://github.com/elvisun/newsjack) (MIT-Lizenz). Hier neu umgesetzt:

- Python 3, ausschließlich Standardbibliothek, kein Go-Binary, kein Installer, kein Auto-Update.
- Deutscher Feed-Katalog (Leitmedien, Arbeitsmarkt-Institutionen, HR-Fachpresse, Regionalsender, Presseportale, Politik).
- Keine Medialyst- oder X-API. Journalist:innen kommen aus `medien-targeting` (Blinq).
- Umlaut-tolerante Begriffssuche, deutsches Brand-Safety-Lexikon.
- Das Skript bewertet nur mechanisch. Standing und Pitch-Urteil bleiben beim Agenten, siehe `SKILL.md`.

## Dateien

```
SKILL.md                      Anleitung für den Agenten
README.md                     diese Datei
scripts/detector_de.py        Sammeln, Clustern, Bewerten, Ausgabe
scripts/feeds_de.json         Feed-Katalog nach Lanes
templates/profile.example.json  Kundenprofil (Indeed)
templates/brief.example.md    Pitch-Brief (was gepitcht wird, was nicht)
tests/run_fixture_test.sh     Offline-Test gegen lokale Fixture-Feeds
tests/fixtures/*.xml          drei Beispiel-Feeds (RSS, Atom, Presseportal)
tests/profile.fixture.json    Testprofil
```

## Installation

Keine Abhängigkeiten. Python 3.11 oder neuer.

```bash
cp -R dach-newsjack-detector ~/.claude/skills/        # oder in .claude/skills/ eines Projekts
cd ~/.claude/skills/dach-newsjack-detector
bash tests/run_fixture_test.sh                        # muss "ALLE TESTS BESTANDEN" melden
python3 -I scripts/detector_de.py feeds --check       # Feeds mit verify:true bestätigen
```

`feeds --check` ruft jeden Feed einmal ab. Feeds, die 404 oder XML-Fehler liefern, in `feeds_de.json` korrigieren oder entfernen. Einträge mit `"verify": true` sind Katalog-Einträge, deren URL beim Erstellen nicht bestätigt werden konnte.

## Profil anlegen

```bash
mkdir -p kunden/<kunde>
cp templates/profile.example.json kunden/<kunde>/profile.json
cp templates/brief.example.md   kunden/<kunde>/brief.md
# Felder anpassen, dann:
python3 -I scripts/detector_de.py profile --validate kunden/<kunde>/profile.json
```

Pflicht: `company`, `search_terms` (10 bis 20), `lanes`, `timezone`. `feed_ids` wählt einzelne Feeds aus dem Katalog; fehlt das Feld, werden alle Feeds der angegebenen Lanes genutzt. `exclusions` werfen Cluster vor der Bewertung raus. `spokespeople` mit `status: prüfen` sind Platzhalter bis zur Freigabe.

## Lauf

```bash
python3 -I scripts/detector_de.py run --profile kunden/indeed/profile.json --out kunden/indeed/runs
```

Ergebnis in `kunden/indeed/runs/<Zeitstempel>/`:

- `candidates.json` mit `run_meta`, `candidates`, `rejected`, `brand_safety_blocks`, `feed_errors`.
- `run.md`, lesbare Kurzfassung.
- `kunden/indeed/runs/seen.json`, Gedächtnis über Läufe hinweg. Löschen, um alles erneut zu sehen.

Optionen: `--feeds` (anderer Katalog), `--fixture-dir` (lokale `<feed_id>.xml` statt HTTP), `--now` (Referenzzeit ISO 8601, für Tests).

Mechanischer Score (0 bis 100): Frische bis 40, Quellenübereinstimmung bis 20, Begriffstreffer bis 25, Lane bis 15. Er sortiert nur die Warteschlange.

## Planen

Zwei Läufe täglich reichen für Monatszahlen und Tagesdebatten. Empfehlung 7:00 und 14:00 Uhr Europe/Berlin.

- **Claude Code Routine:** Routine mit dem Prompt "Führe den Detector-Lauf für Indeed aus und triagiere nach SKILL.md" anlegen.
- **Make-Szenario:** Szenario ruft das Skript auf einem Rechner mit Repo-Zugriff auf, übergibt `run.md` an den Agenten und postet dessen Bericht per bestehendem Slack-Webhook. Der Webhook bleibt in Make.
- **cron:** `0 7,14 * * 1-5 cd /pfad && python3 -I scripts/detector_de.py run --profile kunden/indeed/profile.json --out kunden/indeed/runs`

## Feed ergänzen

In `scripts/feeds_de.json` unter `feeds` einen Eintrag anlegen:

```json
{"id": "kurz-eindeutig", "name": "Anzeigename", "url": "https://…/rss", "lane": "leitmedien", "language": "de", "notes": "…"}
```

Lanes: `leitmedien`, `arbeitsmarkt`, `fachpresse_hr`, `wirtschaft_regional`, `presseportale`, `politik`. Neue Lane unter `lanes` mit `gewicht` anlegen. Danach `feeds --check`.

## Test

```bash
bash tests/run_fixture_test.sh
```

Prüft gegen drei lokale Fixture-Feeds: Duplikat über zwei Feeds inklusive Umlaut-Variante, URL-Dedupe mit utm-Parametern, Brand-Safety-Block, Ausschlussbegriffe, Alters-Buckets, Wettbewerber-Treffer, Seen-State über zwei Läufe.

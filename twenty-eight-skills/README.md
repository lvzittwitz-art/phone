# Twenty-Eight Skills

Agent-Skills für die PR-Arbeit von Twenty-Eight, abgeleitet aus zwei Open-Source-Projekten und auf Deutsch, DACH-Medien und die Kunden der Agentur umgebaut.

| Ordner | Zweck | Herkunft |
|---|---|---|
| `geo-content-optimizer-v2/` | Texte messbar zitierfähig machen (ChatGPT, Perplexity, AI Overviews), Google-Doc-Audit im CI | Nectiv Digital, `aeo-content-structure-optimizer` (MIT) |
| `pr-skills/` | Nachrichtenwert-Check, Angle-Generator, Chefredakteur-Roast, Krisen-Holding, Ethik-Regeln | newsjack.sh, `elvisun/newsjack` (MIT) |
| `dach-newsjack-detector/` | Reaktive PR-Chancen aus deutschen Nachrichtenfeeds, erstes Profil Indeed | newsjack.sh, `newsjack-detector` und `newsjack-monitor-setup` (MIT), neu implementiert |

## Wie die Teile zusammenspielen

```
dach-newsjack-detector  ──▶  nachrichtenwert-check  ──▶  angle-generator
   (was passiert gerade)        (lohnt es sich)            (welche Geschichte)
                                                                │
                      bestehende Skills: umfrage-zu-pm, indeed-arbeitsmarkt-pm, journalisten-pitch
                                                                │
                                                       chefredakteur-roast
                                                                │
                                              medien-targeting (Blinq) ──▶ Versand nach Freigabe

geo-content-optimizer-v2: eigene Spur für Website- und Ratgebertexte des Kunden,
Seitenauswahl optional über Peec AI, Lieferung als Google Doc.

krisen-holding: eigenständig, mit juristischem Gate.
```

## Betriebsarten

Alle Skills laufen in Cowork und claude.ai im **Limited Mode** (Urteil, Entwürfe, Triage eingefügter Daten). Skripte, Monitoring-Läufe, Messungen und Dateiexporte brauchen **Full Mode** in Claude Code mit Shell. Jede SKILL.md sagt im ersten Abschnitt, was in welcher Betriebsart geht.

## Voraussetzungen

Python 3.10+ ohne Fremdpakete, `curl` für Seitenabrufe. Keine API-Schlüssel, keine Drittanbieter-Dienste. Optional: Google-Drive-Connector (Audit als Google Doc), Peec AI (Seitenauswahl), Blinq (Journalist:innen), Make-Webhook (Slack-Zustellung der Detector-Läufe).

## Tests

```bash
bash geo-content-optimizer-v2/tests/run_tests.sh
bash dach-newsjack-detector/tests/run_fixture_test.sh
```

## Was bewusst nicht übernommen wurde

- **Medialyst-Anbindung** aus newsjack (US-Journalistendatenbank, Credits, OAuth). Twenty-Eight hat Blinq für den DACH-Markt; Kundendaten bleiben lokal.
- **newsjack-Installer** (`curl | bash` mit Auto-Update vor jedem Lauf). Die Skills hier sind reine Dateien ohne Update-Mechanik.
- **pr-strategist** aus newsjack: auf Gründer:innen und „go direct“ zugeschnitten, verbietet Agenturmetriken. Passt nicht zur Kundenarbeit.
- **AI-Visibility-Panel-Skills** aus newsjack: durch Peec AI, Blinq GEO und `seo-geo-strategie` abgedeckt.
- **Nectivs Entity-Heuristik** (zählt Großschreibung): im Deutschen unbrauchbar, ersetzt durch Konkretheitsmessung.

## Lizenz

Die übernommenen Strukturen stehen unter MIT (Nectiv Digital; Elvis Sun und Carly Martinetti). Die Anpassungen gehören Twenty-Eight.

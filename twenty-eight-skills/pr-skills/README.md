# PR-Skills für Twenty-Eight

Vier Skills und eine Regelbasis für die Urteilsarbeit in der PR: Ist das eine Nachricht, welche Winkel gibt es, hält der Text einer Redaktion stand, was sagen wir in der ersten Stunde einer Krise. Alle Skills sind auf Deutsch, auf den DACH-Medienmarkt und auf die Arbeitsweise von Twenty-Eight (Daten-PR, Indeed, Netzschreier, Lebenskraftpur) zugeschnitten.

## Die Skills

**nachrichtenwert-check.** Bewertet ein Ereignis (Newsjack?) oder eine eigene Meldung (Pitch?) auf einer verankerten Skala von 1 bis 10 mit DACH-Ankern, gewichteten Dimensionen, Standing-Gate, Caps gegen PR-Inflation und Kill Switches für Tragödien. Liefert ein festes Verdict (REITEN / WARTEN / LASSEN / NIEMALS beziehungsweise PITCHEN / ÜBERARBEITEN / ZURÜCKHALTEN) mit Begründung, Belegen und Lücken. Der Skill ist absichtlich streng: Die meisten Dinge sind keine Nachricht.

**angle-generator.** Dreht einen Fakt, ein Update oder einen Datensatz durch feste Linsen (Perspektivwechsel, Abstraktionsleiter, Nachrichtenfaktoren, Datenwinkel, Inversion, Aktualitätsanker) und liefert drei bis sechs strukturell verschiedene Winkel mit Ressort, Medientyp, Decay-Tag, Belegbedarf und der Angabe, wen man nicht anschreibt. Verworfene Winkel werden mit Grund protokolliert. Eine eigene Sektion beschreibt die Drehreihenfolge für Umfragen und Hiring-Lab-Daten (Zeitvergleich, Regionalsplit, Branchensplit, Demografie, Ausreißer).

**chefredakteur-roast.** Kritisiert einen Pitch oder eine Pressemitteilung aus der Sicht einer Chefredakteur:in: 13 Kriterien mit je 0 bis 2 Punkten, ein einziges Mapping von Punkten auf Score und Verdict (publizierbar / workshopfähig / neu anfangen), deutsche Sperrliste für Floskeln, die drei schlimmsten Vergehen zeilengenau, Zeile-für-Zeile-Kritik, druckfertige Ersatz-Lede, zwei bis drei nächste Schritte. Hart, nie beleidigend.

**krisen-holding.** Erstellt Holding Statements in drei Varianten (kurz, mittel, vorsichtige juristische Fassung mit Änderungsliste), ein Q&A-Gerüst mit Antworthaltung und Bridge/Flag/Block-Technik, eine Tabelle der Sätze, die nicht fallen dürfen, und ein Gültigkeitsfenster mit Refresh-Auslösern. Vor jedem Entwurf steht ein juristisches Gate, das bei Datenschutzvorfällen, Behördenbezug, Personalthemen und Personenschäden stoppt, solange keine Kanzlei eingebunden ist. Berücksichtigt DSGVO-Fristen, Betriebsrat und dpa-Dynamik.

**ETHIK-UND-ANTI-SPAM.md.** Die Regelbasis, die über allen Skills steht: zehn Regeln für individuelle Pitches, harte Linien, und eine Twenty-Eight-spezifische Klärung, warum der Presseverteiler ein anderer Kanal mit eigenen Regeln ist und nicht unter die Fünfer-Regel fällt.

## Wie die Skills zusammenspielen

```
Ereignis oder eigener Fakt
        │
        ▼
nachrichtenwert-check ──── LASSEN / NIEMALS ──▶ Ende
        │ REITEN / PITCHEN
        ▼
angle-generator ──▶ 3–6 Winkel mit Ressort und Decay
        │
        ▼
umfrage-zu-pm / indeed-arbeitsmarkt-pm / journalisten-pitch  (bestehende Skills: Text)
        │
        ▼
chefredakteur-roast ──▶ workshopfähig? zurück zum Text
        │ publizierbar
        ▼
medien-targeting (bestehender Skill: Namen, Redaktionen, Blinq)
        │
        ▼
Freigabe durch Mensch, dann Versand
```

`krisen-holding` steht außerhalb dieser Kette und übersteuert sie: Liegt ein Vorfall vor, zuerst dorthin.

## Herkunft und Änderungen

Portiert und adaptiert aus **elvisun/newsjack** (MIT-Lizenz, Elvis Sun und Carly Martinetti): newsworthiness-check, angle-generator, meanest-editor, crisis-holding und WHY-NOT-SPAM.md. Die Architektur der Rubriken (verankerte Skalen, Caps, Kill Switches, Verweigerungsgründe, Decay-Tags, juristisches Gate) stammt von dort.

Geändert gegenüber dem Original:

- Vollständig auf Deutsch, Anrede "du" wie in den bestehenden Twenty-Eight-Skills
- DACH-Anker statt US-Anker (BVerfG, Bundestagswahl, Tarifabschluss, BA-Zahlen statt Supreme Court, Series A, SEC)
- DACH-Medienlogik ergänzt: dpa-Multiplikation, Fachpresse vs. Leitmedien, Sperrfrist, Regionalbezug, Betriebsrat, DSGVO-Fristen, Social-Screenshot-Dynamik
- Twenty-Eight-Kontext: Daten-PR-Drehreihenfolge für Umfragen und Hiring-Lab-Daten, Handoffs an bestehende Skills (journalisten-pitch, medien-targeting, umfrage-zu-pm, anti-ki-schreibcheck, Twenty-Eight Charts)
- Beim Roast: die im Original inkonsistenten Score-Bänder durch ein einziges Mapping ersetzt, deutsche Sperrliste, Sonderregel für Gastbeiträge
- Beim Nachrichtenwert-Check: Stichprobenkriterium für Umfragen in der Anti-Inflation-Liste, Hinweis auf Regionalsplit als Score-Hebel
- In der Ethik-Datei: Klärung Presseverteiler vs. Pitch, damit die Fünfer-Regel nicht den regulären PM-Versand blockiert
- Keine Abhängigkeit von Medialyst, X-API oder dem newsjack-CLI; alle Skills laufen ohne Schlüssel in Claude Code, Cowork und claude.ai

Nicht portiert: find-journalists (Blinq deckt das ab), pr-strategist (Gründer:innen-Framing, passt nicht zur Agenturarbeit), die AI-Visibility-Skills (Peec AI und geo-content-optimizer decken das ab), newsjack-detector (eigener Ordner `dach-newsjack-detector`).

## Installation

Jeder Unterordner ist ein eigenständiger Skill mit `SKILL.md` und Frontmatter (`name`, `description`). Zum Einbinden den Ordner in das anthropic-skills-Plugin beziehungsweise in den Cowork-Skill-Sync kopieren, so wie die bestehenden Skills (journalisten-pitch, umfrage-zu-pm) dort liegen. `ETHIK-UND-ANTI-SPAM.md` liegt eine Ebene über den Skills und wird aus ihnen relativ referenziert; beim Kopieren einzelner Skills die Datei mitnehmen oder den Pfad anpassen.

Keine Abhängigkeiten, keine Schlüssel, keine Skripte. Alles ist Markdown.

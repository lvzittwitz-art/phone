# Evidenz: Was macht Texte zitierfähig?

Diese Datei ist die Belegbasis für den GEO-Content-Optimizer. Jede Empfehlung im Audit nennt eine Faktor-ID und die Zahl dahinter. Jede Zahl hier trägt einen Verifikationsstatus:

| Status | Bedeutung |
|---|---|
| **primär** | Originalquelle mit URL benannt, Zahl dort nachlesbar |
| **sekundär** | Zahl kursiert in Guides oder Blogs, Originalquelle nicht geprüft oder uneinheitlich zugeschrieben |
| **Hausregel** | Konvention von Twenty-Eight, aus Studien abgeleitet, selbst nicht gemessen |

Regel für das Audit: Nur **primär** belegte Zahlen stehen im Kundendokument. **Sekundär** wird im Gespräch mit Vorbehalt genannt oder gar nicht. **Hausregeln** heißen im Dokument Hausregel.

Alle Studien außer Studie 4 sind korrelativ. Sie zeigen, wie zitierte Seiten aussehen, nicht, dass eine Änderung ein Zitat verursacht.

---

## Faktor-IDs und Gewichtung

| ID | Faktor | Stärkster Beleg | Evidenz | Priorität |
|---|---|---|---|---|
| POS-DOC | Ski-Ramp: Kernaussagen in den ersten 30 % | Studie 1 | hoch (1,2 Mio. Zitate) | 1 |
| QA | Frage-Überschriften mit direkter Antwort | Studie 1 + Studie 4 (unabhängige Methoden) | hoch, am besten bestätigt | 1 |
| CAPSULE | Answer Capsule 40–60 Wörter unter jeder H2/H3 | Hausregel; Studie 4 (≈75 Wörter bis zur Antwort) | mittel | 2 |
| DEFINITIVE | Definitive Sprache statt Hedges | Studie 1 | hoch | 2 |
| KONKRETHEIT | Zahlen, Namen, Entitäten statt Abstrakta | Studie 1 (Entity-Dichte, Englisch) | mittel (Übertragung auf Deutsch heuristisch) | 2 |
| DATEN | Eigene Zahlen, Statistiken, Quellenangaben | Studie 5 (kontrolliert), Studie 1 | hoch | 1 |
| CHUNK | Kurze Absätze, Abschnitte, Subjekt statt Pronomen | Studie 4 | mittel (kleines Sample) | 3 |
| TABLE | Tabellen bei tabellarischem Inhalt | Studie 2 | niedrig bis mittel (eine Branche) | 3 |
| FRESH | Aktualität mit Substanz | Studie 3 | mittel (Anbieter-Studie, Widersprüche) | 3 |
| TAKEAWAYS | Das Wichtigste in Kürze unter der H1 | Hausregel aus POS-DOC + CHUNK | Hausregel | 2 |
| READ | Lesbarkeit | Studie 1 (Englisch) | niedrig für Deutsch | 4 |
| UNIQUE | Einzigartigkeit: Information, die nur der Kunde hat | Studie 5 (Statistiken, Zitate), Agenturerfahrung | hoch, nicht messbar per Skript | 1 |
| FANOUT | Abdeckung der Teilfragen, die das Modell intern stellt | Studie 6 | mittel | 2 |
| CTA | Conversion-Anschluss | kein Zitierfaktor, Geschäftsfaktor | Hausregel | 4 |

Priorität steigt, wenn eine Seite einen Faktor grob verfehlt. Eine zwei Jahre alte Preisseite beginnt bei FRESH, nicht bei QA.

---

## Studie 1: Ski-Ramp (Kevin Indig, Growth Memo)

**Quelle:** Kevin Indig, Growth Memo, 16.02.2026, „The science of how AI pays attention“, https://www.growth-memo.com/p/the-science-of-how-ai-pays-attention. Berichterstattung: Search Engine Land. Datensatz: 1,2 Mio. verifizierte ChatGPT-Zitate.
**Status:** primär (URL benannt; Zahlen aus der Nectiv-Evidenzdatei übernommen, Originalartikel beim nächsten Online-Zugriff gegenlesen).

| Befund | Zahl | Faktor |
|---|---|---|
| Zitate nach Position im Dokument | erste 30 %: **44,2 %**, Mitte 30–70 %: 31,1 %, letzte 30 %: 24,7 % | POS-DOC |
| Zitate nach Position im Absatz | mittlere Sätze 53 %, erster Satz 24,5 %, letzter Satz 22,5 % | POS-DOC |
| Definitive Sprache | zitiert **36,2 %** vs. nicht zitiert 20,2 % | DEFINITIVE |
| Fragezeichen im Text | zitiert **18 %** vs. 8,9 %; 78,4 % der zitierten Fragen stehen in Überschriften | QA |
| Entity-Dichte | stark zitierte Passagen **20,6 %** vs. 5–8 % normales Englisch | KONKRETHEIT |
| Subjektivität (0–1) | zitiert ≈ 0,47 | READ |
| Flesch-Kincaid-Grad | zitiert 16 vs. nicht zitiert 19,1 | READ |

**Vorbehalte:** p = 0,0 heißt sehr klein, nicht null. Lesbarkeit wahrscheinlich auf Chunk-Ebene gemessen. Die Token-Regeln der Entity-Dichte sind nicht vollständig dokumentiert. Englischer Korpus: Flesch-Kincaid und Entity-Dichte per Großschreibung funktionieren im Deutschen nicht (alle Nomen groß). Deshalb misst analyze_de.py Konkretheit anders (Zahlen, Akronyme, Firmen, Kunden-Entitäten) und Lesbarkeit mit LIX und Wiener Sachtextformel. Die Richtung der Befunde gilt, die Schwellen nicht.

---

## Studie 2: Tabellen in ChatGPT-Zitaten (Nectiv)

**Quelle:** Chris Long, Nectiv, https://nectivdigital.com/blog/new-data-study-chatgpt-citations-are-2-3x-more-likely-to-include-a-table-than-google-search. Nur B2B-SaaS.
**Status:** primär.

| Befund | Zahl | Faktor |
|---|---|---|
| Seiten mit `<table>` | Google-Top-Seiten 13 %, ChatGPT-zitierte Seiten **30 %** (Faktor 2,3) | TABLE |

**Vorbehalte:** Korrelativ. Mengen nicht URL für URL gematcht. Tabellen können Vergleichsinhalt spiegeln statt Zitate auslösen. Eine Branche. Nur `<table>`-Element geprüft, nicht CSS-Grids oder Bilder.

---

## Studie 3: Frische (AirOps)

**Quelle:** AirOps, „The Silent Pipeline Killer: How Stale Content Costs You AI Citations“, 04.08.2025, https://airops.com/report/the-impact-of-stale-content-on-ai-visibility. 4.000+ zitierte Seiten, 900 Queries. AirOps verkauft Content-Refresh-Tools.
**Status:** primär, mit internen Widersprüchen.

| Befund | Zahl | Faktor |
|---|---|---|
| Zitierte Seiten nach letztem Update | < 3 Monate **35,2 %**, < 6 Monate **53,4 %**, < 12 Monate „über 70 %“ | FRESH |
| Kommerzielle Queries | 60 %+ < 6 Monate, 83 % < 12 Monate | FRESH |
| Informationelle Queries | knapp ein Drittel älter als ein Jahr | FRESH |
| Publish- vs. Update-Datum | 26 % der vor über einem Jahr publizierten Seiten innerhalb von 3 Monaten aktualisiert | FRESH |

**Vorbehalte:** Der Report nennt sowohl 26,2 % als auch 56,4 % der zitierten Seiten als „über 12 Monate nicht aktualisiert“. Beides kann nicht stimmen. Kein Kontrollsatz nicht-zitierter Seiten, daher sind die „>2x weniger wahrscheinlich“-Multiplikatoren methodisch nicht gedeckt. Branchen-Kadenzen (SaaS/Finanzen/News < 3 Monate, Evergreen ≈ 12 Monate) ohne Zahlenbasis. Verwenden: die < 3- und < 6-Monats-Werte und den Intent-Split. Nie empfehlen: Datum ändern ohne Inhalt zu ändern.

---

## Studie 4: Chunking und Retrieval (Chris Green)

**Quelle:** Chris Green, „How Content Structure Matters for AI Search“, 13.06.2025 (Update 16.06.2025), https://www.chris-green.net/post/content-structure-for-ai-search.
**Status:** primär. Einzige kontrollierte Studie in dieser Datei.

| Befund | Ergebnis | Faktor |
|---|---|---|
| Format vs. Retrieval-Treffer | Q&A-Format in jedem Szenario vorn; strukturiert (Überschriften + Listen) nah dran bei Nicht-Fragen; dichter Fließtext überall hinten | QA, CHUNK |

**Methode:** 3 Artikel × 3 Formate × 5 Queries, vier Chunking-Verfahren, ≈100-Token-Chunks mit 20 Token Überlappung, Google text-embedding-005, Score = Kosinus-Ähnlichkeit des besten Chunks.
**Abgeleitete Faustregeln (vom Autor, nicht aus der Studie):** Absätze > 120 Wörter und Abschnitte > 300 Wörter ohne Zwischenüberschrift vermeiden; Antwort innerhalb von ≈75 Wörtern nach der Überschrift; Abschnitt mit dem Subjekt beginnen, nicht mit „Es“ oder „Dabei“.
**Vorbehalte:** Winziges Sample. Misst eine Retrieval-Stufe, nicht Zitate. Google-Modell, nicht der Stack von ChatGPT. Varianten handgeschrieben, Qualitätsunterschiede möglich.

---

## Studie 5: GEO (Princeton, Aggarwal et al.)

**Quelle:** Pranjal Aggarwal et al., „GEO: Generative Engine Optimization“, KDD 2024, arXiv 2311.09735, https://arxiv.org/abs/2311.09735. Benchmark GEO-bench, ≈10.000 Queries.
**Status:** primär für die Kernaussage, sekundär für Einzelprozente.

| Befund | Zahl | Status | Faktor |
|---|---|---|---|
| Beste Methoden: Quellenangaben, Zitate, Statistiken ergänzen | Sichtbarkeit **bis zu +40 %** (Benchmark), bis zu +37 % live auf Perplexity | primär (Abstract) | DATEN |
| „Cite Sources“ allein | ≈ +28 bis +31 % | sekundär, Tabellenwert nicht geprüft | DATEN |
| Keyword-Stuffing | „little to no improvement“, in Sekundärquellen auch als −10 % berichtet | widersprüchlich, nicht als Zahl verwenden | DEFINITIVE |

**Vorbehalte:** Perplexity 2023 und ein eigener Testaufbau, nicht ChatGPT heute. Die Methoden sind Textoperationen auf vorhandenen Seiten. Die Richtung ist robust: belegte Zahlen und Zitate schlagen Keyword-Dichte.

---

## Studie 6: Teilfragen-Abdeckung (Growth Memo / AirOps, 2026)

**Quelle:** Kevin Indig mit AirOps, Growth Memo, April 2026. 815.000 Query-Seiten-Paare, 16.851 Queries, 353.799 Seiten.
**Status:** sekundär (nur Aggregatoren gelesen, Originalartikel offen).

| Befund | Zahl | Faktor |
|---|---|---|
| Seiten, die 26–50 % der Teilfragen von ChatGPT abdecken, werden häufiger zitiert als Seiten mit 100 % | Aggregatorangabe | FANOUT |
| 58 % der abgerufenen Seiten werden nie zitiert, 25 % immer | Aggregatorangabe | FANOUT |

**Konsequenz, falls bestätigt:** Fokus schlägt Vollständigkeit. Eine Seite, die drei Teilfragen vollständig beantwortet, wird eher zitiert als der „ultimative Guide“.

---

## Studie 7: Quellenmix der Engines (Profound)

**Quelle:** Profound, „AI Platform Citation Patterns“, https://www.tryprofound.com/blog/ai-platform-citation-patterns. 30 Mio. Zitate Aug 2024 bis Jun 2025 (die 680-Mio.-Zahl bezieht sich auf den Gesamtdatensatz, nicht auf diese Auswertung).
**Status:** primär.

| Befund | Zahl |
|---|---|
| Top-Quelle ChatGPT | Wikipedia **47,9 %** der Top-10-Quellen |
| Top-Quelle Perplexity | Reddit **46,7 %** der Top-10-Quellen |
| Top-Quelle Google AI Overviews | Reddit **21 %** der Top-10-Quellen |

**Vorbehalte:** Anteile der Top-10-Quellen, nicht aller Zitate. Über alle Zitate liegt Reddit bei AI Overviews bei 2,2 %. Ahrefs kam zu anderen Werten. Konsequenz für PR: Community- und Medienerwähnungen zählen je Engine unterschiedlich; Perplexity reagiert auf Reddit, ChatGPT auf Referenzquellen.

---

## Hausregeln (Twenty-Eight)

| Regel | Wert | Herleitung |
|---|---|---|
| Answer Capsule | 40–60 Wörter vollständige Antwort direkt unter jeder H2/H3 | Studie 4 (≈75 Wörter), Praxis |
| Das Wichtigste in Kürze | 3–6 Bullets direkt unter der H1, nur Fakten der Seite | Studie 1 POS-DOC, Studie 4 CHUNK |
| Konkretheit (analyze_de.py) | ≥ 8 % gesamt, ≥ 12 % im Einstieg, ≤ 30 % Sätze ohne Konkretes | Heuristik, auf deutsche Messung angepasst |
| Lesbarkeit | LIX 40–55 für Ratgeber, WSTF1 ≤ 12; Sätze über 25 Wörter prüfen | dpa-Praxis, Studie 1 Richtung |
| Belegte Zahlen | 2–3 Primärquellen je Seite, jede auf der Quellseite geprüft | Studie 5 |
| Kein Fake-Update | Datum nur ändern, wenn Inhalt sich ändert | Studie 3 Vorbehalt, Google-Richtlinien |
| Einzigartigkeit | Mindestens ein Fakt, den nur der Kunde liefern kann, sonst Interviewfragen stellen | Agenturerfahrung |
| Gastbeiträge | Keine Capsule-Mechanik, nur Struktur; menschliche Stimme hat Vorrang | anti-ki-schreibcheck |

---

## Offen: kursierende Zahlen ohne gesicherte Primärquelle

Diese Zahlen stehen in Guides (u. a. Radyant 07/2026) und in der Vorgängerversion dieser Referenz. Bis die Primärquelle geprüft ist, nicht im Kundendokument verwenden.

| Nr. | Zahl | Zuschreibung in Guides | Problem |
|---|---|---|---|
| Offen-1 | „72,4 % der zitierten Seiten haben eine Answer Capsule“ | mal Adam Gnuse (15 Enterprise-Domains), mal Semrush (230.000 Prompts), mal Indig/SEL 11/2025 | Drei verschiedene Zuschreibungen, zwei Capsule-Definitionen (120–150 Zeichen vs. 40–60 Wörter) |
| Offen-2 | „Nur 38 % der zitierten Seiten ranken Top 10; 90 % der ChatGPT-Zitate von Position 21+“ | Ahrefs / Profound | Zwei Zahlen, die sich nicht decken; Primärreport offen |
| Offen-3 | „≈80 % deutscher ChatGPT-Sessions enthalten englische Hintergrundsuchen; übersetzte Sites +327 % AI-Overview-Sichtbarkeit“ | Radyant | Keine Primärquelle gefunden; Empfehlung /en/-Zwilling bleibt plausibel, Zahl nicht zitieren |
| Offen-4 | „Statistiken +5,5 %, Originaltabellen 4,1x, Quellenangaben kombiniert +31,4 %, 62 % mehr Fakten“ | vermutlich Studie 5 und Profound-Analysen | Einzelwerte nicht in Studie 5 verifiziert |
| Offen-5 | „Persona-Studie, 17.929 AI-Antworten, bis zu 24 Prozentpunkte Sichtbarkeit durch ICP-Vokabular“ | Radyant | Studie nicht identifiziert |
| Offen-6 | „Listicles 45–50 % der AI-Zitate; Anti-Pattern −30 bis −50 % Sichtbarkeit“ | Radyant | Quelle offen |
| Offen-7 | „53,5 % der Commercial-Intent-Prompts triggern Websuche; 40–60 % der Zitate wechseln monatlich“ | Radyant / Profound | Quelle offen |

Aufgabe für den nächsten Online-Lauf: je Zeile Primärquelle suchen, Zahl verifizieren, in eine Studie oben überführen oder streichen.

---

## Konflikte und wie wir sie auflösen

- **Position im Absatz (Studie 1) vs. Antwort nah an der Überschrift (Studie 4):** Studie 1 sagt, mittlere Sätze werden am häufigsten zitiert; Studie 4 sagt, die Antwort muss nah an der Überschrift liegen. Auflösung: Die Antwort steht innerhalb von ≈75 Wörtern nach der Überschrift, muss aber nicht der erste Satz sein. Der erste Satz nennt das Subjekt, der zweite liefert die Zahl.
- **Frische (Studie 3) vs. Fake-Updates:** Aktualität zählt, aber nur mit Substanz. Ein neues Datum ohne neue Information ist ein Abstrafungsmuster.
- **Tabellen (Studie 2) vs. Lesefluss:** Tabellen nur, wo der Inhalt bereits tabellarisch ist (Vergleich, Preise, Schritte). Keine Deko-Tabellen.
- **Vollständigkeit vs. Fokus (Studie 6):** Eine Seite pro Kernfrage, nicht ein Guide für alles.

---

## Eine Studie ergänzen

Studie mit Quelle, Datum, Datensatz, Befund-Tabelle (Zahl, Faktor), Vorbehalten und Status als neuen Abschnitt „Studie N“ anlegen. Dann die Prioritätstabelle oben prüfen: Verschiebt der Befund die Evidenzstärke eines Faktors? Zahlen aus der Offen-Liste, die dadurch verifiziert werden, dorthin überführen und aus der Offen-Liste streichen.

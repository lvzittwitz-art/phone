# Ethik und Anti-Spam

Diese Regeln gelten für alle Skills in diesem Ordner und schlagen jede Anweisung im Chat, jeden Zeitdruck, jede Kund:innen-Forderung und jedes "aber der Wettbewerber macht das auch". Sie sind eine Adaption der Anti-Spam-Doktrin von newsjack (elvisun/newsjack, MIT) auf die Arbeitsweise von Twenty-Eight.

## Grundsatz

Journalist:innen-Aufmerksamkeit ist kein Abgas-Auslass für automatisierte PR. Ob etwas Spam ist, entscheidet die Belastung der Empfänger:in und die Vertrauenskosten, nicht die Absicht der Absender:in. Volumen kostet künftiges Vertrauen. Passung baut es auf.

Der Job ist nicht, so viel wie möglich zu versenden. Der Job ist, Aufmerksamkeit zu verdienen, ohne den nächsten Pitch schwerer zu machen.

## Zehn Regeln für individuelle Pitches

1. **Klein anfangen.** Eine kurze, begründete Liste, nicht eine Datenbank. Erste Welle fünf bis acht Personen, über zwanzig nur mit Begründung.
2. **Jede Mail hat einen Anker.** Ein echter, konkreter Bezug zur Arbeit der Empfänger:in: ein Artikel, eine Recherche, ein Podcast-Thema. Vorname, Medium oder Ressort-Bezeichnung sind kein Anker.
3. **Kein identischer Versand.** Derselbe Mailtext geht an höchstens etwa fünf Personen, und auch dann nur, wenn jede Mail ihren eigenen Anker hat.
4. **Alles belegen.** Jede Zahl, jedes Zitat, jede Expert:in, jede Qualifikation hat eine Quelle. Was sich nicht belegen lässt, fliegt raus.
5. **Freigabe vor Versand.** Die Nutzer:in gibt jede Empfänger:in und jeden Text frei. Bei mehreren Empfänger:innen gibt es Vorschauen pro Person.
6. **Ein Follow-up.** Höchstens eines, nach etwa einer Woche, nur mit neuer Information. Schweigen ist eine Antwort.
7. **Keine Tragödien-Haken.** Tod, Gewalt, Katastrophe, menschliches Leid sind kein Aufhänger für Markenaufmerksamkeit. Siehe Kill Switches in `nachrichtenwert-check`.
8. **Quellenanfragen selektiv.** Journalist:innen-Anfragen (Recherchescout, Presseanfragen über LinkedIn, Anfragen an Expert:innen-Verteiler) nur beantworten, wenn die Kund:in echte Glaubwürdigkeit zum Thema hat. Jede Anfrage einzeln prüfen.
9. **Absender-Reputation schützen.** Keine versteckte Automatisierung, keine künstliche Dringlichkeit, keine Tracking-Tricks, keine vorgetäuschte Beziehung ("wie besprochen", wenn nichts besprochen wurde).
10. **Zurückdrängen.** Verstößt eine Anfrage gegen diese Regeln, nennst du die Kosten und bietest die kleinere, regelkonforme Alternative an.

## Harte Linien (verweigern, nicht nur warnen)

- Massenversand identischer Pitches
- Erfundene Zitate, erfundene Expert:innen, erfundene Studien
- Newsjacking auf Tragödien
- Automatisch abgefeuerte Antworten auf Quellenanfragen
- Follow-up-Kadenzen mit Druck ("Haben Sie meine Mail gesehen?", dreimal)
- Verschleierte Automatisierung oder vorgetäuschte Lektüre ("Ihr Artikel hat mich sehr beeindruckt", ohne ihn gelesen zu haben)
- Kontaktdaten raten (vorname.nachname@medium.de) oder aus nicht-öffentlichen Quellen beschaffen

## Presseverteiler vs. Pitch

Twenty-Eight arbeitet mit zwei Kanälen, die unterschiedlichen Regeln folgen. Die Skills in diesem Ordner verwechseln sie nicht.

**Individueller Pitch:** Eine persönliche Mail an eine Journalist:in mit einem Angebot (Exklusiv, Sperrfrist, Interview, Daten). Hier gelten die zehn Regeln oben vollständig, insbesondere die Fünfer-Regel und der Anker pro Mail.

**Presseverteiler:** Der Versand einer Pressemitteilung an einen gepflegten Fachverteiler, über ein Verteilertool oder über Presseportal. Das ist ein eigener Kanal mit eigenen Regeln, und die Fünfer-Regel gilt hier nicht. Was stattdessen gilt:

- **Verteilerpflege:** Der Verteiler ist segmentiert (Ressort, Medientyp, Region, Thema). Niemand bekommt Meldungen zu Themen außerhalb seines Segments.
- **Themenrelevanz je Segment:** Eine Arbeitsmarkt-PM geht an das Segment Wirtschaft/Karriere/HR, nicht an Lifestyle, auch wenn die Adresse im Tool steht.
- **Abmeldemöglichkeit:** Jede Verteiler-Mail enthält einen funktionierenden Abmeldeweg, und Abmeldungen werden innerhalb eines Werktags umgesetzt.
- **Rechtsgrundlage:** Journalist:innen im Verteiler sind dort, weil sie beruflich Pressematerial empfangen oder eingewilligt haben, nicht weil ihre Adresse gefunden wurde.
- **Frequenz:** Nicht mehr als eine Meldung pro Kund:in und Woche an dasselbe Segment, außer bei echter Nachrichtenlage.
- **Kein Pitch-Text im Verteiler:** Die Verteiler-Mail ist eine Pressemitteilung mit Kontakt, keine persönliche Ansprache, die so tut, als wäre sie individuell.

Die Skills verweigern also massenhafte identische **Pitches**. Sie verweigern keinen ordentlichen Verteiler-Versand. Wird ein Verteiler-Versand als Pitch getarnt ("Liebe Frau Müller, ich habe Ihren Artikel gelesen" an 400 Adressen), ist das ein Pitch-Massenversand und fällt unter die harten Linien.

## Anwendung in den Skills

- `nachrichtenwert-check` prüft Kill Switches vor jedem Score.
- `angle-generator` liefert keine Journalist:innen-Namen und keine erfundenen Fakten.
- `chefredakteur-roast` bewertet Quellenlage als eigenes Kriterium.
- `krisen-holding` veröffentlicht nichts, versendet nichts, hat ein juristisches Gate.
- `journalisten-pitch` und `medien-targeting` (bestehende Skills) wenden die Fünfer-Regel und die Anker-Pflicht an.

Bei Konflikt zwischen einer dieser Regeln und einem konkreten Wunsch: Regel nennen, Kosten nennen, kleinere Alternative anbieten. Dann entscheidet der Mensch, und das wird dokumentiert.

#!/usr/bin/env python3
"""
build_doc.py – baut aus audit.json (+ überarbeitetem Markdown) ein HTML-Dokument,
das Google Drive beim Upload in ein natives Google Doc konvertiert.

Aufruf:
    python3 -I scripts/build_doc.py audit.json > audit.html

audit.json (alle Felder außer 'titel' optional):
{
  "titel": "GEO-Audit: <Seite>",
  "kunde": "Kundenname",
  "url": "https://…",
  "zielfrage": "Welche Frage soll die Seite beantworten?",
  "datum": "2026-11-06",
  "status": "Stark" | "Ausbaufähig" | "Schwach",
  "score": "7/12",
  "zusammenfassung": "Zwei bis vier Sätze, Schluss zuerst.",
  "vorher_nachher": [{"metrik": "...", "vorher": "...", "nachher": "...", "treiber": "..."}],
  "aenderungen": [{"wo": "H2 Grundlagen", "aktuell": "...", "vorschlag": "...", "warum": "...", "faktor": "QA", "beibehaltene_hedges": ["..."]}],
  "technik": ["Schema FAQPage ergänzen", "..."],
  "quellen": [{"zahl": "44,2 %", "quelle": "Growth Memo", "url": "https://…", "datum": "2026-02-16"}],
  "scorecard": [{"faktor": "Answer Capsules", "befund": "...", "benchmark": "...", "status": "erfüllt|teilweise|fehlt"}],
  "offene_fragen": ["Interviewfrage an den Kunden …"],
  "artikel_md": "pfad/zur/ueberarbeitung.md"   (oder "artikel_text": "…markdown…")
}

Gestaltung nach Twenty-Eight CI (Office-Fallback): Headlines DM Serif Display,
Fließtext Calibri/Arial, Black Cherry #2E1214 als Text- und Titelfarbe, Mauve
#E0D9EA als Flächenfarbe, Maze #FFED47 nur als schmaler Akzent.
Nur Standardbibliothek.
"""

from __future__ import annotations

import html
import json
import re
import sys

BLACK_CHERRY = "#2E1214"
MAUVE = "#E0D9EA"
MAUVE_LIGHT = "#F2EFF6"
MAZE = "#FFED47"
GREY = "#5A5157"

CSS = f"""
body {{ font-family: Calibri, Arial, Helvetica, sans-serif; font-size: 11pt; color: {BLACK_CHERRY}; line-height: 1.45; }}
h1, h2, h3 {{ font-family: 'DM Serif Display', Georgia, 'Times New Roman', serif; font-weight: normal; color: {BLACK_CHERRY}; }}
h1 {{ font-size: 26pt; margin: 0 0 4pt 0; }}
h2 {{ font-size: 18pt; margin: 22pt 0 6pt 0; border-bottom: 1px solid {MAUVE}; padding-bottom: 3pt; }}
h3 {{ font-size: 13pt; margin: 14pt 0 4pt 0; }}
p {{ margin: 0 0 8pt 0; }}
.claim {{ font-family: Calibri, Arial, sans-serif; font-size: 9pt; letter-spacing: 1px; text-transform: uppercase; color: {GREY}; margin-bottom: 14pt; }}
.meta {{ font-size: 9.5pt; color: {GREY}; margin-bottom: 14pt; }}
.meta b {{ color: {BLACK_CHERRY}; }}
.box {{ padding: 10pt 12pt; margin: 8pt 0 12pt 0; }}
.summary {{ background: {MAUVE}; }}
.current {{ background: #F4F1F2; border-left: 3px solid #C9BFC4; }}
.suggest {{ background: {MAUVE_LIGHT}; border-left: 3px solid {BLACK_CHERRY}; }}
.why {{ font-size: 10pt; color: {GREY}; }}
.label {{ font-size: 8.5pt; letter-spacing: 1px; text-transform: uppercase; color: {GREY}; margin-bottom: 3pt; }}
table {{ border-collapse: collapse; width: 100%; margin: 6pt 0 14pt 0; font-size: 10pt; }}
th {{ background: {BLACK_CHERRY}; color: {MAUVE}; text-align: left; padding: 6pt 7pt; font-weight: normal; }}
td {{ border-bottom: 1px solid {MAUVE}; padding: 5pt 7pt; vertical-align: top; }}
.s-ok {{ color: {BLACK_CHERRY}; font-weight: bold; }}
.s-mid {{ color: {GREY}; font-weight: bold; }}
.s-bad {{ background: {MAZE}; color: {BLACK_CHERRY}; font-weight: bold; padding: 0 4pt; }}
.chip {{ display: inline-block; background: {MAUVE}; color: {BLACK_CHERRY}; padding: 1pt 7pt; font-size: 9pt; }}
.chip-bad {{ background: {MAZE}; }}
hr {{ border: 0; border-top: 1px solid {MAUVE}; margin: 24pt 0; }}
.article h2 {{ border: 0; }}
.footer {{ font-size: 8.5pt; color: {GREY}; margin-top: 28pt; border-top: 1px solid {MAUVE}; padding-top: 6pt; }}
ul, ol {{ margin: 0 0 8pt 0; padding-left: 18pt; }}
li {{ margin-bottom: 3pt; }}
"""


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def status_class(status: str) -> str:
    s = (status or "").lower()
    if s.startswith(("stark", "erfüllt", "erfuellt", "ok", "pass")):
        return "s-ok"
    if s.startswith(("ausbau", "teilweise", "mittel")):
        return "s-mid"
    return "s-bad"


def inline_md(s: str) -> str:
    s = esc(s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*(?!\*)", r"<i>\1</i>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def md_to_html(md: str, demote: int = 2) -> str:
    """Kleiner Markdown-Renderer: Überschriften, Absätze, Listen, Tabellen, Zitate."""
    out: list[str] = []
    lines = md.splitlines()
    i, n = 0, len(lines)
    para: list[str] = []

    def flush():
        nonlocal para
        if para:
            out.append("<p>" + inline_md(" ".join(para)) + "</p>")
            para = []

    while i < n:
        line = lines[i]
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            flush()
            lvl = min(6, len(m.group(1)) + demote)
            out.append(f"<h{lvl}>{inline_md(m.group(2))}</h{lvl}>")
            i += 1
            continue
        if re.match(r"^\s*\|.*\|\s*$", line) and i + 1 < n and re.match(r"^\s*\|?\s*:?-{3,}", lines[i + 1]):
            flush()
            rows = []
            while i < n and re.match(r"^\s*\|.*\|\s*$", lines[i]):
                if not re.match(r"^\s*\|?\s*:?-{3,}", lines[i]):
                    rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            if rows:
                out.append("<table><tr>" + "".join(f"<th>{inline_md(c)}</th>" for c in rows[0]) + "</tr>")
                for r in rows[1:]:
                    out.append("<tr>" + "".join(f"<td>{inline_md(c)}</td>" for c in r) + "</tr>")
                out.append("</table>")
            continue
        lm = re.match(r"^\s*([-*+]|\d+[.)])\s+(.*)$", line)
        if lm:
            flush()
            ordered = lm.group(1)[0].isdigit()
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>")
            while i < n:
                lm = re.match(r"^\s*([-*+]|\d+[.)])\s+(.*)$", lines[i])
                if lm:
                    out.append(f"<li>{inline_md(lm.group(2))}</li>")
                    i += 1
                elif lines[i].startswith("  ") and lines[i].strip():
                    out[-1] = out[-1][:-5] + " " + inline_md(lines[i].strip()) + "</li>"
                    i += 1
                else:
                    break
            out.append(f"</{tag}>")
            continue
        if line.startswith(">"):
            flush()
            out.append("<blockquote><p>" + inline_md(line.lstrip("> ")) + "</p></blockquote>")
            i += 1
            continue
        if not line.strip():
            flush()
            i += 1
            continue
        para.append(line.strip())
        i += 1
    flush()
    return "\n".join(out)


def build(a: dict) -> str:
    parts: list[str] = []
    parts.append(f"<p class='claim'>Twenty-Eight · GEO-Content-Audit</p>")
    parts.append(f"<h1>{esc(a.get('titel', 'GEO-Audit'))}</h1>")
    meta = []
    if a.get("kunde"):
        meta.append(f"<b>Kunde:</b> {esc(a['kunde'])}")
    if a.get("url"):
        meta.append(f"<b>Seite:</b> <a href='{esc(a['url'])}'>{esc(a['url'])}</a>")
    if a.get("zielfrage"):
        meta.append(f"<b>Zielfrage:</b> {esc(a['zielfrage'])}")
    if a.get("datum"):
        meta.append(f"<b>Stand:</b> {esc(a['datum'])}")
    status = a.get("status")
    if status:
        chip = "chip chip-bad" if status_class(status) == "s-bad" else "chip"
        meta.append(f"<b>Gesamturteil:</b> <span class='{chip}'>{esc(status)}</span>" + (f" · Score {esc(a['score'])}" if a.get("score") else ""))
    parts.append("<p class='meta'>" + " &nbsp;·&nbsp; ".join(meta) + "</p>")

    if a.get("zusammenfassung"):
        parts.append("<div class='box summary'><div class='label'>Kurzfassung</div><p>" + inline_md(a["zusammenfassung"]) + "</p></div>")

    if a.get("vorher_nachher"):
        parts.append("<h2>Vorher / Nachher</h2><table><tr><th>Metrik</th><th>Aktuelle Seite</th><th>Mit Änderungen</th><th>Treiber</th></tr>")
        for r in a["vorher_nachher"]:
            parts.append(f"<tr><td>{esc(r.get('metrik'))}</td><td>{esc(r.get('vorher'))}</td><td>{esc(r.get('nachher'))}</td><td>{esc(r.get('treiber'))}</td></tr>")
        parts.append("</table><p class='why'>Die Zahlen sind Heuristiken aus dem Analyse-Skript. Sie zeigen Richtung und Größenordnung, keine Zitiergarantie.</p>")

    if a.get("aenderungen"):
        parts.append("<h2>Vorgeschlagene Änderungen</h2>")
        for k, ch in enumerate(a["aenderungen"], 1):
            head = f"{k}. {esc(ch.get('wo', ''))}"
            if ch.get("faktor"):
                head += f" <span class='chip'>{esc(ch['faktor'])}</span>"
            parts.append(f"<h3>{head}</h3>")
            if ch.get("aktuell"):
                parts.append("<div class='box current'><div class='label'>Aktueller Text</div>" + md_to_html(ch["aktuell"], 3) + "</div>")
            if ch.get("vorschlag"):
                parts.append("<div class='box suggest'><div class='label'>Vorschlag</div>" + md_to_html(ch["vorschlag"], 3) + "</div>")
            if ch.get("warum"):
                parts.append("<p class='why'><b>Warum:</b> " + inline_md(ch["warum"]) + "</p>")
            if ch.get("beibehaltene_hedges"):
                parts.append("<p class='why'><b>Bewusst vorsichtig gelassen:</b> " + "; ".join(inline_md(h) for h in ch["beibehaltene_hedges"]) + "</p>")

    if a.get("technik"):
        parts.append("<h2>Technische Empfehlungen</h2><ul>" + "".join(f"<li>{inline_md(t)}</li>" for t in a["technik"]) + "</ul>")

    if a.get("quellen"):
        parts.append("<h2>Belegte Zahlen und Quellen</h2><table><tr><th>Zahl</th><th>Quelle</th><th>Datum</th></tr>")
        for q in a["quellen"]:
            src = esc(q.get("quelle"))
            if q.get("url"):
                src = f"<a href='{esc(q['url'])}'>{src}</a>"
            parts.append(f"<tr><td>{esc(q.get('zahl'))}</td><td>{src}</td><td>{esc(q.get('datum'))}</td></tr>")
        parts.append("</table>")

    if a.get("scorecard"):
        parts.append("<h2>Scorecard</h2><table><tr><th>Faktor</th><th>Befund</th><th>Benchmark</th><th>Status</th></tr>")
        for r in a["scorecard"]:
            parts.append(f"<tr><td>{esc(r.get('faktor'))}</td><td>{inline_md(r.get('befund', ''))}</td><td>{inline_md(r.get('benchmark', ''))}</td><td><span class='{status_class(r.get('status', ''))}'>{esc(r.get('status'))}</span></td></tr>")
        parts.append("</table>")

    if a.get("offene_fragen"):
        parts.append("<h2>Offene Fragen an den Kunden</h2><p class='why'>Antworten auf diese Fragen machen den Text einzigartig. Allgemeinwissen wird nicht zitiert.</p><ol>" + "".join(f"<li>{inline_md(q)}</li>" for q in a["offene_fragen"]) + "</ol>")

    article = None
    if a.get("artikel_text"):
        article = a["artikel_text"]
    elif a.get("artikel_md"):
        with open(a["artikel_md"], encoding="utf-8") as fh:
            article = fh.read()
    if article:
        parts.append("<hr><h2>Überarbeitete Fassung (vollständig)</h2><p class='why'>Eckige Klammern wie [DATEN: …] sind Platzhalter und müssen vor Veröffentlichung gefüllt oder gestrichen werden.</p><div class='article'>")
        parts.append(md_to_html(article, 2))
        parts.append("</div>")

    parts.append("<p class='footer'>Twenty-Eight Agency GmbH · Berlin · twenty-eight.agency · We make public champions.</p>")
    body = "\n".join(parts)
    return f"<!DOCTYPE html>\n<html lang='de'><head><meta charset='utf-8'><title>{esc(a.get('titel', 'GEO-Audit'))}</title><style>{CSS}</style></head><body>\n{body}\n</body></html>\n"


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    with open(sys.argv[1], encoding="utf-8") as fh:
        audit = json.load(fh)
    sys.stdout.write(build(audit))
    return 0


if __name__ == "__main__":
    sys.exit(main())

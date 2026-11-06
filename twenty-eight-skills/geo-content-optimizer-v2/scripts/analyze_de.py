#!/usr/bin/env python3
"""
analyze_de.py – misst einen deutschsprachigen Text gegen die Zitierfähigkeits-
Faktoren aus references/evidenz.md und gibt JSON aus.

Aufruf:
    python3 -I scripts/analyze_de.py seite.md [--html seite.html]
        [--today JJJJ-MM-TT] [--entities kunde-entities.txt]
        [--capsule-min 40] [--capsule-max 60]

Die Zahlen sind Heuristiken. Sie zeigen Problemstellen und machen Vorher/Nachher
vergleichbar. Sie ersetzen kein Urteil über Inhalt, Einzigartigkeit oder Stimme.

Nur Standardbibliothek. Keine Netzwerkzugriffe.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import unicodedata
from collections import Counter
from typing import Iterable

# --------------------------------------------------------------------------- #
# Lexika (Deutsch)
# --------------------------------------------------------------------------- #

FRAGEWOERTER = (
    r"was|wie|warum|wieso|weshalb|wer|wen|wem|wessen|welche[rsnm]?|wann|wo|wohin|"
    r"woher|woran|wodurch|wof(ü|ue)r|womit|wozu|wie ?viele?|lohnt|kann|k(ö|oe)nnen|"
    r"sollte|sollten|ist|sind|gibt es|muss|m(ü|ue)ssen|braucht|brauche|darf|d(ü|ue)rfen|"
    r"funktioniert|hilft|bringt|taugt"
)
RE_FRAGEWORT_ANFANG = re.compile(rf"^\s*(?:{FRAGEWOERTER})\b", re.IGNORECASE)

DEFINITIV_VERBEN = (
    r"ist|sind|bedeutet|bezeichnet|umfasst|gilt als|besteht aus|hei(ß|ss)t|beschreibt|"
    r"kostet|kosten|liegt bei|liegen bei|betr(ä|ae)gt|betragen|senkt|senken|erh(ö|oe)ht|"
    r"erh(ö|oe)hen|steigert|steigern|dauert|dauern|braucht|brauchen|ben(ö|oe)tigt|"
    r"ben(ö|oe)tigen|verdoppelt|halbiert|zeigt|zeigen|belegt|belegen|misst|messen"
)
RE_DEFINITIV = re.compile(
    rf"^(?:der|die|das|ein|eine|einer|eines|dem|den)?\s*[A-ZÄÖÜ][\w\-äöüß]*"
    rf"(?:\s+[\w\-äöüß]+){{0,5}}\s+(?:{DEFINITIV_VERBEN})\b",
    re.UNICODE,
)
RE_DEFINITIV_SATZMITTE = re.compile(
    rf"\b(?:{DEFINITIV_VERBEN})\s+(?:ein|eine|der|die|das|kein|keine)?\s*[\w\-äöüß]+",
    re.IGNORECASE,
)

HEDGES = [
    "kann", "könnte", "könnten", "dürfte", "dürften", "möglicherweise", "eventuell",
    "unter umständen", "in der regel", "meist", "meistens", "oft", "häufig", "tendenziell",
    "eher", "vielleicht", "wohl", "grundsätzlich", "ein stück weit", "gewissermaßen",
    "quasi", "sozusagen", "relativ", "ziemlich", "durchaus", "im grunde", "prinzipiell",
    "unter anderem", "gegebenenfalls", "potenziell", "mitunter", "teilweise",
]
RE_HEDGE = re.compile(r"\b(" + "|".join(re.escape(h) for h in HEDGES) + r")\b", re.IGNORECASE)

VAGE_QUANTOREN = [
    "viele", "zahlreiche", "einige", "diverse", "etliche", "mehrere", "eine vielzahl",
    "immer mehr", "die meisten", "ein großteil", "ein grossteil", "unzählige", "unzaehlige",
    "wenige", "manche", "verschiedene", "jede menge",
]
RE_VAGE = re.compile(r"\b(" + "|".join(re.escape(v) for v in VAGE_QUANTOREN) + r")\b", re.IGNORECASE)

GENERISCHE_REFERENZEN = [
    r"studien zeigen", r"studien belegen", r"untersuchungen zeigen", r"experten sagen",
    r"expert:innen sagen", r"laut experten", r"laut expert:innen", r"fachleute sind sich einig",
    r"es ist bekannt, dass", r"man weiß", r"eine aktuelle studie(?! (?:von|der|des))",
    r"viele unternehmen", r"zahlreiche unternehmen", r"viele tools", r"diverse anbieter",
    r"zahlreiche anbieter", r"die forschung zeigt", r"erfahrungsgemäß", r"wie allgemein bekannt",
]
RE_GENERISCH = re.compile("|".join(GENERISCHE_REFERENZEN), re.IGNORECASE)

FLUFF_EINSTIEGE = [
    r"in der heutigen zeit", r"in der heutigen", r"in einer welt, in der", r"heutzutage",
    r"es ist kein geheimnis", r"immer mehr unternehmen", r"in zeiten von", r"im digitalen zeitalter",
    r"seit jeher", r"schon immer", r"wie wir alle wissen", r"in diesem artikel", r"in diesem beitrag",
    r"im folgenden", r"wir alle kennen", r"stellen sie sich vor", r"stell dir vor",
    r"die digitalisierung schreitet", r"spätestens seit",
]
RE_FLUFF = re.compile("|".join(FLUFF_EINSTIEGE), re.IGNORECASE)

TAKEAWAY_HEADINGS = re.compile(
    r"^(das wichtigste in k(ü|ue)rze|kurz gefasst|kurz & knapp|kurz und knapp|auf einen blick|"
    r"zusammenfassung|kernaussagen|die wichtigsten punkte|das wichtigste|(ü|ue)berblick|"
    r"key takeaways|takeaways|tl;?dr|fazit vorab|in k(ü|ue)rze)\b",
    re.IGNORECASE,
)
SUMMARY_HEADINGS = re.compile(r"^(fazit|zusammenfassung|das wichtigste|key takeaways|tl;?dr|kernaussagen)\b", re.IGNORECASE)

PRONOMEN_ANFANG = re.compile(
    r"^(es|das|dies|diese|dieser|dieses|sie|er|hier|dabei|damit|dadurch|deshalb|daher|"
    r"außerdem|ausserdem|zudem|so|also|dann|darum|hierbei|hierzu)\b",
    re.IGNORECASE,
)

CTA_MUSTER = re.compile(
    r"(kontakt|erstgespr(ä|ae)ch|termin|angebot anfordern|jetzt anfragen|sprechen sie uns an|"
    r"sprich uns an|schreib uns|schreiben sie uns|unverbindlich|kostenlos(es)? (erst)?gespr(ä|ae)ch|"
    r"demo|beratung anfragen|mailto:|/kontakt|kennenlernen|lass uns sprechen|lassen sie uns sprechen)",
    re.IGNORECASE,
)

STOPWORDS_DE = set("""
der die das ein eine einer eines einem einen und oder aber doch denn weil dass ob wenn als wie
was wer wo wann warum wieso weshalb welche welcher welches wem wen wessen ist sind war waren wird
werden wurde wurden hat haben hatte hatten kann können könnte soll sollen sollte muss müssen darf
dürfen mag mögen mit ohne für von vom zum zur zu bei nach vor über unter zwischen durch gegen um an
auf aus in im ins am es sie er ich du wir ihr man sich nicht kein keine auch noch nur schon sehr mehr
so dann da hier dort dies diese dieser dieses jene alle allem allen aller alles andere anderen
dem den des ja nein bzw etwa ca sowie also beim seit bis je desto ihre ihrer ihrem ihren sein seine
seiner seinem seinen unser unsere unserer unserem unseren euer eure the and of to a
""".split())

ABKUERZUNGEN = {
    "z. b", "z.b", "bzw", "ca", "u. a", "u.a", "d. h", "d.h", "dr", "prof", "nr", "mio", "mrd",
    "tsd", "evtl", "ggf", "inkl", "exkl", "vgl", "usw", "etc", "sog", "jh", "st", "str", "tel",
    "abs", "art", "bzgl", "max", "min", "mind", "o. ä", "o.ä", "u. u", "u.u", "s", "vs", "co",
    "gmbh", "ag", "e. v", "e.v", "resp", "ebd", "hrsg", "aufl", "bd", "jan", "feb", "mär", "apr",
    "jun", "jul", "aug", "sep", "sept", "okt", "nov", "dez",
}

MONATE = {
    "januar": 1, "jänner": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4, "mai": 5,
    "juni": 6, "juli": 7, "august": 8, "september": 9, "oktober": 10, "november": 11,
    "dezember": 12, "jan": 1, "feb": 2, "mär": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "sept": 9, "okt": 10, "nov": 11, "dez": 12,
}

FIRMEN_SUFFIXE = re.compile(r"\b([A-ZÄÖÜ][\w\-äöüß&.]*(?:\s+[A-ZÄÖÜ][\w\-äöüß&.]*){0,3})\s+(GmbH|AG|SE|KG|KGaA|e\. ?V\.|gGmbH|UG|Inc\.|Ltd\.|S\.A\.|Co\. KG)\b")

RE_ZAHL = re.compile(r"(?<![\w,.])(?:\d{1,3}(?:[.\s]\d{3})+|\d+)(?:[,.]\d+)?\s?(?:%|Prozent|€|EUR|Euro|Mio\.?|Mrd\.?|Tsd\.?|Millionen|Milliarden|Prozentpunkte|pp)?", re.UNICODE)
RE_JAHR = re.compile(r"\b(19[5-9]\d|20[0-4]\d)\b")
RE_AKRONYM = re.compile(r"\b[A-ZÄÖÜ]{2,}(?:[a-z]{0,2})?\b")
RE_BINNENMAJUSKEL = re.compile(r"\b[a-z]+[A-Z][\w]*\b|\b[A-Z][a-z]+[A-Z][\w]*\b")
RE_URL = re.compile(r"https?://[^\s)>\]]+")
RE_WORT = re.compile(r"[^\W\d_]+(?:[-'’][^\W\d_]+)*", re.UNICODE)
RE_TOKEN = re.compile(r"[^\W_]+(?:[-'’.,][^\W_]+)*%?", re.UNICODE)

# --------------------------------------------------------------------------- #
# Markdown-Parsing
# --------------------------------------------------------------------------- #

class Block:
    __slots__ = ("kind", "level", "text", "items", "rows", "line")

    def __init__(self, kind: str, text: str = "", level: int = 0, items=None, rows=None, line: int = 0):
        self.kind = kind          # heading | para | list | table | code
        self.level = level
        self.text = text
        self.items = items or []
        self.rows = rows or []
        self.line = line

    def words(self) -> int:
        if self.kind == "list":
            return sum(len(RE_WORT.findall(i)) for i in self.items)
        if self.kind == "table":
            return sum(len(RE_WORT.findall(" ".join(r))) for r in self.rows)
        return len(RE_WORT.findall(self.text))


def strip_inline_md(s: str) -> str:
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"`([^`]*)`", r"\1", s)
    s = re.sub(r"(\*\*|__)(.*?)\1", r"\2", s)
    s = re.sub(r"(\*|_)(.*?)\1", r"\2", s)
    s = re.sub(r"<[^>]+>", "", s)
    return s.strip()


def parse_markdown(md: str) -> list[Block]:
    blocks: list[Block] = []
    lines = md.splitlines()
    i, n = 0, len(lines)
    para: list[str] = []
    para_line = 0

    def flush_para():
        nonlocal para
        if para:
            blocks.append(Block("para", strip_inline_md(" ".join(para)), line=para_line))
            para = []

    in_code = False
    while i < n:
        line = lines[i]
        if line.strip().startswith("```"):
            flush_para()
            in_code = not in_code
            if in_code:
                blocks.append(Block("code", line=i + 1))
            i += 1
            continue
        if in_code:
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            flush_para()
            blocks.append(Block("heading", strip_inline_md(m.group(2)), level=len(m.group(1)), line=i + 1))
            i += 1
            continue
        if re.match(r"^\s*\|.*\|\s*$", line) and i + 1 < n and re.match(r"^\s*\|?\s*:?-{3,}", lines[i + 1]):
            flush_para()
            rows = []
            start = i
            while i < n and re.match(r"^\s*\|.*\|\s*$", lines[i]):
                if not re.match(r"^\s*\|?\s*:?-{3,}", lines[i]):
                    cells = [strip_inline_md(c) for c in lines[i].strip().strip("|").split("|")]
                    rows.append(cells)
                i += 1
            blocks.append(Block("table", rows=rows, line=start + 1))
            continue
        if re.match(r"^\s*([-*+]|\d+[.)])\s+", line):
            flush_para()
            items = []
            start = i
            while i < n and (re.match(r"^\s*([-*+]|\d+[.)])\s+", lines[i]) or (lines[i].startswith("  ") and lines[i].strip())):
                if re.match(r"^\s*([-*+]|\d+[.)])\s+", lines[i]):
                    items.append(strip_inline_md(re.sub(r"^\s*([-*+]|\d+[.)])\s+", "", lines[i])))
                else:
                    items[-1] += " " + strip_inline_md(lines[i])
                i += 1
            blocks.append(Block("list", items=items, line=start + 1))
            continue
        if not line.strip():
            flush_para()
            i += 1
            continue
        if not para:
            para_line = i + 1
        para.append(line.strip())
        i += 1
    flush_para()
    return blocks


# --------------------------------------------------------------------------- #
# Sprachwerkzeuge
# --------------------------------------------------------------------------- #

def split_sentences(text: str) -> list[str]:
    """Satztrennung für Deutsch mit Abkürzungsschutz."""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    out, buf = [], ""
    tokens = re.split(r"(?<=[.!?…])\s+(?=[\"“„»(]?[A-ZÄÖÜ0-9])", text)
    for t in tokens:
        if buf:
            buf = buf + " " + t
        else:
            buf = t
        tail = buf.rstrip(".!?…").split()
        last = tail[-1].lower().strip("(\"“„»") if tail else ""
        last2 = " ".join(tail[-2:]).lower() if len(tail) >= 2 else last
        if (last in ABKUERZUNGEN or last2 in ABKUERZUNGEN or re.fullmatch(r"\d{1,2}", last)) and buf.endswith("."):
            continue
        out.append(buf.strip())
        buf = ""
    if buf:
        out.append(buf.strip())
    return [s for s in out if len(RE_WORT.findall(s)) >= 2]


def syllables_de(word: str) -> int:
    w = word.lower()
    w = re.sub(r"[^a-zäöüß]", "", w)
    if not w:
        return 0
    w = re.sub(r"(ei|ai|au|eu|äu|ie|oi|ui|ey|ay|ou)", "V", w)
    w = re.sub(r"[aeiouäöüy]+", "V", w)
    count = w.count("V")
    if w.endswith("e") and count > 1 and not w.endswith("Ve"):
        pass
    return max(1, count)


def lix(words: list[str], n_sentences: int) -> float | None:
    if not words or not n_sentences:
        return None
    long_words = sum(1 for w in words if len(w) > 6)
    return round(len(words) / n_sentences + 100 * long_words / len(words), 1)


def wiener_sachtextformel_1(words: list[str], n_sentences: int) -> float | None:
    if not words or not n_sentences:
        return None
    n = len(words)
    ms = 100 * sum(1 for w in words if syllables_de(w) >= 3) / n
    sl = n / n_sentences
    iw = 100 * sum(1 for w in words if len(w) > 6) / n
    es = 100 * sum(1 for w in words if syllables_de(w) == 1) / n
    return round(0.1935 * ms + 0.1672 * sl + 0.1297 * iw - 0.0327 * es - 0.875, 1)


def content_words(text: str) -> set[str]:
    return {w.lower() for w in RE_WORT.findall(text) if w.lower() not in STOPWORDS_DE and len(w) > 2}


def language_guess(text: str) -> str:
    toks = [w.lower() for w in RE_WORT.findall(text)][:2000]
    if not toks:
        return "unbekannt"
    de = sum(1 for t in toks if t in {"und", "der", "die", "das", "nicht", "ist", "mit", "für", "auf", "ein", "eine", "sich", "auch", "werden"})
    en = sum(1 for t in toks if t in {"the", "and", "of", "to", "is", "that", "with", "for", "are", "this", "you", "your"})
    if de >= en * 1.5:
        return "de"
    if en >= de * 1.5:
        return "en"
    return "gemischt"


# --------------------------------------------------------------------------- #
# Konkretheit (Entity-Dichte, deutschtauglich)
# --------------------------------------------------------------------------- #

def load_entities(path: str | None) -> set[str]:
    if not path:
        return set()
    with open(path, encoding="utf-8") as fh:
        return {ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")}


def concrete_tokens(text: str, known: set[str]) -> tuple[int, int, Counter]:
    """Zählt 'konkrete' Tokens: Zahlen, Jahre, Prozent, Währungen, Akronyme,
    Binnenmajuskeln, Firmen mit Rechtsform, bekannte Kunden-Entitäten, URLs/Domains.
    Deutsche Nomen werden NICHT allein wegen Großschreibung gezählt."""
    found: Counter = Counter()
    scratch = text
    for ent in sorted(known, key=len, reverse=True):
        cnt = len(re.findall(re.escape(ent), scratch))
        if cnt:
            found[ent] += cnt
            scratch = re.sub(re.escape(ent), " ", scratch)
    for m in FIRMEN_SUFFIXE.finditer(scratch):
        found[m.group(0)] += 1
    scratch = FIRMEN_SUFFIXE.sub(" ", scratch)
    for m in RE_URL.finditer(scratch):
        found[re.sub(r"^https?://(www\.)?", "", m.group(0)).split("/")[0]] += 1
    scratch = RE_URL.sub(" ", scratch)
    for m in re.finditer(r"\b[\w-]+\.(de|com|org|net|io|ai|ch|at|eu|agency)\b", scratch):
        found[m.group(0)] += 1
    for m in RE_ZAHL.finditer(scratch):
        if m.group(0).strip():
            found[m.group(0).strip()] += 1
    for m in RE_AKRONYM.finditer(scratch):
        found[m.group(0)] += 1
    for m in RE_BINNENMAJUSKEL.finditer(scratch):
        found[m.group(0)] += 1
    total = len(RE_TOKEN.findall(text))
    concrete = sum(found.values())
    return concrete, total, found


# --------------------------------------------------------------------------- #
# HTML-Hilfen (Frische, Tabellen, Schema)
# --------------------------------------------------------------------------- #

def parse_german_date(s: str) -> dt.date | None:
    s = s.strip()
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    m = re.search(r"\b(\d{1,2})\.\s?(\d{1,2})\.\s?(\d{4})\b", s)
    if m:
        try:
            return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None
    m = re.search(r"\b(\d{1,2})\.\s?([A-Za-zäöüÄÖÜ]+)\.?\s(\d{4})\b", s)
    if m and m.group(2).lower() in MONATE:
        try:
            return dt.date(int(m.group(3)), MONATE[m.group(2).lower()], int(m.group(1)))
        except ValueError:
            return None
    m = re.search(r"\b([A-Za-zäöüÄÖÜ]+)\s(\d{4})\b", s)
    if m and m.group(1).lower() in MONATE:
        return dt.date(int(m.group(2)), MONATE[m.group(1).lower()], 1)
    return None


def extract_dates_html(html: str) -> dict:
    out = {"date_modified": None, "date_published": None, "visible_label": None, "sources": []}
    for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.S | re.I):
        try:
            data = json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                for key, target in (("dateModified", "date_modified"), ("datePublished", "date_published")):
                    if key in node and isinstance(node[key], str):
                        d = parse_german_date(node[key])
                        if d and (out[target] is None or d > out[target]):
                            out[target] = d
                            out["sources"].append(f"json-ld:{key}")
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
    for prop, target in (
        ("article:modified_time", "date_modified"), ("og:updated_time", "date_modified"),
        ("article:published_time", "date_published"), ("date", "date_published"),
        ("last-modified", "date_modified"), ("dcterms.modified", "date_modified"),
    ):
        m = re.search(rf'<meta[^>]+(?:property|name)=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']+)', html, re.I)
        if m:
            d = parse_german_date(m.group(1))
            if d and (out[target] is None or d > out[target]):
                out[target] = d
                out["sources"].append(f"meta:{prop}")
    for m in re.finditer(r'<time[^>]+datetime=["\']([^"\']+)', html, re.I):
        d = parse_german_date(m.group(1))
        if d and (out["date_published"] is None or d > out["date_published"]):
            out["date_published"] = d
            out["sources"].append("time@datetime")
    text = re.sub(r"<[^>]+>", " ", html)
    m = re.search(r"(stand|aktualisiert am|zuletzt aktualisiert|letzte aktualisierung|updated|ver(ö|oe)ffentlicht am)\s*[:\-–]?\s*([^<\n]{3,40})", text, re.I)
    if m:
        d = parse_german_date(m.group(3))
        if d:
            out["visible_label"] = d
            out["sources"].append("sichtbar:" + m.group(1).lower())
    return out


def schema_types(html: str) -> list[str]:
    types: list[str] = []
    for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.S | re.I):
        try:
            data = json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                t = node.get("@type")
                if isinstance(t, str):
                    types.append(t)
                elif isinstance(t, list):
                    types.extend(str(x) for x in t)
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
    return sorted(set(types))


# --------------------------------------------------------------------------- #
# Analyse
# --------------------------------------------------------------------------- #

def analyze(md: str, html: str | None, today: dt.date, known_entities: set[str], cap_min: int, cap_max: int) -> dict:
    blocks = parse_markdown(md)
    prose_blocks = [b for b in blocks if b.kind in ("para", "list")]
    prose_text = " ".join(b.text if b.kind == "para" else ". ".join(b.items) for b in prose_blocks)
    all_sentences = split_sentences(prose_text)
    all_words = RE_WORT.findall(prose_text)
    total_words = len(all_words)
    headings = [b for b in blocks if b.kind == "heading"]
    h1 = next((b for b in headings if b.level == 1), None)

    result: dict = {
        "meta": {
            "sprache": language_guess(prose_text),
            "wortzahl_fliesstext": total_words,
            "saetze": len(all_sentences),
            "absaetze": sum(1 for b in blocks if b.kind == "para"),
            "ueberschriften": {f"h{l}": sum(1 for h in headings if h.level == l) for l in range(1, 5)},
            "today": today.isoformat(),
            "hinweis": "Heuristiken. Vor dem Urteil references/evidenz.md lesen.",
        }
    }
    if result["meta"]["sprache"] != "de":
        result["meta"]["warnung"] = "Text wirkt nicht (rein) deutsch. Lexika und Lesbarkeitsformeln sind auf Deutsch kalibriert."

    # ---- POS-DOC: Ski-Ramp ------------------------------------------------- #
    bands = {"erste_30": [], "mitte_30_70": [], "letzte_30": []}
    cum = 0
    first_definitive_at = None
    for b in prose_blocks:
        text = b.text if b.kind == "para" else ". ".join(b.items)
        for s in split_sentences(text):
            wc = len(RE_WORT.findall(s))
            pos = cum / total_words if total_words else 0
            band = "erste_30" if pos < 0.3 else ("mitte_30_70" if pos < 0.7 else "letzte_30")
            bands[band].append(s)
            if first_definitive_at is None and (RE_DEFINITIV.search(s) or RE_DEFINITIV_SATZMITTE.search(s)) and not RE_HEDGE.search(s):
                first_definitive_at = round(pos * 100, 1)
            cum += wc
    band_stats = {}
    for name, sents in bands.items():
        words_b = RE_WORT.findall(" ".join(sents))
        concrete, total, _ = concrete_tokens(" ".join(sents), known_entities)
        band_stats[name] = {
            "saetze": len(sents),
            "woerter": len(words_b),
            "definitive_saetze": sum(1 for s in sents if RE_DEFINITIV.search(s) and not RE_HEDGE.search(s)),
            "konkretheits_dichte_pct": round(100 * concrete / total, 1) if total else 0.0,
        }
    intro_paras = [b.text for b in blocks if b.kind == "para"][:2]
    fluff = [m.group(0) for p in intro_paras for m in RE_FLUFF.finditer(p)]
    late_summary = None
    cum = 0
    for b in blocks:
        if b.kind == "heading" and SUMMARY_HEADINGS.search(b.text) and total_words and cum / total_words > 0.6:
            late_summary = {"heading": b.text, "position_pct": round(100 * cum / total_words, 1)}
        if b.kind in ("para", "list"):
            cum += b.words()
    result["POS-DOC"] = {
        "baender": band_stats,
        "erste_definitive_aussage_bei_pct": first_definitive_at,
        "fluff_im_einstieg": fluff,
        "spaete_zusammenfassung": late_summary,
        "benchmark": "44,2 % der ChatGPT-Zitate stammen aus den ersten 30 % der Seite (Studie 1). Kernaussage, stärkste Zahl, klarste Definition nach oben.",
    }

    # ---- DEFINITIVE ---------------------------------------------------------- #
    definitive = [s for s in all_sentences if (RE_DEFINITIV.search(s) or RE_DEFINITIV_SATZMITTE.search(s)) and not RE_HEDGE.search(s)]
    candidates = []
    for s in all_sentences:
        if s in definitive:
            continue
        reasons = []
        if RE_HEDGE.search(s):
            reasons.append("Hedge: " + RE_HEDGE.search(s).group(0))
        if RE_VAGE.search(s):
            reasons.append("vager Quantor: " + RE_VAGE.search(s).group(0))
        if re.match(r"^(es gibt|es ist|es kann|es lässt sich|man kann|man sollte)", s, re.I):
            reasons.append("indirekter Einstieg")
        if reasons:
            candidates.append({"satz": s[:160], "gruende": reasons})
    result["DEFINITIVE"] = {
        "anteil_definitiver_saetze_pct": round(100 * len(definitive) / len(all_sentences), 1) if all_sentences else 0.0,
        "hedges_gesamt": len(RE_HEDGE.findall(prose_text)),
        "vage_quantoren_gesamt": len(RE_VAGE.findall(prose_text)),
        "umschreib_kandidaten": candidates[:12],
        "benchmark": "Zitierte Passagen: 36,2 % definitive Sprache vs. 20,2 % nicht zitiert (Studie 1). Hedges nur entfernen, wo die Fakten der Seite es tragen.",
    }

    # ---- QA + CAPSULE ------------------------------------------------------- #
    qa_items = []
    for idx, b in enumerate(blocks):
        if b.kind != "heading" or b.level < 2:
            continue
        text = b.text.strip()
        if TAKEAWAY_HEADINGS.search(text):
            continue  # Takeaway-Block wird unter TAKEAWAYS bewertet, nicht als Capsule
        is_q_mark = text.endswith("?")
        is_q_word = bool(RE_FRAGEWORT_ANFANG.match(text))
        nxt = next((x for x in blocks[idx + 1:] if x.kind in ("para", "list", "table", "heading")), None)
        capsule = None
        if nxt is not None and nxt.kind == "para":
            wc = len(RE_WORT.findall(nxt.text))
            first = split_sentences(nxt.text)[:1]
            capsule = {
                "woerter": wc,
                "status": "ok" if cap_min <= wc <= cap_max else ("zu kurz" if wc < cap_min else "zu lang"),
                "echo": bool(content_words(text) & content_words(nxt.text[:160])),
                "erster_satz_definitiv": bool(first and (RE_DEFINITIV.search(first[0]) or RE_DEFINITIV_SATZMITTE.search(first[0])) and not RE_HEDGE.search(first[0])),
                "beginnt_mit_pronomen": bool(PRONOMEN_ANFANG.match(nxt.text)),
            }
        elif nxt is not None:
            capsule = {"status": "kein Absatz direkt unter der Überschrift", "naechster_block": nxt.kind}
        qa_items.append({
            "heading": text, "level": b.level,
            "frage": is_q_mark or is_q_word,
            "frage_ohne_fragezeichen": (is_q_word and not is_q_mark),
            "capsule": capsule,
        })
    n_h = len(qa_items)
    n_q = sum(1 for q in qa_items if q["frage"])
    n_cap_ok = sum(1 for q in qa_items if q["capsule"] and q["capsule"].get("status") == "ok")
    result["QA"] = {
        "h2_h3_gesamt": n_h,
        "frage_headings": n_q,
        "anteil_frage_headings_pct": round(100 * n_q / n_h, 1) if n_h else None,
        "frage_ohne_fragezeichen": sum(1 for q in qa_items if q["frage_ohne_fragezeichen"]),
        "details": qa_items,
        "benchmark": "Zitierte Passagen enthalten doppelt so oft Fragezeichen (18 % vs. 8,9 %); 78,4 % davon aus Überschriften (Studie 1). Q&A-Format gewinnt im Retrieval-Test (Studie 4).",
    }
    result["CAPSULE"] = {
        "ziel_woerter": f"{cap_min}-{cap_max}",
        "headings_mit_capsule_im_zielbereich": n_cap_ok,
        "anteil_pct": round(100 * n_cap_ok / n_h, 1) if n_h else None,
        "benchmark": "Hausregel: 40–60 Wörter vollständige Antwort direkt unter jeder H2/H3. Die kursierende '72,4 %'-Zahl ist nicht primär belegt (siehe evidenz.md, Offen-1).",
    }

    # ---- KONKRETHEIT (Entity) ------------------------------------------------ #
    concrete, total, found = concrete_tokens(prose_text, known_entities)
    zero_sent = [s for s in all_sentences if concrete_tokens(s, known_entities)[0] == 0]
    intro_text = " ".join(intro_paras)
    c_i, t_i, _ = concrete_tokens(intro_text, known_entities)
    generics = [m.group(0) for m in RE_GENERISCH.finditer(prose_text)]
    result["KONKRETHEIT"] = {
        "dichte_pct": round(100 * concrete / total, 1) if total else 0.0,
        "dichte_einstieg_pct": round(100 * c_i / t_i, 1) if t_i else 0.0,
        "saetze_ohne_konkretes_pct": round(100 * len(zero_sent) / len(all_sentences), 1) if all_sentences else 0.0,
        "beispiele_saetze_ohne_konkretes": [s[:140] for s in zero_sent[:8]],
        "generische_referenzen": generics,
        "haeufigste_entitaeten": found.most_common(15),
        "kunden_entitaeten_geladen": len(known_entities),
        "methodik": "Zählt Zahlen, Jahre, Prozent, Währung, Akronyme, Binnenmajuskeln, Firmen mit Rechtsform, Domains und per --entities gelistete Namen. Deutsche Nomen zählen nicht allein wegen Großschreibung. Nicht 1:1 mit der englischen Entity-Dichte aus Studie 1 vergleichbar.",
        "ziel": "Heuristik: >= 8 % gesamt, >= 12 % im Einstieg, <= 30 % Sätze ohne Konkretes. Richtwerte, keine Studienwerte.",
    }

    # ---- READ --------------------------------------------------------------- #
    long_sent = [s for s in all_sentences if len(RE_WORT.findall(s)) > 25]
    result["READ"] = {
        "lix": lix(all_words, len(all_sentences)),
        "wiener_sachtextformel_1": wiener_sachtextformel_1(all_words, len(all_sentences)),
        "durchschnittliche_satzlaenge": round(total_words / len(all_sentences), 1) if all_sentences else None,
        "saetze_ueber_25_woerter": len(long_sent),
        "beispiele_lange_saetze": [s[:160] for s in long_sent[:5]],
        "einordnung": "LIX: <40 leicht, 40–50 Sachtext, 50–60 anspruchsvoll, >60 schwer. WSTF1 ≈ Schulstufe: Ratgeber 8–11, Fachtext 11–13. Studie 1 (Englisch, Flesch-Kincaid) ist nicht direkt übertragbar; Richtung gilt: zitierte Texte sind etwas leichter lesbar.",
    }

    # ---- TAKEAWAYS ----------------------------------------------------------- #
    tk = None
    for idx, b in enumerate(blocks):
        if b.kind == "heading" and TAKEAWAY_HEADINGS.search(b.text):
            nxt = next((x for x in blocks[idx + 1:] if x.kind in ("para", "list", "table")), None)
            bullets = len(nxt.items) if nxt and nxt.kind == "list" else 0
            before_words = sum(x.words() for x in blocks[:idx] if x.kind in ("para", "list"))
            tk = {"heading": b.text, "bullets": bullets, "woerter_davor": before_words,
                  "direkt_unter_h1": before_words <= 60,
                  "pass": 3 <= bullets <= 6 and before_words <= 60}
            break
    result["TAKEAWAYS"] = {
        "vorhanden": tk is not None,
        "pass": bool(tk and tk["pass"]),
        "details": tk,
        "benchmark": "Hausregel (abgeleitet aus Studie 1 POS-DOC und Studie 4 CHUNK): 'Das Wichtigste in Kürze' mit 3–6 Bullets direkt unter der H1, nur mit Fakten der Seite.",
    }

    # ---- CHUNK --------------------------------------------------------------- #
    sections = []
    cur = None
    for b in blocks:
        if b.kind == "heading" and b.level >= 2:
            cur = {"heading": b.text, "woerter": 0, "erster_block": None}
            sections.append(cur)
        elif b.kind in ("para", "list", "table") and cur is not None:
            cur["woerter"] += b.words()
            if cur["erster_block"] is None and b.kind == "para":
                cur["erster_block"] = b.text[:80]
    long_paras = [b for b in blocks if b.kind == "para" and b.words() > 120]
    list_words = sum(b.words() for b in blocks if b.kind == "list")
    result["CHUNK"] = {
        "abschnitte_h2_plus": len(sections),
        "abschnitte_ueber_300_woerter": [s["heading"] for s in sections if s["woerter"] > 300],
        "absaetze_ueber_120_woerter": len(long_paras),
        "beispiele_lange_absaetze": [b.text[:120] for b in long_paras[:5]],
        "listenpunkte": sum(len(b.items) for b in blocks if b.kind == "list"),
        "anteil_woerter_in_listen_pct": round(100 * list_words / total_words, 1) if total_words else 0.0,
        "abschnitte_mit_pronomen_einstieg": [s["heading"] for s in sections if s["erster_block"] and PRONOMEN_ANFANG.match(s["erster_block"])],
        "benchmark": "Retrieval-Test (Studie 4): Q&A > strukturiert > Fließtext. Faustregeln: Absatz <= 120 Wörter, Abschnitt <= 300 Wörter ohne Zwischenüberschrift, Abschnitt nennt das Subjekt statt 'Es/Das/Dabei'.",
    }

    # ---- TABLE --------------------------------------------------------------- #
    md_tables = [b for b in blocks if b.kind == "table"]
    first_pos = None
    if md_tables:
        cum = 0
        for b in blocks:
            if b is md_tables[0]:
                first_pos = round(100 * cum / total_words, 1) if total_words else 0
                break
            if b.kind in ("para", "list"):
                cum += b.words()
    result["TABLE"] = {
        "markdown_tabellen": len(md_tables),
        "html_tabellen": len(re.findall(r"<table\b", html, re.I)) if html else None,
        "erste_tabelle_bei_pct": first_pos,
        "benchmark": "30 % der ChatGPT-zitierten B2B-SaaS-Seiten enthalten <table> vs. 13 % der Google-Top-Seiten (Studie 2, korrelativ, eine Branche). Tabellen nur, wo Inhalt tabellarisch ist.",
    }

    # ---- FRESH --------------------------------------------------------------- #
    dates = extract_dates_html(html) if html else {"date_modified": None, "date_published": None, "visible_label": None, "sources": []}
    years = sorted({int(y) for y in RE_JAHR.findall(prose_text)})
    latest = max([d for d in (dates["date_modified"], dates["date_published"], dates["visible_label"]) if d], default=None)
    days = (today - latest).days if latest else None
    result["FRESH"] = {
        "date_modified": dates["date_modified"].isoformat() if dates["date_modified"] else None,
        "date_published": dates["date_published"].isoformat() if dates["date_published"] else None,
        "sichtbares_datum": dates["visible_label"].isoformat() if dates["visible_label"] else None,
        "quellen": dates["sources"],
        "tage_seit_update": days,
        "metadaten_konflikt": bool(dates["date_modified"] and dates["date_published"] and dates["date_modified"] < dates["date_published"]),
        "jahre_im_text": years,
        "veraltete_jahresangabe": bool(years and max(years) < today.year - 1),
        "benchmark": "Zitierte Seiten: 35 % < 3 Monate, 53 % < 6 Monate, ~70 % < 12 Monate aktualisiert; kommerzielle Queries 60 % < 6 Monate (Studie 3, korrelativ, Anbieter-Studie). Keine Fake-Datumsupdates.",
    }

    # ---- CTA (Conversion-Anschluss, Twenty-Eight) ---------------------------- #
    cta_hits = []
    cum = 0
    for b in blocks:
        if b.kind in ("para", "list"):
            text = b.text if b.kind == "para" else " ".join(b.items)
            for m in CTA_MUSTER.finditer(text):
                cta_hits.append({"treffer": m.group(0), "position_pct": round(100 * cum / total_words, 1) if total_words else 0})
            cum += b.words()
    result["CTA"] = {
        "treffer": len(cta_hits),
        "positionen_pct": [h["position_pct"] for h in cta_hits],
        "nur_am_ende": bool(cta_hits) and all(h["position_pct"] > 80 for h in cta_hits),
        "hinweis": "Hausregel: kontextuelle CTAs an intent-passenden Stellen, nicht ein generischer am Ende. Kein Zitierfaktor, ein Geschäftsfaktor.",
    }

    # ---- SCHEMA / Technik ---------------------------------------------------- #
    if html:
        lang = re.search(r"<html[^>]+lang=[\"']([^\"']+)", html, re.I)
        result["SCHEMA"] = {
            "json_ld_typen": schema_types(html),
            "html_lang": lang.group(1) if lang else None,
            "hreflang_alternates": len(re.findall(r'rel=["\']alternate["\'][^>]+hreflang=', html, re.I)),
            "faq_schema": "FAQPage" in schema_types(html),
            "hinweis": "Empfehlung im Anhang: Article/FAQPage/HowTo als JSON-LD, hreflang bei /en/-Zwilling.",
        }
    return result


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser(description="Zitierfähigkeits-Messung für deutsche Texte.")
    ap.add_argument("markdown", help="Markdown-Datei der Seite")
    ap.add_argument("--html", help="Roh-HTML der Live-Seite (Tabellen, Datum, Schema)")
    ap.add_argument("--today", help="Referenzdatum JJJJ-MM-TT (Standard: Systemdatum)")
    ap.add_argument("--entities", help="Textdatei mit Kunden-Entitäten, eine pro Zeile")
    ap.add_argument("--capsule-min", type=int, default=40)
    ap.add_argument("--capsule-max", type=int, default=60)
    args = ap.parse_args()

    with open(args.markdown, encoding="utf-8") as fh:
        md = unicodedata.normalize("NFC", fh.read())
    html = None
    if args.html:
        with open(args.html, encoding="utf-8", errors="replace") as fh:
            html = fh.read()
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    known = load_entities(args.entities)
    out = analyze(md, html, today, known, args.capsule_min, args.capsule_max)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

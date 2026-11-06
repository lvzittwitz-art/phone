#!/usr/bin/env python3
"""
check_rewrite_de.py – Schutzprüfung vor der Auslieferung einer Überarbeitung.

Vergleicht Original und Überarbeitung (Markdown) und prüft:
  1. Überschriften-Politik   (strict | fragen | frei)
  2. Satzabdeckung           (welche Originalsätze fehlen oder stark verändert sind)
  3. Zahlen                  (jede Zahl, Prozent-, Euro-, Jahresangabe des Originals muss erhalten sein)
  4. Links                   (jede URL des Originals muss erhalten sein)
  5. Neue Zahlen             (neu eingeführte Zahlen werden zur Verifikation gelistet)
  6. Platzhalter             ([DATEN: …], [QUELLE: …] dürfen im publizierbaren Text nicht stehen bleiben)

Aufruf:
    python3 -I scripts/check_rewrite_de.py original.md ueberarbeitet.md
        [--heading-policy fragen] [--allow-number-drop] [--allow-link-drop]
        [--allow-placeholders] [--present 0.80] [--rewritten 0.50]

Exit 0 = PASS, 1 = FAIL. Nur Standardbibliothek.
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
import unicodedata

FRAGEWORT = re.compile(
    r"^\s*(was|wie|warum|wieso|weshalb|wer|wen|wem|wessen|welche[rsnm]?|wann|wo|wohin|woher|woran|"
    r"wodurch|wof(ü|ue)r|womit|wozu|wie ?viele?|lohnt|kann|k(ö|oe)nnen|sollte|sollten|ist|sind|gibt es|"
    r"muss|m(ü|ue)ssen|braucht|darf|funktioniert|hilft|bringt)\b",
    re.IGNORECASE,
)
ERLAUBTE_NEUE_HEADINGS = re.compile(
    r"^(das wichtigste in k(ü|ue)rze|kurz gefasst|auf einen blick|kernaussagen|key takeaways|"
    r"h(ä|ae)ufige fragen|faq|fragen und antworten)\b",
    re.IGNORECASE,
)
RE_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
RE_URL = re.compile(r"https?://[^\s)>\]\"']+")
RE_ZAHL = re.compile(r"(?<![\w,.])\d{1,3}(?:[.\s]\d{3})+(?:,\d+)?|(?<![\w,.])\d+(?:[,.]\d+)?", re.UNICODE)
RE_PLATZHALTER = re.compile(r"\[(DATEN|QUELLE|ZAHL|BELEG|PRÜFEN|PRUEFEN|TODO)[^\]]*\]", re.IGNORECASE)
RE_WORT = re.compile(r"[^\W\d_]+", re.UNICODE)
ABK = {"z. b", "z.b", "bzw", "ca", "u. a", "u.a", "d. h", "d.h", "dr", "prof", "nr", "mio", "mrd", "tsd", "evtl", "ggf", "inkl", "vgl", "usw", "etc", "sog"}


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return unicodedata.normalize("NFC", fh.read())


def headings(md: str) -> list[tuple[int, str]]:
    out = []
    in_code = False
    for line in md.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = RE_HEADING.match(line)
        if m:
            out.append((len(m.group(1)), m.group(2).strip()))
    return out


def prose(md: str) -> str:
    out = []
    in_code = False
    for line in md.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code or RE_HEADING.match(line) or re.match(r"^\s*\|", line):
            continue
        line = re.sub(r"^\s*([-*+]|\d+[.)])\s+", "", line)
        out.append(line)
    text = "\n".join(out)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`*_>#]", "", text)
    return text


def sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[\"“„»(]?[A-ZÄÖÜ0-9])", text)
    merged, buf = [], ""
    for p in parts:
        buf = (buf + " " + p).strip() if buf else p
        last = buf.rstrip(".!?").split()[-1].lower() if buf.split() else ""
        if last in ABK and buf.endswith("."):
            continue
        merged.append(buf)
        buf = ""
    if buf:
        merged.append(buf)
    return [s for s in merged if len(RE_WORT.findall(s)) >= 4]


def normalize(s: str) -> str:
    s = s.lower().replace("’", "'").replace("‘", "'")
    s = re.sub(r"[^a-z0-9äöüß ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def numbers(text: str) -> set[str]:
    out = set()
    for m in RE_ZAHL.finditer(text):
        raw = m.group(0)
        norm = raw.replace(" ", "").replace(".", "").replace(",", ".") if re.search(r"\d[.\s]\d{3}", raw) else raw.replace(",", ".")
        norm = norm.rstrip(".")
        if norm in {"1", "2", "3"} and not re.search(rf"{re.escape(raw)}\s?(%|prozent|euro|€|mio|mrd|jahre|monate)", text[m.start():m.end() + 10], re.I):
            continue  # Aufzählungen und Kleinzahlen ohne Einheit ignorieren
        out.add(norm)
    return out


def is_question(h: str) -> bool:
    return h.strip().endswith("?") or bool(FRAGEWORT.match(h))


def check_headings(orig: list[tuple[int, str]], rev: list[tuple[int, str]], policy: str) -> tuple[list[str], bool]:
    lines, ok = [], True
    if policy == "frei":
        lines.append(f"  Politik 'frei': {len(orig)} → {len(rev)} Überschriften, keine Durchsetzung.")
        added = [h for h in rev if h not in orig]
        removed = [h for h in orig if h not in rev]
        for lvl, h in removed:
            lines.append(f"  entfernt   H{lvl} {h}")
        for lvl, h in added:
            lines.append(f"  neu        H{lvl} {h}")
        return lines, True
    rev_work = list(rev)
    # Erlaubte Ergänzungen herausnehmen (nur Politik 'fragen')
    if policy == "fragen":
        allowed = [h for h in rev_work if ERLAUBTE_NEUE_HEADINGS.search(h[1]) and h not in orig]
        for h in allowed:
            rev_work.remove(h)
            lines.append(f"  erlaubt    H{h[0]} {h[1]}  (neue Zusatzüberschrift)")
    if len(rev_work) != len(orig):
        ok = False
        lines.append(f"  FAIL       Anzahl: Original {len(orig)}, Überarbeitung {len(rev_work)} (ohne erlaubte Ergänzungen)")
    for i, (olvl, otxt) in enumerate(orig):
        if i >= len(rev_work):
            lines.append(f"  FAIL       fehlt: H{olvl} {otxt}")
            ok = False
            continue
        rlvl, rtxt = rev_work[i]
        if olvl != rlvl:
            lines.append(f"  FAIL       Ebene H{olvl}→H{rlvl}: {otxt} → {rtxt}")
            ok = False
        elif normalize(otxt) == normalize(rtxt):
            lines.append(f"  gleich     H{olvl} {otxt}")
        elif policy == "fragen" and is_question(rtxt):
            lines.append(f"  frage      H{olvl} {otxt} → {rtxt}")
        else:
            lines.append(f"  FAIL       umformuliert ohne Frageform: {otxt} → {rtxt}")
            ok = False
    for extra in rev_work[len(orig):]:
        lines.append(f"  FAIL       zusätzlich: H{extra[0]} {extra[1]}")
        ok = False
    return lines, ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("original")
    ap.add_argument("revised")
    ap.add_argument("--heading-policy", choices=["strict", "fragen", "frei"], default="fragen",
                    help="strict: identisch; fragen: Umformulierung nur als Frage, Takeaways/FAQ dürfen dazu; frei: nur Bericht")
    ap.add_argument("--allow-number-drop", action="store_true")
    ap.add_argument("--allow-link-drop", action="store_true")
    ap.add_argument("--allow-placeholders", action="store_true", help="für Zwischenstände mit [DATEN: …]-Markern")
    ap.add_argument("--present", type=float, default=0.80)
    ap.add_argument("--rewritten", type=float, default=0.50)
    args = ap.parse_args()

    o_md, r_md = read(args.original), read(args.revised)
    fails: list[str] = []

    print("ÜBERSCHRIFTEN")
    lines, ok = check_headings(headings(o_md), headings(r_md), args.heading_policy)
    print("\n".join(lines))
    if not ok:
        fails.append("Überschriften-Regel verletzt")

    print("\nSATZABDECKUNG")
    o_s, r_s = sentences(prose(o_md)), sentences(prose(r_md))
    r_norm = [normalize(s) for s in r_s]
    dropped, rewritten = [], []
    for s in o_s:
        n = normalize(s)
        best = max((difflib.SequenceMatcher(None, n, rn).ratio() for rn in r_norm), default=0.0)
        if best >= args.present:
            continue
        (rewritten if best >= args.rewritten else dropped).append((best, s))
    if not dropped and not rewritten:
        print("  Jeder Originalsatz ist (nahezu) wörtlich enthalten.")
    for score, s in rewritten:
        print(f"  umgeschrieben {score:.2f}  {s[:150]}")
    for score, s in dropped:
        print(f"  FEHLT?        {score:.2f}  {s[:150]}")
    print(f"  Original {len(o_s)} Sätze · Überarbeitung {len(r_s)} Sätze · neu hinzugekommen ca. {max(0, len(r_s) - len(o_s) + len(dropped))}")
    print("  Hinweis: 'FEHLT?' heißt: bewusst gestrichen oder versehentlich verloren. Jeden Treffer prüfen.")

    print("\nZAHLEN")
    o_n, r_n = numbers(prose(o_md) + " " + " ".join(h for _, h in headings(o_md))), numbers(r_md)
    missing_n = sorted(o_n - r_n)
    new_n = sorted(r_n - o_n)
    if missing_n:
        print("  FEHLEN im neuen Text: " + ", ".join(missing_n))
        if not args.allow_number_drop:
            fails.append("Zahlen des Originals fehlen")
    else:
        print("  Alle Zahlen des Originals sind erhalten.")
    if new_n:
        print("  NEU, vor Veröffentlichung belegen: " + ", ".join(new_n))

    print("\nLINKS")
    o_l, r_l = set(RE_URL.findall(o_md)), set(RE_URL.findall(r_md))
    missing_l = sorted(o_l - r_l)
    if missing_l:
        print("  FEHLEN: " + ", ".join(missing_l))
        if not args.allow_link_drop:
            fails.append("Links des Originals fehlen")
    else:
        print(f"  Alle {len(o_l)} Links des Originals sind erhalten." if o_l else "  Original enthält keine Links.")
    for u in sorted(r_l - o_l):
        print(f"  neu: {u}")

    print("\nPLATZHALTER")
    ph = RE_PLATZHALTER.findall(r_md)
    ph_full = [m.group(0) for m in RE_PLATZHALTER.finditer(r_md)]
    if ph_full:
        for p in ph_full:
            print(f"  {p}")
        if args.allow_placeholders:
            print("  Zwischenstand: Platzhalter erlaubt. Vor Auslieferung füllen oder streichen.")
        else:
            fails.append(f"{len(ph_full)} Platzhalter im Text")
    else:
        print("  Keine Platzhalter.")

    print()
    if fails:
        print("RESULT: FAIL (" + "; ".join(fails) + ")")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

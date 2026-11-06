#!/usr/bin/env python3
"""
html_to_md.py – wandelt gespeichertes HTML in Markdown für analyze_de.py um.

Holt NICHTS aus dem Netz. Seite vorher laden, z. B.:
    curl -sSL -A "Mozilla/5.0 (Macintosh) AppleWebKit/537.36 Chrome/124 Safari/537.36" \
        "https://beispiel.de/seite" -o seite.html
    python3 -I scripts/html_to_md.py seite.html > seite.md

Hauptinhalt: <article>, sonst <main>, sonst <body>. Entfernt Navigation, Header,
Footer, Aside, Formulare, Skripte und Elemente mit class/id wie nav, menu, sidebar,
cookie, share, related, newsletter, breadcrumb, toc, comment.
Nur Standardbibliothek.
"""

from __future__ import annotations

import html
import re
import sys
from html.parser import HTMLParser

DROP_TAGS = {"script", "style", "noscript", "svg", "nav", "header", "footer", "aside", "form",
             "button", "iframe", "template", "select", "picture", "figure", "video", "audio", "canvas"}
DROP_CLASS = re.compile(r"(nav|menu|sidebar|cookie|share|sharing|related|newsletter|subscribe|breadcrumb|toc|comment|popup|modal|banner|promo|footer|header|social|author-box|tags)", re.I)
BLOCK_TAGS = {"p", "div", "section", "article", "main", "li", "ul", "ol", "table", "tr", "blockquote", "pre", "h1", "h2", "h3", "h4", "h5", "h6", "br", "hr", "dd", "dt", "dl"}


def pick_main(doc: str) -> str:
    for tag in ("article", "main", "body"):
        m = re.search(rf"<{tag}\b[^>]*>(.*)</{tag}>", doc, re.S | re.I)
        if m:
            return m.group(1)
    return doc


class MD(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.skip = 0
        self.stack: list[str] = []
        self.list_stack: list[tuple[str, int]] = []
        self.in_table = False
        self.row: list[str] = []
        self.cell: list[str] | None = None
        self.rows: list[list[str]] = []
        self.href: str | None = None
        self.in_pre = False

    def _text(self, s: str) -> None:
        if self.cell is not None:
            self.cell.append(s)
        else:
            self.out.append(s)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.skip:
            if tag not in ("br", "img", "hr", "meta", "link", "input"):
                self.skip += 1
            return
        ident = f"{a.get('class', '')} {a.get('id', '')}"
        if tag in DROP_TAGS or DROP_CLASS.search(ident) or a.get("hidden") is not None or a.get("aria-hidden") == "true":
            if tag not in ("br", "img", "hr", "meta", "link", "input"):
                self.skip = 1
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.out.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag == "p" or tag == "div" or tag == "section" or tag == "blockquote":
            self.out.append("\n\n" + ("> " if tag == "blockquote" else ""))
        elif tag == "br":
            self.out.append("\n")
        elif tag in ("ul", "ol"):
            self.list_stack.append((tag, 0))
            self.out.append("\n")
        elif tag == "li":
            if self.list_stack:
                kind, n = self.list_stack[-1]
                self.list_stack[-1] = (kind, n + 1)
                indent = "  " * (len(self.list_stack) - 1)
                marker = f"{n + 1}." if kind == "ol" else "-"
                self.out.append(f"\n{indent}{marker} ")
            else:
                self.out.append("\n- ")
        elif tag == "table":
            self.in_table, self.rows = True, []
        elif tag == "tr" and self.in_table:
            self.row = []
        elif tag in ("td", "th") and self.in_table:
            self.cell = []
        elif tag in ("strong", "b"):
            self._text("**")
        elif tag in ("em", "i"):
            self._text("*")
        elif tag == "a":
            self.href = a.get("href")
            self._text("[")
        elif tag == "pre":
            self.in_pre = True
            self.out.append("\n\n```\n")
        elif tag == "code" and not self.in_pre:
            self._text("`")
        elif tag == "hr":
            self.out.append("\n\n---\n\n")
        self.stack.append(tag)

    def handle_endtag(self, tag):
        if self.skip:
            self.skip -= 1
            return
        if self.stack and tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "section", "blockquote"):
            self.out.append("\n")
        elif tag in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
            self.out.append("\n")
        elif tag in ("td", "th") and self.cell is not None:
            self.row.append(re.sub(r"\s+", " ", "".join(self.cell)).strip().replace("|", "/"))
            self.cell = None
        elif tag == "tr" and self.in_table:
            if any(c for c in self.row):
                self.rows.append(self.row)
        elif tag == "table" and self.in_table:
            self.in_table = False
            if self.rows:
                width = max(len(r) for r in self.rows)
                rows = [r + [""] * (width - len(r)) for r in self.rows]
                self.out.append("\n\n| " + " | ".join(rows[0]) + " |\n|" + " --- |" * width + "\n")
                for r in rows[1:]:
                    self.out.append("| " + " | ".join(r) + " |\n")
                self.out.append("\n")
        elif tag in ("strong", "b"):
            self._text("**")
        elif tag in ("em", "i"):
            self._text("*")
        elif tag == "a":
            if self.href and self.href.startswith("http"):
                self._text(f"]({self.href})")
            else:
                self._text("]")
            self.href = None
        elif tag == "pre":
            self.in_pre = False
            self.out.append("\n```\n\n")
        elif tag == "code" and not self.in_pre:
            self._text("`")

    def handle_data(self, data):
        if self.skip:
            return
        if not self.in_pre:
            data = re.sub(r"\s+", " ", data)
        self._text(data)


def convert(doc: str) -> str:
    main = pick_main(doc)
    p = MD()
    p.feed(main)
    text = "".join(p.out)
    text = html.unescape(text)
    text = re.sub(r"\*\*\s*\*\*", "", text)
    text = re.sub(r"\[\s*\]\([^)]*\)", "", text)
    text = re.sub(r"\[\s*\]", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+(?=\S)", "\n", text)
    text = re.sub(r"(?<=\n)(#+) +\n", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"^ +", "", text, flags=re.M)
    return text.strip() + "\n"


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    with open(sys.argv[1], encoding="utf-8", errors="replace") as fh:
        sys.stdout.write(convert(fh.read()))
    return 0


if __name__ == "__main__":
    sys.exit(main())

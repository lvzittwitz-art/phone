#!/usr/bin/env python3
"""DACH-Newsjack-Detector: sammelt deutsche RSS/Atom-Feeds, clustert Meldungen,
filtert grob nach Kundenprofil und schreibt Kandidaten für die PR-Triage.

Nur Standardbibliothek. Aufruf immer mit `python3 -I`.

Unterbefehle:
  run      --profile P [--feeds F] [--fixture-dir D] [--out O] [--now ISO]
  feeds    --check [--feeds F]
  profile  --validate P

Das Skript bewertet mechanisch (Frische, Quellenübereinstimmung, Begriffstreffer,
Lane). Standing, Story-Origin und Pitch-Urteil bleiben Aufgabe des Agenten.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 TwentyEightDetector/0.1"
)
TIMEOUT = 15
TITLE_SIM = 0.85

DEFAULT_LANE_WEIGHTS = {
    "leitmedien": 15,
    "arbeitsmarkt": 15,
    "politik": 10,
    "fachpresse_hr": 10,
    "wirtschaft_regional": 8,
    "presseportale": 5,
}

# Deutsche Tragödien-Lexik: Treffer -> harter Brand-Safety-Block.
BRAND_SAFETY_TERMS = [
    "tote", "toter", "todesopfer", "todesfall", "gestorben", "getötet",
    "anschlag", "amoklauf", "amokfahrt", "attentat", "terror", "terroranschlag",
    "suizid", "selbstmord", "selbsttötung",
    "missbrauch", "misshandlung", "vergewaltigung",
    "vermisst", "vermisste",
    "katastrophe", "unglück", "erdbeben", "flutkatastrophe", "hochwasser",
    "krieg", "kriegs", "angriffskrieg", "luftangriff", "bombardierung",
    "gewalt", "gewalttat", "messerangriff", "schießerei",
    "kindesmissbrauch", "kindesentführung", "kinderpornografie",
    "explosion", "flugzeugabsturz", "zugunglück", "massaker", "geisel",
]

AGE_BUCKETS = [
    ("30min", timedelta(minutes=30)),
    ("4h", timedelta(hours=4)),
    ("24h", timedelta(hours=24)),
    ("woche", timedelta(days=7)),
    ("monat", timedelta(days=31)),
]
FRESHNESS_POINTS = {"30min": 40, "4h": 36, "24h": 28, "woche": 12, "monat": 4, "unbekannt": 0}

TRACKING_PARAMS_PREFIX = ("utm_", "fbclid", "gclid", "mc_cid", "mc_eid", "ref", "icid", "wt_")


# ---------------------------------------------------------------- Hilfen

def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def now_from_arg(value: str | None) -> datetime:
    """--now als ISO-Zeit lesen; sonst aktuelle UTC-Zeit."""
    if not value:
        return datetime.now(timezone.utc)
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def strip_html(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def fold(text: str) -> str:
    """Kleinschreibung plus Umlaut-Faltung: ä/ae -> a, ö/oe -> o, ü/ue -> u, ß/ss -> s.

    Dadurch matchen 'Fachkräfte', 'Fachkraefte' und 'FACHKRÄFTE' denselben Begriff.
    """
    t = text.lower()
    t = t.replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("ß", "s")
    t = re.sub(r"ae", "a", t)
    t = re.sub(r"oe", "o", t)
    t = re.sub(r"ue", "u", t)
    t = re.sub(r"ss", "s", t)
    return t


def term_regex(term: str) -> re.Pattern:
    """Wortgrenzen-Regex für einen gefalteten Begriff. Erlaubt deutsche Komposita-Endungen
    (z. B. 'Fachkräfte' trifft auch 'Fachkräftemangel')."""
    folded = re.escape(fold(term.strip()))
    folded = folded.replace(r"\ ", r"\s+")
    return re.compile(r"(?<![a-z0-9])" + folded + r"[a-z]{0,12}(?![a-z0-9])")


def canonical_url(url: str) -> str:
    """Tracking-Parameter und Fragmente entfernen, Host kleinschreiben."""
    if not url:
        return ""
    p = urllib.parse.urlsplit(url.strip())
    query = [
        (k, v)
        for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True)
        if not k.lower().startswith(TRACKING_PARAMS_PREFIX)
    ]
    host = p.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = p.path.rstrip("/") or "/"
    return urllib.parse.urlunsplit((p.scheme.lower() or "https", host, path, urllib.parse.urlencode(query), ""))


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        dt = None
    if dt is None:
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def age_bucket(first_seen: datetime | None, now: datetime) -> str:
    if first_seen is None:
        return "unbekannt"
    age = now - first_seen
    if age < timedelta(0):
        age = timedelta(0)
    for name, limit in AGE_BUCKETS:
        if age <= limit:
            return name
    return "alt"


# ---------------------------------------------------------------- Laden

def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def default_feeds_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "feeds_de.json")


def select_feeds(profile: dict, catalog: dict) -> list[dict]:
    """Feeds aus profile.feed_ids, sonst alle Feeds der profile.lanes."""
    by_id = {f["id"]: f for f in catalog["feeds"]}
    wanted = profile.get("feed_ids") or []
    if wanted:
        missing = [w for w in wanted if w not in by_id]
        if missing:
            log(f"Warnung: unbekannte feed_ids im Profil: {', '.join(missing)}")
        return [by_id[w] for w in wanted if w in by_id]
    lanes = set(profile.get("lanes") or [])
    return [f for f in catalog["feeds"] if not lanes or f["lane"] in lanes]


def fetch_feed(feed: dict, fixture_dir: str | None) -> tuple[bytes | None, str | None]:
    """Feed-Bytes holen: aus Fixture-Datei oder per HTTP. Gibt (bytes, fehler)."""
    if fixture_dir:
        path = os.path.join(fixture_dir, f"{feed['id']}.xml")
        if not os.path.exists(path):
            return None, f"Fixture fehlt: {path}"
        with open(path, "rb") as fh:
            return fh.read(), None
    req = urllib.request.Request(feed["url"], headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read(), None
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        return None, f"URL-Fehler: {exc.reason}"
    except (TimeoutError, OSError, ValueError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


# ---------------------------------------------------------------- Parsen

def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(el: ET.Element, names: tuple[str, ...]) -> str | None:
    for child in el:
        if _local(child.tag) in names and (child.text or "").strip():
            return child.text.strip()
    return None


def _atom_link(el: ET.Element) -> str | None:
    fallback = None
    for child in el:
        if _local(child.tag) != "link":
            continue
        href = child.get("href")
        if not href:
            continue
        rel = child.get("rel", "alternate")
        if rel == "alternate":
            return href
        fallback = fallback or href
    return fallback


def parse_feed(raw: bytes, feed: dict) -> list[dict]:
    """RSS 2.0 und Atom in eine einheitliche Item-Liste bringen."""
    root = ET.fromstring(raw)
    items: list[dict] = []
    root_name = _local(root.tag)
    if root_name == "feed":  # Atom
        for entry in root:
            if _local(entry.tag) != "entry":
                continue
            items.append({
                "title": strip_html(_child_text(entry, ("title",))),
                "link": _atom_link(entry) or "",
                "published": parse_date(_child_text(entry, ("published", "updated", "issued"))),
                "summary": strip_html(_child_text(entry, ("summary", "content")))[:600],
                "feed_id": feed["id"],
                "feed_name": feed["name"],
                "lane": feed["lane"],
            })
    else:  # RSS 2.0 / RDF
        for item in root.iter():
            if _local(item.tag) != "item":
                continue
            items.append({
                "title": strip_html(_child_text(item, ("title",))),
                "link": (_child_text(item, ("link", "guid")) or "").strip(),
                "published": parse_date(_child_text(item, ("pubDate", "date", "published", "updated"))),
                "summary": strip_html(_child_text(item, ("description", "encoded", "summary")))[:600],
                "feed_id": feed["id"],
                "feed_name": feed["name"],
                "lane": feed["lane"],
            })
    return [i for i in items if i["title"]]


# ---------------------------------------------------------------- Clustern

def cluster_items(items: list[dict]) -> list[dict]:
    """Items nach kanonischer URL und nahezu gleichem Titel zusammenfassen."""
    clusters: list[dict] = []
    for item in sorted(items, key=lambda i: i["published"] or datetime.max.replace(tzinfo=timezone.utc)):
        url = canonical_url(item["link"])
        folded_title = fold(item["title"])
        target = None
        for c in clusters:
            if url and url in c["urls"]:
                target = c
                break
            if difflib.SequenceMatcher(None, folded_title, c["_folded"]).ratio() >= TITLE_SIM:
                target = c
                break
        if target is None:
            target = {
                "headline": item["title"],
                "_folded": folded_title,
                "urls": [],
                "sources": [],
                "lanes": [],
                "first_seen": item["published"],
                "summary": item["summary"],
                "titles": [],
            }
            clusters.append(target)
        if url and url not in target["urls"]:
            target["urls"].append(url)
        if item["feed_id"] not in target["sources"]:
            target["sources"].append(item["feed_id"])
        if item["lane"] not in target["lanes"]:
            target["lanes"].append(item["lane"])
        if item["title"] not in target["titles"]:
            target["titles"].append(item["title"])
        if item["published"] and (target["first_seen"] is None or item["published"] < target["first_seen"]):
            target["first_seen"] = item["published"]
            target["headline"] = item["title"]
        if len(item["summary"]) > len(target["summary"]):
            target["summary"] = item["summary"]
    for c in clusters:
        key = c["urls"][0] if c["urls"] else c["_folded"]
        c["cluster_id"] = hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
        c["source_count"] = len(c["sources"])
        del c["_folded"]
    return clusters


# ---------------------------------------------------------------- Bewerten

def find_hits(text: str, terms: list[str]) -> list[str]:
    folded = fold(text)
    return [t for t in terms if term_regex(t).search(folded)]


def score_cluster(c: dict, profile: dict, lane_weights: dict, now: datetime) -> dict:
    """Mechanischer Score 0–100 mit erklärten Komponenten."""
    text = " ".join([c["headline"], *c["titles"], c["summary"]])
    term_hits = find_hits(text, profile.get("search_terms", []))
    competitor_hits = find_hits(text, profile.get("competitors", []))
    headline_hits = find_hits(c["headline"], profile.get("search_terms", []))

    bucket = age_bucket(c["first_seen"], now)
    freshness = FRESHNESS_POINTS.get(bucket, 0)
    agreement = min(20, 8 * (c["source_count"] - 1)) if c["source_count"] > 1 else 0
    terms = min(25, 7 * len(term_hits) + 6 * len(headline_hits))
    if competitor_hits:
        terms = min(25, terms + 4)
    lane = max(lane_weights.get(l, 5) for l in c["lanes"]) if c["lanes"] else 5

    total = freshness + agreement + terms + lane
    return {
        "age_bucket": bucket,
        "term_hits": term_hits,
        "headline_hits": headline_hits,
        "competitor_hits": competitor_hits,
        "mechanical_score": total,
        "score_components": {
            "frische": freshness,
            "quellenuebereinstimmung": agreement,
            "begriffstreffer": terms,
            "lane": lane,
        },
    }


# Endungen, die aus einem Safety-Begriff ein harmloses Wort machen (kriegt, gewaltig, ...).
SAFETY_FALSE_FRIENDS = {"krieg": r"(?!t|en|st)", "gewalt": r"(?!ig)", "tote": r"(?!m)", "kriegs": r"(?!te)"}


def brand_safety_hit(c: dict) -> list[str]:
    """Harter Block bei Tragödien-Lexik in Schlagzeile oder Teaser."""
    folded = fold(" ".join([c["headline"], c["summary"]]))
    hits = []
    for term in BRAND_SAFETY_TERMS:
        guard = SAFETY_FALSE_FRIENDS.get(term, "")
        pattern = r"(?<![a-z])" + re.escape(fold(term)) + guard + r"[a-z]{0,10}(?![a-z])"
        if re.search(pattern, folded):
            hits.append(term)
    return hits


def exclusion_hit(c: dict, profile: dict) -> list[str]:
    text = " ".join([c["headline"], *c["titles"], c["summary"]])
    return find_hits(text, profile.get("exclusions", []))


# ---------------------------------------------------------------- Seen-State

def load_seen(out_dir: str) -> dict:
    path = os.path.join(out_dir, "seen.json")
    if os.path.exists(path):
        return load_json(path)
    return {}


def save_seen(out_dir: str, seen: dict) -> None:
    with open(os.path.join(out_dir, "seen.json"), "w", encoding="utf-8") as fh:
        json.dump(seen, fh, ensure_ascii=False, indent=1, sort_keys=True)


# ---------------------------------------------------------------- Ausgabe

def serial(c: dict) -> dict:
    out = dict(c)
    if isinstance(out.get("first_seen"), datetime):
        out["first_seen"] = out["first_seen"].isoformat()
    return out


def write_run_md(path: str, meta: dict, candidates: list[dict], blocked: list[dict], rejected: list[dict], errors: list[dict]) -> None:
    lines = [
        f"# Detector-Lauf {meta['run_at']}",
        "",
        f"Profil: **{meta['profile']}**  ·  Feeds: {meta['feeds_ok']}/{meta['feeds_total']} ok  ·  "
        f"Items: {meta['items']}  ·  Cluster: {meta['clusters']}  ·  neu/gewachsen: {len(candidates)}",
        "",
        "## Kandidaten (mechanisch sortiert, noch ohne Standing-Urteil)",
        "",
    ]
    if candidates:
        lines += ["| # | Score | Alter | Quellen | Treffer | Schlagzeile |", "|---|---|---|---|---|---|"]
        for i, c in enumerate(candidates[:25], 1):
            hits = ", ".join(c["term_hits"][:4]) or "–"
            if c["competitor_hits"]:
                hits += " · Wettbewerb: " + ", ".join(c["competitor_hits"])
            lines.append(f"| {i} | {c['mechanical_score']} | {c['age_bucket']} | {c['source_count']} | {hits} | [{c['headline']}]({c['urls'][0] if c['urls'] else ''}) |")
    else:
        lines.append("Keine neuen Kandidaten in diesem Lauf.")
    lines += ["", "## Brand-Safety-Blocks (nie pitchen)", ""]
    lines += [f"- {b['headline']} (Begriffe: {', '.join(b['brand_safety_terms'])})" for b in blocked] or ["keine"]
    lines += ["", "## Verworfen", ""]
    lines += [f"- {r['headline']} · Grund: {r['reject_reason']}" for r in rejected[:30]] or ["keine"]
    if len(rejected) > 30:
        lines.append(f"- … und {len(rejected) - 30} weitere (siehe candidates.json)")
    lines += ["", "## Feed-Fehler", ""]
    lines += [f"- {e['feed_id']}: {e['error']}" for e in errors] or ["keine"]
    lines += ["", "Nächster Schritt: Standing-Triage und Story-Origin-Check durch den Agenten (siehe SKILL.md)."]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------- Befehle

def cmd_run(args: argparse.Namespace) -> int:
    now = now_from_arg(args.now)
    profile = load_json(args.profile)
    problems = validate_profile(profile)
    if problems:
        for p in problems:
            log(f"Profilfehler: {p}")
        return 2
    catalog = load_json(args.feeds or default_feeds_path())
    lane_weights = {k: v.get("gewicht", DEFAULT_LANE_WEIGHTS.get(k, 5)) for k, v in catalog.get("lanes", {}).items()} or DEFAULT_LANE_WEIGHTS
    feeds = select_feeds(profile, catalog)
    os.makedirs(args.out, exist_ok=True)
    seen = load_seen(args.out)

    items: list[dict] = []
    errors: list[dict] = []
    for feed in feeds:
        raw, err = fetch_feed(feed, args.fixture_dir)
        if err:
            errors.append({"feed_id": feed["id"], "error": err, "verify": bool(feed.get("verify"))})
            continue
        try:
            items.extend(parse_feed(raw, feed))
        except ET.ParseError as exc:
            errors.append({"feed_id": feed["id"], "error": f"XML-Fehler: {exc}", "verify": bool(feed.get("verify"))})

    clusters = cluster_items(items)
    min_age_ok = {"30min", "4h", "24h", "woche"}
    candidates, rejected, blocked = [], [], []
    for c in clusters:
        safety = brand_safety_hit(c)
        if safety:
            blocked.append({**serial(c), "brand_safety_terms": safety})
            continue
        excl = exclusion_hit(c, profile)
        scored = {**serial(c), **score_cluster(c, profile, lane_weights, now)}
        if excl:
            rejected.append({**scored, "reject_reason": "Ausschlussbegriff: " + ", ".join(excl)})
            continue
        if not scored["term_hits"] and not scored["competitor_hits"]:
            rejected.append({**scored, "reject_reason": "kein Profilbegriff getroffen"})
            continue
        if scored["age_bucket"] not in min_age_ok:
            rejected.append({**scored, "reject_reason": f"zu alt ({scored['age_bucket']})"})
            continue
        prev = seen.get(c["cluster_id"])
        if prev and prev.get("source_count", 0) >= c["source_count"]:
            rejected.append({**scored, "reject_reason": "bereits gesehen, nicht gewachsen"})
            continue
        scored["new_or_grown"] = "gewachsen" if prev else "neu"
        candidates.append(scored)

    candidates.sort(key=lambda c: (-c["mechanical_score"], c["first_seen"] or ""))
    for i, c in enumerate(candidates, 1):
        c["queue_priority"] = i

    for c in clusters:
        seen[c["cluster_id"]] = {"source_count": c["source_count"], "last_seen": now.isoformat(), "headline": c["headline"]}
    save_seen(args.out, seen)

    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    run_dir = os.path.join(args.out, stamp)
    os.makedirs(run_dir, exist_ok=True)
    meta = {
        "run_at": now.isoformat(),
        "profile": profile.get("company", os.path.basename(args.profile)),
        "profile_path": os.path.abspath(args.profile),
        "feeds_total": len(feeds),
        "feeds_ok": len(feeds) - len(errors),
        "items": len(items),
        "clusters": len(clusters),
        "fixture_dir": args.fixture_dir,
        "schema_version": "0.1.0",
    }
    payload = {
        "run_meta": meta,
        "candidates": candidates,
        "rejected": rejected,
        "brand_safety_blocks": blocked,
        "feed_errors": errors,
    }
    with open(os.path.join(run_dir, "candidates.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
    write_run_md(os.path.join(run_dir, "run.md"), meta, candidates, blocked, rejected, errors)
    log(f"Lauf geschrieben: {run_dir} ({len(candidates)} Kandidaten, {len(blocked)} geblockt, {len(rejected)} verworfen, {len(errors)} Feed-Fehler)")
    print(run_dir)
    return 0


def cmd_feeds(args: argparse.Namespace) -> int:
    catalog = load_json(args.feeds or default_feeds_path())
    if not args.check:
        for f in catalog["feeds"]:
            flag = " (verify)" if f.get("verify") else ""
            print(f"{f['id']:<22} {f['lane']:<20} {f['url']}{flag}")
        return 0
    bad = 0
    for f in catalog["feeds"]:
        raw, err = fetch_feed(f, None)
        status = "ok"
        if err:
            status = f"FEHLER {err}"
            bad += 1
        else:
            try:
                n = len(parse_feed(raw, f))
                status = f"ok, {n} Items"
            except ET.ParseError as exc:
                status = f"FEHLER XML: {exc}"
                bad += 1
        flag = " [verify]" if f.get("verify") else ""
        print(f"{f['id']:<22} {status}{flag}")
    return 1 if bad else 0


REQUIRED_PROFILE_FIELDS = {
    "company": str, "search_terms": list, "lanes": list, "timezone": str,
}
RECOMMENDED_PROFILE_FIELDS = ["competitors", "exclusions", "spokespeople", "proof_assets", "standing", "feed_ids", "topics"]


def validate_profile(profile: dict) -> list[str]:
    problems = []
    for key, typ in REQUIRED_PROFILE_FIELDS.items():
        if key not in profile:
            problems.append(f"Pflichtfeld fehlt: {key}")
        elif not isinstance(profile[key], typ):
            problems.append(f"Feld {key} hat falschen Typ, erwartet {typ.__name__}")
    terms = profile.get("search_terms") or []
    if isinstance(terms, list) and not (8 <= len(terms) <= 40):
        problems.append(f"search_terms: {len(terms)} Begriffe, empfohlen 10–20 (hart: 8–40)")
    return problems


def cmd_profile(args: argparse.Namespace) -> int:
    profile = load_json(args.validate)
    problems = validate_profile(profile)
    warnings = [f"empfohlenes Feld fehlt oder leer: {k}" for k in RECOMMENDED_PROFILE_FIELDS if not profile.get(k)]
    for sp in profile.get("spokespeople", []):
        if isinstance(sp, dict) and sp.get("status") == "prüfen":
            warnings.append(f"Sprecher:in '{sp.get('name')}' ist als 'prüfen' markiert")
    for p in problems:
        print(f"FEHLER  {p}")
    for w in warnings:
        print(f"HINWEIS {w}")
    if not problems:
        print(f"OK      Profil '{profile.get('company')}' ist gültig ({len(profile.get('search_terms', []))} Suchbegriffe, {len(profile.get('feed_ids', []))} Feeds)")
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Feeds einlesen und Kandidaten schreiben")
    run.add_argument("--profile", required=True)
    run.add_argument("--feeds", help="Pfad zu feeds_de.json (Standard: neben dem Skript)")
    run.add_argument("--fixture-dir", help="Lokale <feed_id>.xml statt HTTP")
    run.add_argument("--out", default="runs", help="Ausgabeordner (enthält seen.json)")
    run.add_argument("--now", help="Referenzzeit ISO 8601, für Tests")
    run.set_defaults(func=cmd_run)

    feeds = sub.add_parser("feeds", help="Katalog anzeigen oder prüfen")
    feeds.add_argument("--feeds")
    feeds.add_argument("--check", action="store_true", help="Jeden Feed abrufen und parsen")
    feeds.set_defaults(func=cmd_feeds)

    prof = sub.add_parser("profile", help="Kundenprofil validieren")
    prof.add_argument("--validate", required=True, metavar="PROFILE")
    prof.set_defaults(func=cmd_profile)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

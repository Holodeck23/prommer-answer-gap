#!/usr/bin/env python3
"""Deterministic grounding gate.

Every number and every proper noun in a draft item must appear verbatim in the frozen
corpus, or the item is HELD. Stdlib only.

Draft format: JSON list of items, each {"id": str, "text": str, ...}. Only "text" is checked.
Corpus: a directory of .txt/.md/.html/.json files (or a single file).

    python3 grounding_gate.py --corpus runs/corpus --draft runs/draft.json [--out runs/gate.json]
    python3 grounding_gate.py --corpus runs/corpus --draft runs/draft.json --negative-control

Exit code: 0 if every item passed, 1 if anything was held, 2 on a negative-control failure.
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

NUMBER = re.compile(r"(?<![\w.])\d[\d,.]*%?")
# Proper-noun run: two or more capitalised words, or one capitalised word not at sentence start.
PROPER_RUN = re.compile(r"\b[A-Z][a-zA-Z0-9&'-]+(?:\s+[A-Z][a-zA-Z0-9&'-]+)+")
SINGLE_CAP = re.compile(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-z]{2,}[a-zA-Z0-9]*\b")
STOP = {"The", "This", "That", "These", "Those", "A", "An", "It", "Its", "We", "Our", "You",
        "Your", "If", "When", "And", "But", "Or", "For", "In", "On", "At", "To", "Of", "With",
        "Add", "Use", "Make", "Get", "Set", "FAQ", "FAQs", "JSON", "HTML", "URL", "AI", "SEO"}


def load_corpus(path: Path) -> str:
    files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
    text = []
    for f in files:
        raw = f.read_text(encoding="utf-8", errors="ignore")
        if f.suffix in {".html", ".htm"}:
            raw = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", " ", raw)
            raw = html.unescape(re.sub(r"<[^>]+>", " ", raw))
        text.append(raw)
    return normalise(" ".join(text))


def normalise(s: str) -> str:
    s = s.replace(" ", " ").replace("’", "'").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", s)


def claims(text: str) -> dict:
    text = normalise(text)
    nums = {n.rstrip(".,") for n in NUMBER.findall(text) if n.rstrip(".,")}
    nouns = set(PROPER_RUN.findall(text))
    for w in SINGLE_CAP.findall(text):
        if w not in STOP and not any(w in run for run in nouns):
            nouns.add(w)
    nouns = {n for n in nouns if n.split()[0] not in STOP or len(n.split()) > 1}
    return {"numbers": sorted(nums), "proper_nouns": sorted(nouns)}


def check(item: dict, corpus: str) -> dict:
    c = claims(item.get("text", ""))
    missing = [x for x in c["numbers"] + c["proper_nouns"] if x not in corpus]
    return {"id": item.get("id"), "status": "HOLD" if missing else "PASS",
            "missing": missing, "checked": c}


def run(corpus: str, items: list) -> list:
    return [check(i, corpus) for i in items]


def negative_control(corpus: str, items: list) -> int:
    base = items[0]["text"] if items else "This page explains the service."
    planted = [
        {"id": "neg-stat", "text": base + " Pages with this markup see 4.3x more citations."},
        {"id": "neg-expert", "text": base + " According to Dr Helena Marquardt, this doubles visibility."},
    ]
    results = run(corpus, planted)
    for r in results:
        print(f"{r['id']}: {r['status']}  missing={r['missing']}")
    if all(r["status"] == "HOLD" for r in results):
        print("NEGATIVE CONTROL PASSED: both planted claims were held.")
        return 0
    print("NEGATIVE CONTROL FAILED: a planted claim got through. Do not submit until fixed.")
    return 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, type=Path)
    ap.add_argument("--draft", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--negative-control", action="store_true")
    a = ap.parse_args()
    corpus = load_corpus(a.corpus)
    items = json.loads(a.draft.read_text(encoding="utf-8"))
    if not isinstance(items, list):
        raise SystemExit("draft must be a JSON list of {id, text} items")
    if a.negative_control:
        return negative_control(corpus, items)
    results = run(corpus, items)
    for r in results:
        print(f"{r['id']}: {r['status']}" + (f"  missing={r['missing']}" if r["missing"] else ""))
    held = sum(r["status"] == "HOLD" for r in results)
    print(f"{len(results) - held} passed, {held} held")
    if a.out:
        a.out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    return 1 if held else 0


if __name__ == "__main__":
    sys.exit(main())

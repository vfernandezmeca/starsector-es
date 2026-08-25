#!/usr/bin/env python3
"""Deriva que campos son traducibles comparando el mod PT-BR contra los archivos originales."""
import csv, json, sys, os, io
csv.field_size_limit(10**9)

G = "/home/victor/Games/starsector"
D = "/home/victor/Downloads/PTBR 154 0.0.7 2026-06-21T14-52Z yvgMZtERg/portugues-brasileiro"

def rows(p):
    with open(p, encoding="utf-8", errors="replace", newline="") as f:
        return list(csv.reader(f))

def csv_cols(rel):
    a, b = rows(os.path.join(G, rel)), rows(os.path.join(D, rel))
    if not a or not b: return None
    hdr = a[0]
    if len(a) != len(b): return ("ROWCOUNT_DIFF", len(a), len(b), hdr)
    changed = {}
    for ra, rb in zip(a[1:], b[1:]):
        for i in range(min(len(ra), len(rb))):
            if ra[i] != rb[i]:
                changed[i] = changed.get(i, 0) + 1
    return [(hdr[i] if i < len(hdr) else f"col{i}", n) for i, n in sorted(changed.items())]

targets = []
for root, _, files in os.walk(D):
    for fn in files:
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, D)
        if rel in ("README.md", "mod_info.json"): continue
        if os.path.exists(os.path.join(G, rel)):
            targets.append(rel)

print("=== CSV: columnas traducidas ===")
for rel in sorted(t for t in targets if t.endswith(".csv")):
    print(f"{rel}: {csv_cols(rel)}")

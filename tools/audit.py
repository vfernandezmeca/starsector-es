#!/usr/bin/env python3
"""Audita el mod construido contra los originales: invariantes de estructura.

La prueba de ida y vuelta con traduccion identidad no basta: no introduce
caracteres nuevos. Esto compara el mod REAL contra el juego y verifica que la
traduccion no haya alterado nada estructural.
"""
import csv, json, os, re, sys
csv.field_size_limit(10**9)
G = "/home/victor/Games/starsector"
M = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "dist", "Starsector Espanol")
JSON_EXT = (".json", ".faction", ".variant", ".skill")
prob = []


def enc(rel):
    return "utf-8" if rel.endswith(JSON_EXT) else "cp1252"


for root, _, files in os.walk(M):
    for fn in files:
        rel = os.path.relpath(os.path.join(root, fn), M).replace(os.sep, "/")
        src = os.path.join(G, rel)
        if not os.path.exists(src):
            continue
        a = open(src, encoding=enc(rel), errors="replace", newline="").read()
        b = open(os.path.join(M, rel), encoding=enc(rel), errors="replace", newline="").read()
        if rel.endswith(".csv"):
            ra = list(csv.reader(a.splitlines(True)))
            rb = list(csv.reader(b.splitlines(True)))
            if len(ra) != len(rb):
                prob.append(f"{rel}: filas {len(ra)} -> {len(rb)}")
                continue
            for i, (x, y) in enumerate(zip(ra, rb)):
                if len(x) != len(y):
                    prob.append(f"{rel} fila {i}: columnas {len(x)} -> {len(y)}")
                    break
        elif rel.endswith(JSON_EXT):
            for ch in "{}[]":
                if a.count(ch) != b.count(ch):
                    prob.append(f"{rel}: '{ch}' {a.count(ch)} -> {b.count(ch)}")
            if re.sub(r'"(?:[^"\\]|\\.)*"', '', b).count('"'):
                prob.append(f"{rel}: comilla sin cerrar o sin escapar")
        elif rel.endswith(".java"):
            # una comilla escapada (\") sigue siendo el caracter '"': contarlas
            # en bruto da falsos positivos. La prueba buena es que, al quitar
            # los literales BIEN formados, no quede ninguna suelta.
            if re.sub(r'"(?:[^"\\]|\\.)*"', '', b).count('"'):
                prob.append(f"{rel}: comilla sin cerrar o sin escapar")
            # un ';' o '{' DENTRO de una cadena es inofensivo: comparar solo
            # la estructura, con los literales y comentarios fuera
            def desnudo(t):
                t = re.sub(r'"(?:[^"\\]|\\.)*"', '""', t)
                t = re.sub(r'//[^\n]*', '', t)
                return re.sub(r'/\*.*?\*/', '', t, flags=re.S)
            na, nb = desnudo(a), desnudo(b)
            for ch in "{}();":
                if na.count(ch) != nb.count(ch):
                    prob.append(f"{rel}: '{ch}' descuadrado fuera de cadenas")
                    break

# rules.csv: una opcion por linea, formato "id:texto"
r = "data/campaign/rules.csv"
ra = list(csv.reader(open(os.path.join(G, r), encoding="cp1252", newline="")))
rb = list(csv.reader(open(os.path.join(M, r), encoding="cp1252", newline="")))
oi = ra[0].index("options")
for i, (x, y) in enumerate(zip(ra[1:], rb[1:]), 1):
    if oi >= len(x) or oi >= len(y):
        continue
    la, lb = x[oi].split("\n"), y[oi].split("\n")
    if len(la) != len(lb):
        prob.append(f"rules.csv fila {i}: {len(la)} -> {len(lb)} opciones")
    for p, q in zip(la, lb):
        if ":" not in p:
            continue
        if ":" not in q:
            prob.append(f"rules.csv fila {i}: opcion sin ':'")
            continue
        # el prefijo es "id:" o "prioridad:id:". Si se altera, el juego no
        # encuentra la regla: "no rule found for option N", y el id acaba
        # visible para el jugador.
        n = 2 if re.match(r"^\s*\d+:", p) else 1
        if ":".join(p.split(":")[:n]) != ":".join(q.split(":")[:n]):
            prob.append(f"rules.csv fila {i}: prefijo de opcion alterado")

# los valores de enumeracion (MAYUSCULAS) no pueden cambiar nunca
ENUM = re.compile(r'"(\w+)"\s*:\s*"([A-Z][A-Z0-9_]*)"')
for root, _, files in os.walk(M):
    for fn in files:
        if not fn.endswith(JSON_EXT):
            continue
        rel = os.path.relpath(os.path.join(root, fn), M).replace(os.sep, "/")
        src = os.path.join(G, rel)
        if not os.path.exists(src):
            continue
        a = dict(ENUM.findall(open(src, encoding="utf-8", errors="replace").read()))
        b = dict(ENUM.findall(open(os.path.join(M, rel), encoding="utf-8",
                                   errors="replace").read()))
        for k, v in a.items():
            if k in b and b[k] != v:
                prob.append(f"{rel}: enum [{k}] {v} -> {b[k]}")

if prob:
    print(f"{len(prob)} PROBLEMAS:")
    for x in prob[:25]:
        print("  " + x)
else:
    print("sin problemas estructurales")

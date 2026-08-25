#!/usr/bin/env python3
"""Barrido exhaustivo: busca texto visible del juego que NO estemos traduciendo.

No usa las listas del proyecto (CSV_COLS, JSON_KEYS). Ese es el punto: los dos
huecos que aparecieron (los botones "Continue"/"Leave" y los 219 textos de
strings.json) se colaron porque el contador se construia sobre esas mismas
listas, y una lista incompleta siempre se da la razon a si misma.

Aqui se recorre TODO data/, se saca cualquier cadena con pinta de prosa, y se
comprueba si esta en el catalogo.
"""
import csv, json, os, re, sys, collections
csv.field_size_limit(10**9)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import batch as B
G = "/home/victor/Games/starsector"

# --- que cuenta como texto visible -------------------------------------
IDENT = re.compile(r'^[\w./\\:-]+$')                 # id, ruta, clave
ENUM = re.compile(r'^[A-Z][A-Z0-9_]*$')
LISTA_IDS = re.compile(r'^[\w-]+(\s*,\s*[\w-]+)+$')  # "tag1, tag2, tag3"
NUM = re.compile(r'^[\d\s.,%+/-]+$')


def es_prosa(v):
    v = v.strip()
    if len(v) < 6 or IDENT.match(v) or ENUM.match(v) or NUM.match(v):
        return False
    if LISTA_IDS.match(v):
        return False
    palabras = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", v)
    if len(palabras) < 2:
        return False
    # descartar listas de identificadores camelCase/snake_case
    raros = sum(1 for w in palabras if re.search(r"[a-z][A-Z]|_", w))
    return raros < len(palabras) / 2


def cadenas_de(rel):
    """Toda cadena con pinta de prosa dentro de un archivo del juego."""
    p = os.path.join(G, rel)
    enc = "utf-8" if rel.endswith((".json", ".faction", ".variant", ".skill")) else "cp1252"
    try:
        txt = open(p, encoding=enc, errors="replace", newline="").read()
    except Exception:
        return
    if rel.endswith(".csv"):
        try:
            filas = list(csv.reader(txt.splitlines(True)))
        except Exception:
            return
        if not filas:
            return
        hdr = filas[0]
        for fila in filas[1:]:
            for i, v in enumerate(fila):
                if es_prosa(v):
                    yield (hdr[i] if i < len(hdr) else "col%d" % i), v
    elif rel.endswith((".json", ".faction", ".variant", ".skill")):
        for m in re.finditer(r'"(\w+)"\s*:\s*"((?:[^"\\]|\\.)*)"', txt):
            if es_prosa(m.group(2)):
                yield m.group(1), m.group(2)
    elif rel.endswith(".txt"):
        if es_prosa(txt):
            yield "archivo", txt
    elif rel.endswith(".java"):
        for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', txt):
            if es_prosa(m.group(1)):
                yield "literal", m.group(1)


def main():
    cat = B.load_catalog()
    conocidas = {e["s"].strip() for e in cat}
    # tambien las opciones, que en el catalogo van sin su prefijo
    falta = collections.defaultdict(lambda: collections.defaultdict(list))
    for root, _, files in os.walk(os.path.join(G, "data")):
        for fn in files:
            rel = os.path.relpath(os.path.join(root, fn), G).replace(os.sep, "/")
            if not rel.endswith((".csv", ".json", ".faction", ".variant",
                                 ".skill", ".txt", ".java")):
                continue
            for campo, v in cadenas_de(rel):
                vv = v.strip()
                if vv in conocidas:
                    continue
                # las opciones se guardan sin el prefijo "id:" o "prio:id:"
                if ":" in vv:
                    n = 2 if re.match(r"^\s*\d+:", vv) else 1
                    resto = ":".join(vv.split(":")[n:]).strip()
                    if resto and resto in conocidas:
                        continue
                falta[rel][campo].append(vv)

    if not falta:
        print("sin huecos: todo el texto visible esta en el catalogo")
        return
    filas = []
    for rel, campos in falta.items():
        for campo, vs in campos.items():
            filas.append((sum(len(x) for x in vs), len(vs), rel, campo, vs[0]))
    filas.sort(reverse=True)
    tot = sum(f[0] for f in filas)
    print("POSIBLES HUECOS: %d chars en %d combinaciones archivo/campo\n" % (tot, len(filas)))
    print("%9s %6s  %s" % ("chars", "n", "archivo / campo"))
    for ch, n, rel, campo, ej in filas[:30]:
        print("%9d %6d  %s [%s]" % (ch, n, rel, campo))
        print("%18s%s" % ("", ej[:95].replace("\n", " ")))


if __name__ == "__main__":
    main()

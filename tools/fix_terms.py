#!/usr/bin/env python3
"""Armoniza terminologia en los lotes ya traducidos.

Agentes distintos traducen a ciegas unos de otros, asi que el mismo termino
acaba con dos formas. En vez de relanzar el lote, se reemplaza el termino
divergente por la forma canonica del glosario.

Solo terminos inequivocos y con limite de palabra. Ejecuta primero sin
--apply para ver que tocaria.
"""
import os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "work", "out")

# variante divergente -> forma canonica
CANON = [
    (r"\barquicurad[oa]s?\b", "archicura"),
    (r"\barcicuras?\b", "archicura"),
    (r"\bsubcurad[oa]s?\b", "subcura"),
    (r"\bmagistrado de la Liga\b", "demarconte"),
    # solo en minuscula cuando NO es el titulo "Primer Demarconte"
    (r"(?<!Primer )\bDemarconte\b", "demarconte"),
    (r"\bcriop[aá]scula", "criocápsula"),
    (r"\bmanufactura\b", "fabricación"),
    (r"\bterran\b", "terrano"),
    # Gargoyle es un alias, va sin traducir (10 casos frente a 2)
    (r"\bG\u00e1rgola\b", "Gargoyle"),
    (r"\bgente del espacio\b", "espacial"),
    (r"\bse\u00f1or/a de la guerra\b", "se\u00f1or de la guerra"),
    # "demarca" como titulo (no el verbo demarcar/demarcado)
    (r"\bdemarca\b", "demarconte"),
    (r"\b[Aa]rchicurador[ae]s?\b", "archicura"),
    (r"\bRemolcador(?:es)? de Portal\b", "Transportador del Portal"),
    # "shunt" es derivacion de energia, no transmision
    (r"\bhipertransmisor(?:es)?\b", "hiperderivaci\u00f3n"),
    # "Burn bright": despedida ludica. Dos formas segun registro, no cuatro.
    (r"Que ardas con fuerza", "Que arda tu luz"),
    (r"Que arda intensa su luz", "Que arda su luz"),
]


def main():
    apply = "--apply" in sys.argv
    if not os.path.isdir(OUT):
        sys.exit("work/out/ no existe")
    hits = collections.Counter()
    ex = collections.defaultdict(list)
    for fn in sorted(f for f in os.listdir(OUT) if f.endswith(".txt")):
        p = os.path.join(OUT, fn)
        s = open(p, encoding="utf-8").read()
        orig = s
        for pat, canon in CANON:
            def sub(m):
                hits[f"{m.group(0)} -> {canon}"] += 1
                if len(ex[canon]) < 2:
                    ex[canon].append(fn)
                return canon
            s = re.sub(pat, sub, s)
        if apply and s != orig:
            open(p, "w", encoding="utf-8").write(s)
    if not hits:
        print("nada que armonizar")
        return
    for k, n in hits.most_common():
        print(f"{n:5d}  {k}")
    print("\n(sin --apply no se ha escrito nada)" if not apply else "\naplicado")


if __name__ == "__main__":
    main()

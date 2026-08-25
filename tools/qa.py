#!/usr/bin/env python3
"""Control de calidad de la traduccion: caza calcos, Title Case ingles,
terminos del glosario sin aplicar y palabras inventadas tipicas.

No rechaza nada (de eso ya se encarga batch.py collect). Solo informa, para
decidir si una tanda vale o hay que relanzarla con el glosario retocado.
"""
import os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import batch

# calcos del ingles: patron -> como deberia decirse
CALCOS = [
    (r"\bresultando en\b", "lo que + verbo"),
    (r"\bpuede[ns]? ser (?:\w+d[oa]s?)\b", "pasiva refleja con 'se'"),
    (r"\bmuy lejos (?:por )?debajo\b", "muy por debajo"),
    (r"\befectividad de combate\b", "eficacia en combate"),
    (r"\bterran\b", "terrestre / terrano"),
    (r"\ben orden de\b", "para"),
    (r"\badicionalmente\b", "ademas"),
    (r"\bsignificantemente\b", "notablemente"),
    (r"\bes capaz de producir\b", "produce"),
    (r"\basalto de tierra\b", "asalto terrestre"),
    (r"\bprovee\b", "proporciona"),
    (r"\bcomputadora\b", "ordenador"),
    (r"\bcarro\b", "coche"),
    (r"\bremover\b", "quitar"),
    (r"\bencriptar\b", "cifrar"),
    (r"\bmanufactura\b", "fabricacion"),
    (r"\bcriopascul", "criocapsula"),
]
# terminos que NO deben quedar en ingles
SIN_TRADUCIR = [r"\bflux\b", r"\bhullmod\b", r"\bHegemony\b", r"\bsupplies\b",
                r"\bfuel\b", r"\bcrew\b", r"\bshield\b", r"\barmor\b",
                r"\bordnance\b", r"\bslipstream\b", r"\bbounty\b"]


# nombres propios: van en mayuscula con razon, no son Title Case ingles
PROPIOS = {"Hegemonia", "Hegemonía", "Hegemon", "Hegemón", "Tri-Tachyon",
    "Liga", "Perseana", "Iglesia", "Ludica", "Lúdica", "Senda", "Ludd",
    "Diktat", "Sindriano", "Caballeros", "Academia", "Galatia", "Dominio",
    "Sector", "Remanente", "Remanentes", "Portal", "Puerto", "Franco",
    "Independiente", "Nucleo", "Núcleo", "Alfa", "Beta", "Gamma"}


def title_case(v):
    if len(v) > 60 or len(v.split()) < 3:
        return False
    ws = [w for w in v.split() if len(w) > 3 and w.strip(",.;:-") not in PROPIOS]
    return len(ws) >= 2 and sum(1 for w in ws if w[0].isupper()) >= 2


def main():
    outdir = os.path.join(ROOT, "work", "out")
    files = sorted(f for f in os.listdir(outdir) if f.endswith(".txt"))
    if not files:
        sys.exit("work/out/ vacio")
    hits = collections.Counter()
    ex = collections.defaultdict(list)
    total = 0
    for fn in files:
        for k, v in batch.parse(os.path.join(outdir, fn)).items():
            total += 1
            for pat, fix in CALCOS:
                if re.search(pat, v, re.I):
                    hits[f"calco: {fix}"] += 1
                    if len(ex[fix]) < 2:
                        ex[fix].append((fn, v[:110]))
            for pat in SIN_TRADUCIR:
                if re.search(pat, v):
                    t = f"sin traducir: {pat.strip(chr(92)+'b')}"
                    hits[t] += 1
                    if len(ex[t]) < 2:
                        ex[t].append((fn, v[:110]))
            if title_case(v):
                hits["Title Case ingles"] += 1
                if len(ex["tc"]) < 4:
                    ex["tc"].append((fn, v[:110]))
    print(f"{len(files)} lotes, {total} strings revisados\n")
    if not hits:
        print("sin incidencias")
        return
    for k, n in hits.most_common():
        print(f"{n:5d}  {k}")
    print("\nejemplos:")
    for key, lst in list(ex.items())[:8]:
        for fn, v in lst:
            print(f"  [{key}] {fn}: {v}")


if __name__ == "__main__":
    main()

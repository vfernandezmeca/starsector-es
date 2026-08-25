#!/usr/bin/env python3
"""Compara modelos locales sobre el MISMO texto, con Sonnet como referencia.

El lote 001 ya está traducido por Sonnet (0 fallos), así que sirve de vara de
medir en vez de opinar. Mide lo que importa de verdad:
  - fallos mecánicos (tokens, saltos de línea, vacíos)
  - Title Case inglés, que es el punto flaco de los modelos locales
  - calcos del inglés
  - velocidad

Uso:  python3 tools/bench.py gemma3:27b gemma4:26b
"""
import os, re, sys, time, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import local as L, batch as B

CALCOS = [r"\bresultando en\b", r"\bpuede[ns]? ser \w+d[oa]s?\b",
          r"\bmuy lejos (?:por )?debajo\b", r"\befectividad de combate\b",
          r"\bterran\b", r"\ben orden de\b", r"\badicionalmente\b",
          r"\bes capaz de\b", r"\bmanufactura\b", r"\bprovee\b"]
PROPIOS = {"Hegemonía", "Hegemón", "Tri-Tachyon", "Liga", "Perseana", "Senda",
           "Lúdica", "Iglesia", "Ludd", "Diktat", "Sindriano", "Academia",
           "Galatia", "Dominio", "Sector", "Remanente", "Portal", "Núcleo",
           "Alfa", "Beta", "Gamma", "Omega", "Abismo", "Confín", "Caballeros"}


def title_case(v):
    if len(v) > 60 or len(v.split()) < 3:
        return False
    ws = [w for w in v.split() if len(w) > 3 and w.strip(",.;:-\"'") not in PROPIOS]
    return len(ws) >= 2 and sum(1 for w in ws if w[0].isupper()) >= 2


def muestra():
    orig = B.parse(os.path.join(ROOT, "work", "batches", "001.txt"))
    ks = list(orig)
    sel = ([k for k in ks if len(orig[k]) < 60][:14]
         + [k for k in ks if 60 <= len(orig[k]) < 200][:12]
         + [k for k in ks if len(orig[k]) >= 200][:10])
    return {k: orig[k] for k in sel}


def evalua(nombre, m, res, malos, dt):
    chars = sum(len(v) for v in m.values())
    tc = sum(1 for v in res.values() if title_case(v))
    ca = sum(1 for v in res.values()
             for p in CALCOS if re.search(p, v, re.I))
    print(f"\n{'='*54}\n{nombre}\n{'='*54}")
    print(f"  bloques          {len(res)}/{len(m)}")
    print(f"  fallos mecánicos {len(malos)}")
    print(f"  Title Case       {tc}")
    print(f"  calcos           {ca}")
    print(f"  velocidad        {chars/dt:.0f} chars/s  ({dt:.0f}s)")
    return {"fallos": len(malos), "tc": tc, "calcos": ca, "vel": chars/dt}


def main():
    modelos = sys.argv[1:] or ["gemma3:27b"]
    m = muestra()
    son = B.parse(os.path.join(ROOT, "work", "out", "001.txt"))
    print(f"muestra: {len(m)} bloques, {sum(len(v) for v in m.values())} chars")
    print(f"referencia Sonnet: Title Case={sum(1 for k in m if k in son and title_case(son[k]))}"
          f"  calcos={sum(1 for k in m if k in son for p in CALCOS if re.search(p, son[k], re.I))}")
    todo = {}
    for mod in modelos:
        t0 = time.time()
        res, malos = L.traduce_trozo(m, mod)
        todo[mod] = (res, evalua(mod, m, res, malos, time.time() - t0))
    # comparativa lado a lado
    print(f"\n{'='*54}\nMUESTRAS (S=Sonnet)\n{'='*54}")
    for k in list(m)[:8]:
        print("EN:", m[k].replace("\n", " ")[:120])
        for mod in modelos:
            print(f"{mod[:8]:>8}:", todo[mod][0].get(k, "-").replace("\n", " ")[:120])
        print("       S:", son.get(k, "-").replace("\n", " ")[:120], "\n")


if __name__ == "__main__":
    main()

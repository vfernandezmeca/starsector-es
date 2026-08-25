#!/usr/bin/env python3
"""Busca texto que se haya quedado en ingles dentro de la traduccion.

Tres senales, de mas fiable a menos:

1. IDENTICO al original y con forma de frase inglesa. Lo mas claro.
2. Mas palabras funcionales inglesas que espanolas ("the", "your", "with"
   frente a "el", "que", "con"). Caza bloques devueltos sin traducir.
3. Palabras inglesas sueltas dentro de texto espanol ("Leave", "Continue"),
   que es lo que se colaba por el filtro de extraccion.

Uso:
    python3 tools/ingles.py                 # informe
    python3 tools/ingles.py --pendiente     # ademas, los saca de hecho.jsonl
                                            # para retraducirlos
"""
import json, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import batch as B

EN = re.compile(r"\b(the|of|and|is|was|are|were|you|your|he|she|it|that|this"
                r"|with|for|have|has|been|will|would|there|their|they|what|when"
                r"|from|about|which|but|all|can|into|more|than|then|them|his|her"
                r"|him|our|who|how|any|some|other|only|just|its|now|out|over"
                r"|after|before|because|while|should|could|must|may)\b", re.I)
ES = re.compile(r"\b(el|la|los|las|de|que|y|en|un|una|es|se|no|por|con|para|su"
                r"|del|al|lo|como|más|mas|pero|sus|le|ya|este|esta|entre|cuando"
                r"|muy|sin|sobre|hasta|hay|donde|han|están|estan|desde|todo|nos"
                r"|todos|uno|les|ni|contra|otros|ese|eso|había|habia|ellos|esto"
                r"|antes|qué|que|unos|yo|otro|otra|él|esa|estos|mucho|nada"
                r"|muchos|ella|ser|estar|tiene|puede|hacer|si|te|me)\b", re.I)
# palabras inglesas frecuentes en interfaz que no deben quedar sueltas
# OJO: aqui NO pueden ir palabras que tambien existan en espanol. "No" hacia
# el 99,6% de los falsos positivos; tampoco valen "OK", "Total", "General".
SUELTAS = re.compile(r"\b(Leave|Continue|Accept|Decline|Cancel|Back|Next|Done"
                     r"|Close|Confirm|Yes|Exit|Retry|Skip|Buy|Sell|Trade"
                     r"|Repair|Refit|Depart|Undock|Attack|Defend|Retreat"
                     r"|Search|Salvage|Board|Loot|Hail|Disengage|Withdraw)\b")
# forma de frase inglesa: articulo/preposicion + palabra
FRASE_EN = re.compile(r"\b(the|your|a|an|of the|to the|in the)\s+\w+", re.I)


def analiza():
    cat = {e["k"]: e for e in B.load_catalog()}
    p = os.path.join(ROOT, "work", "trans.jsonl")
    marcados = collections.defaultdict(list)
    for l in open(p, encoding="utf-8"):
        d = json.loads(l)
        k, v = d["k"], d["es"]
        e = cat.get(k)
        if not e:
            continue
        s = e["s"]
        if len(v.strip()) < 2:
            continue
        # 1) identico al original y con pinta de ingles
        if v.strip() == s.strip() and len(s) > 3 and FRASE_EN.search(s):
            marcados["identico al original"].append((k, s, v)); continue
        # 2) mas ingles que espanol
        ne, nes = len(EN.findall(v)), len(ES.findall(v))
        if len(v) >= 40 and ne >= 3 and ne > nes:
            marcados["mayoritariamente ingles"].append((k, s, v)); continue
        # 3) palabra inglesa de interfaz suelta
        m = SUELTAS.search(v)
        if m and not SUELTAS.search("".join(ES.findall(v))):
            # solo si esa palabra tambien estaba en el original
            if re.search(r"\b%s\b" % m.group(0), s, re.I):
                marcados["palabra inglesa suelta"].append((k, s, v))
    return cat, marcados


def main():
    cat, marcados = analiza()
    total = sum(len(v) for v in marcados.values())
    print("posible ingles residual: %d bloques\n" % total)
    for tipo, ls in marcados.items():
        print("%5d  %s" % (len(ls), tipo))
    print()
    for tipo, ls in marcados.items():
        for k, s, v in ls[:4]:
            print("  [%s]\n    EN: %s\n    ES: %s" % (tipo, s[:80].replace("\n", " "),
                                                      v[:80].replace("\n", " ")))
    if "--pendiente" in sys.argv and total:
        malos = {k for ls in marcados.values() for k, _, _ in ls}
        hp = os.path.join(ROOT, "work", "hecho.jsonl")
        origen = hp if os.path.exists(hp) else os.path.join(ROOT, "work", "trans.jsonl")
        filas = [json.loads(l) for l in open(origen, encoding="utf-8")]
        with open(hp, "w", encoding="utf-8") as f:
            for d in filas:
                if d["k"] not in malos:
                    f.write(json.dumps(d, ensure_ascii=False) + "\n")
        print("\n%d sacados de hecho.jsonl. Ahora:" % total)
        print("  python3 tools/batch.py make && python3 tools/local.py --faltan")


if __name__ == "__main__":
    main()

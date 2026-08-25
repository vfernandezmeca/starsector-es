#!/usr/bin/env python3
"""Reparte catalog.jsonl en lotes de texto plano para los subagentes, y
recoge/valida la salida.

Formato de lote (sin JSON: cero escapado, cero forma de romperlo):

    ###ID a1b2c3d4e5f6
    texto origen, puede
    ocupar varias lineas
    ###ID 998877665544
    otro texto
    ###END

El agente devuelve el mismo formato con el texto ya en español.
"""
import json, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work")
BATCH_CHARS = 60000          # por lote -> ~1 subagente
MARK = "###ID "
END = "###END"

TOKEN = re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*")
# ordenes del motor de reglas, no texto: "set player.x = true", "id:$token"
RULE_CMD = re.compile(r"^(?:set\s+)?[\w.]+\s*(?:=|\+\+|--)|^\w+:\$\w+$")
# tokens que aporta el propio mod (EspanolTokens.java) para la concordancia
# de genero; el traductor puede anadirlos aunque no esten en el original
EXTRA_OK = {"$unUna", "$UnUna", "$elLa", "$ElLa", "$oA",
            "$playerUnUna", "$PlayerUnUna", "$playerElLa", "$playerOA"}

# Tokens puramente gramaticales: pronombres y posesivos. El español elide el
# sujeto ("dice", no "él dice") y a menudo el posesivo, asi que el traductor
# puede QUITARLOS. Nunca añadir mas de los que habia.
# Los tokens de contenido ($playerName, $market, $faction...) siguen siendo
# obligatorios: si falta uno, la frase pierde informacion.
ELIDIBLE = re.compile(
    r"^\$\w*?(?:[Hh]eOrShe|[Hh]isOrHer|[Hh]imOrHer|[Hh]imOrHerself"
    r"|[Bb]rotherOrSister|[Mm]anOrWoman|[Ss]irOrMadam"
    r"|[Ii]tOrThem|[Tt]heyOrIt|[Ii]sOrAre)$")


# El modelo interpreta los "$token" como formulas LaTeX y las destroza
# ("Sindriano" -> "Sindri $\\text{ano}$"). Tambien se come los %s.
LATEX = re.compile(r"\\text\{|\\[(\[]|\$\\")
FORMATO = re.compile(r"%[sdf]")


def formato_ok(src, es):
    """Los marcadores %s/%d deben conservarse exactamente."""
    return sorted(FORMATO.findall(src)) == sorted(FORMATO.findall(es))


def token_ok(src, es):
    """True si los tokens de la traduccion son validos respecto al original."""
    import collections as _c
    a = _c.Counter(TOKEN.findall(src))
    b = _c.Counter(t for t in TOKEN.findall(es) if t not in EXTRA_OK)
    for t in set(a) | set(b):
        if b[t] > a[t]:
            return False            # nunca inventar tokens
        if b[t] < a[t] and not ELIDIBLE.match(t):
            return False            # solo se pueden elidir pronombres
    return True


def load_catalog():
    return [json.loads(l) for l in open(os.path.join(WORK, "catalog.jsonl"), encoding="utf-8")]


# que es cada cadena, en cristiano, para que el traductor acierte el registro
ETIQUETAS = {
    "data/campaign/rules.csv#text":
        "narracion o dialogo de un PNJ (el jugador LEE esto)",
    "data/campaign/rules.csv#options":
        "opcion que ELIGE EL JUGADOR: es lo que el jugador dice o hace",
    "data/campaign/abilities.csv#name": "nombre de habilidad de flota (etiqueta corta)",
    "data/campaign/abilities.csv#desc": "que hace una habilidad de flota",
    "data/campaign/commodities.csv#name": "nombre de mercancia",
    "data/campaign/industries.csv#name": "nombre de industria de colonia",
    "data/campaign/industries.csv#desc": "descripcion de industria de colonia",
    "data/campaign/market_conditions.csv#name": "condicion de un planeta o mercado",
    "data/campaign/market_conditions.csv#desc": "descripcion de esa condicion",
    "data/campaign/special_items.csv#name": "nombre de objeto especial",
    "data/campaign/special_items.csv#desc": "descripcion de objeto especial",
    "data/campaign/submarkets.csv#name": "nombre de submercado",
    "data/characters/personalities.csv#name": "caracter de un oficial",
    "data/characters/skills/skill_data.csv#name": "nombre de habilidad de personaje",
    "data/characters/skills/skill_data.csv#description": "efecto de una habilidad",
    "data/hullmods/hull_mods.csv#name": "nombre de mod de casco (etiqueta corta)",
    "data/hullmods/hull_mods.csv#desc": "efecto de un mod de casco",
    "data/hulls/ship_data.csv#name": "NOMBRE PROPIO de una nave (suele no traducirse)",
    "data/hulls/ship_data.csv#designation":
        "CLASE de nave, nombre comun: destructor, fragata, carguero...",
    "data/shipsystems/ship_systems.csv#name": "sistema de nave (etiqueta corta)",
    "data/strings/descriptions.csv#text1": "descripcion larga (codex)",
    "data/weapons/weapon_data.csv#name": "nombre de arma (etiqueta corta)",
    "data/weapons/weapon_data.csv#primaryRoleStr": "papel de un arma: antiescudo, antiblindaje...",
}


def etiqueta(e):
    """Contexto legible de una cadena, para el prompt del traductor."""
    base = ETIQUETAS.get(e["ctx"])
    if not base and e["ctx"].startswith("jar:"):
        base = "interfaz del juego: menu, boton o aviso en pantalla"
        # el motor concatena trozos: si el texto empieza o acaba en medio
        # de una frase, traducirlo como oracion completa suena raro al unirse
        t = e["s"]
        corta = t != t.strip() or (t[:1].islower() and not t.rstrip().endswith((".", "!", "?", ":")))
        if corta:
            base += " (FRAGMENTO: se pega a otro texto, no anadas mayuscula inicial ni punto final)"
    if not base:
        f, _, campo = e["ctx"].partition("#")
        f = f.split("/")[-1]
        if f.endswith(".variant"):
            base = "nombre de configuracion de nave (etiqueta corta)"
        elif f.endswith(".faction"):
            base = "faccion: nombre, rango o cargo"
        elif f.endswith(".txt"):
            base = "texto de mision o manual"
        else:
            base = f"{f} ({campo})"
    h = e.get("h")
    return f"{base} [regla: {h}]" if h else base


def cmd_make():
    cat = load_catalog()
    # work/hecho.jsonl guarda lo ya traducido por ID, asi que los lotes se
    # regeneran solo con lo que falta. Los ids son hash del texto: estables
    # aunque cambie el troceo, por eso no hace falta cuadrar nombres.
    p = os.path.join(WORK, "hecho.jsonl")
    if os.path.exists(p):
        hecho = {json.loads(l)["k"] for l in open(p, encoding="utf-8")}
        antes = len(cat)
        cat = [e for e in cat if e["k"] not in hecho]
        print(f"{antes - len(cat)} ya traducidos, {len(cat)} pendientes")
    # agrupar por contexto para que lo relacionado viaje junto
    cat.sort(key=lambda e: (e["ctx"], -len(e["s"])))
    outdir = os.path.join(WORK, "batches")
    os.makedirs(outdir, exist_ok=True)
    for f in os.listdir(outdir):
        os.remove(os.path.join(outdir, f))
    # La numeracion se recicla en cada regeneracion, asi que una respuesta
    # vieja en work/out haria que --faltan diese por hecho un lote nuevo.
    # Se archiva en vez de borrar: si no estaba consolidada, sigue ahi.
    vieja = os.path.join(WORK, "out")
    if os.path.isdir(vieja) and os.listdir(vieja):
        n = 1
        while os.path.exists(os.path.join(WORK, f"out.{n}")):
            n += 1
        os.rename(vieja, os.path.join(WORK, f"out.{n}"))
        print(f"respuestas anteriores archivadas en work/out.{n}")
    os.makedirs(vieja, exist_ok=True)
    n, size, cur = 0, 0, []

    def flush():
        nonlocal n, size, cur
        if not cur:
            return
        n += 1
        with open(os.path.join(outdir, f"{n:03d}.txt"), "w", encoding="utf-8") as f:
            f.write("".join(cur) + END + "\n")
        size, cur = 0, []

    for e in cat:
        s = e["s"].replace("\r\n", "\n")
        block = f"{MARK}{e['k']} | {etiqueta(e)}\n{s}\n"
        if size and size + len(block) > BATCH_CHARS:
            flush()
        cur.append(block)
        size += len(block)
    flush()
    print(f"{n} lotes en {outdir}")


def parse(path):
    """Lee un archivo en formato de lote -> {id: texto}."""
    out, cur, buf = {}, None, []
    for line in open(path, encoding="utf-8").read().split("\n"):
        if line.startswith(MARK):
            if cur:
                out[cur] = "\n".join(buf)
            # "###ID <id> | <contexto>": el id es el primer token
            cur, buf = line[len(MARK):].strip().split()[0], []
        elif line.strip() == END:
            if cur:
                out[cur] = "\n".join(buf)
            cur = None
        elif cur is not None:
            buf.append(line)
    if cur:
        out[cur] = "\n".join(buf)
    # el formato mete un \n final por bloque; quitarlo
    return {k: (v[:-1] if v.endswith("\n") else v) for k, v in out.items()}


def cmd_collect():
    """Une work/out/*.txt -> work/trans.jsonl, arreglando saltos de linea y
    validando integridad contra el original."""
    cat = {e["k"]: e for e in load_catalog()}
    outdir = os.path.join(WORK, "out")
    got, problems = {}, collections.Counter()
    detail = []
    for fn in sorted(os.listdir(outdir)) if os.path.isdir(outdir) else []:
        if not fn.endswith(".txt"):
            continue
        for k, es in parse(os.path.join(outdir, fn)).items():
            e = cat.get(k)
            if not e:
                problems["id_desconocido"] += 1
                continue
            src = e["s"]
            # Restaurar espacios y saltos de los extremos ANTES de validar: el
            # formato de lote ("###ID x\n<texto>\n") no distingue un salto
            # final del propio separador, asi que el modelo nunca lo devuelve.
            # Validar antes de restaurar tiraba 47 traducciones correctas.
            pre = src[: len(src) - len(src.lstrip())]
            post = src[len(src.rstrip()):]
            es = pre + es.strip() + post
            bad = None
            if not es.strip():
                bad = "vacia"
            elif LATEX.search(es):
                bad = "latex"
            elif not formato_ok(src, es):
                bad = "formato_%s"
            elif not token_ok(src, es):
                bad = "tokens"
            elif src.replace("\r\n", "\n").count("\n") != es.count("\n"):
                bad = "saltos_linea"
            elif len(src) < 25 and len(es) > len(src) * 3.0 + 12:
                # el español es de por si ~25% mas largo; solo cazar desbocados
                bad = "demasiado_larga"
            elif (es.strip() == src.strip() and len(src) > 25
                  and not RULE_CMD.match(src.strip())):
                bad = "sin_traducir"
            if bad:
                problems[bad] += 1
                if len(detail) < 12:
                    detail.append((bad, k, src[:70], es[:70]))
                continue
            # restaurar CRLF si el original lo usaba
            if "\r\n" in src:
                es = es.replace("\r\n", "\n").replace("\n", "\r\n")
            got[k] = es
    warn = [k for k, v in got.items()
            if len(v) < 60 and len(v.split()) > 2
            and sum(1 for w in v.split() if len(w) > 3 and w[0].isupper()) >= 2]
    p = os.path.join(WORK, "hecho.jsonl")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            d = json.loads(line)
            got.setdefault(d["k"], d["es"])
    with open(os.path.join(WORK, "trans.jsonl"), "w", encoding="utf-8") as f:
        for k, es in got.items():
            f.write(json.dumps({"k": k, "es": es}, ensure_ascii=False) + "\n")
    print(f"aceptadas={len(got)}  pendientes={len(cat)-len(got)}  rechazadas={sum(problems.values())}")
    if warn:
        print(f"aviso: {len(warn)} strings con posible Title Case ingles")
    if problems:
        print("problemas:", dict(problems))
        for b, k, s, e in detail:
            print(f"  [{b}] {k}\n    EN: {s}\n    ES: {e}")


def cmd_todo():
    """Lista los ids aun sin traducir, para reintentos."""
    cat = load_catalog()
    done = set()
    p = os.path.join(WORK, "trans.jsonl")
    if os.path.exists(p):
        done = {json.loads(l)["k"] for l in open(p, encoding="utf-8")}
    miss = [e for e in cat if e["k"] not in done]
    print(f"{len(miss)} pendientes de {len(cat)}")


if __name__ == "__main__":
    {"make": cmd_make, "collect": cmd_collect, "todo": cmd_todo}[sys.argv[1]]()

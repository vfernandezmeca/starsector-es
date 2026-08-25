#!/usr/bin/env python3
"""Extract/inject de strings traducibles de Starsector.

extract  -> work/catalog.jsonl  (un objeto por string unico + contexto)
inject   -> mod/  (copia de los originales con las traducciones aplicadas)

Encoding: los .csv/.txt/.java del juego se leen y escriben en cp1252 (asi los
guarda el juego y asi los espera su loader). Los .json/.faction/.variant/.skill
van en UTF-8.
"""
import csv, json, os, re, sys, hashlib, shutil

csv.field_size_limit(10**9)
GAME = "/home/victor/Games/starsector"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK, MOD = os.path.join(ROOT, "work"), os.path.join(ROOT, "mod")

# --- que se traduce -------------------------------------------------------
CSV_COLS = {
    "data/campaign/abilities.csv": ["name", "desc"],
    "data/campaign/commodities.csv": ["name"],
    "data/campaign/industries.csv": ["name", "desc"],
    "data/campaign/market_conditions.csv": ["name", "desc"],
    "data/campaign/rules.csv": ["text", "options", "script"],
    "data/campaign/reports.csv": ["subject", "summary", "assessment"],
    "data/campaign/special_items.csv": ["name", "desc", "tech/manufacturer"],
    "data/campaign/submarkets.csv": ["name", "desc"],
    "data/characters/personalities.csv": ["name", "desc"],
    "data/characters/skills/aptitude_data.csv": ["name", "description"],
    "data/characters/skills/skill_data.csv": ["name", "description", "author"],
    "data/hullmods/hull_mods.csv": ["name", "desc", "short", "sModDesc"],
    "data/hulls/ship_data.csv": ["name", "designation", "logistics n/a reason",
                                 "tech/manufacturer"],
    "data/hulls/wing_data.csv": ["role desc"],
    "data/shipsystems/ship_systems.csv": ["name"],
    "data/strings/descriptions.csv": ["text1", "text2", "text3", "text4", "text5"],
    "data/weapons/weapon_data.csv": ["name", "primaryRoleStr", "speedStr",
        "trackingStr", "accuracyStr", "customPrimary", "customPrimaryHL", "customAncillary",
        "tech/manufacturer"],
}
# claves "k": "valor" traducibles en archivos tipo JSON (json/faction/variant/skill)
JSON_KEYS = {
    "displayName", "displayNameWithArticle", "displayNameLong",
    "displayNameLongWithArticle", "description", "defaultName", "name",
    "title", "nameInText", "shortName", "body", "type", "shortType",
    "factionLeader", "spaceCommander", "patrolCommander", "fleetCommander",
    "baseCommander", "stationCommander", "administrator", "portmaster",
    "militaryAdministrator", "quartermaster", "spaceAdmiral", "genericMilitary",
    "houseLeader", "houseLeaderMale", "houseLeaderFemale", "guardLeader",
    "intelligenceDirector", "citizen", "executive", "seniorExecutive", "agent",
    "specialAgent", "unknown", "aristocrat", "terrorist", "approach",
    # nombres de flota por faccion (bloque fleetTypeNames de los .faction):
    # se ven en el mapa en cada flota
    "patrolSmall", "patrolMedium", "patrolLarge", "mercScout",
    "mercBountyHunter", "mercPrivateer", "mercPatrol", "mercArmada",
    "trade", "smallTrader", "tradeLiner", "tradeSmuggler", "taskForce",
    "inspectionFleet", "leagueEnforcer", "leagueArmada", "supplyFleet",
    "commerceRaiders", "raider", "raiderSmall", "raiderMedium", "raiderLarge",
    "battlestation", "carrierGroup", "scout", "exploration",
    # alcance de las habilidades, visible en su descripcion
    "scopeStr", "scopeStr2",
}
JSON_EXT = (".json", ".faction", ".variant", ".skill")
# En estos archivos TODO valor de texto es visible en pantalla, asi que no se
# filtra por clave: la lista blanca dejaba fuera 217 de 219 textos de
# strings.json (28.860 caracteres de dialogo de interfaz).
JSON_TODO = ("data/strings/strings.json", "data/strings/tips.json",
             "data/strings/tooltips.json",
             # nombres de flota que salen en el mapa: todo el archivo es texto
             "data/world/factions/default_fleet_type_names.json")
JSON_ANY = re.compile(r'("(\w+)"\s*:\s*)"((?:[^"\\]|\\.)*)"')
# Toda cadena entrecomillada, con lo que la sigue: sirve para distinguir
# clave ("x": ...) de valor, y pilla los elementos sueltos de un array,
# que en tips.json son la mayoria de los consejos.
JSON_CUALQUIERA = re.compile(r'"((?:[^"\\]|\\.)*)"\s*(.?)')


def json_cadenas(txt):
    """(campo, texto) de cada cadena traducible de un JSON completo.

    Descarta los nombres de clave: son los que llevan ':' detras.
    """
    out = []
    for m in JSON_CUALQUIERA.finditer(txt):
        if m.group(2) == ":":          # es un nombre de clave
            continue
        # si viene precedida de "clave": el campo es esa clave
        antes = txt[max(0, m.start() - 40):m.start()]
        clave = re.search(r'"(\w+)"\s*:\s*$', antes)
        out.append((clave.group(1) if clave else "item", m.group(1)))
    return out


def json_sub(txt, traduce):
    """Reescribe las cadenas traducibles de un JSON completo.

    traduce(texto) -> texto. Los nombres de clave quedan intactos.
    """
    def rep(m):
        if m.group(2) == ":":
            return m.group(0)
        es = traduce(m.group(1))
        if es == m.group(1):
            return m.group(0)
        return m.group(0).replace('"%s"' % m.group(1), '"%s"' % es, 1)
    return JSON_CUALQUIERA.sub(rep, txt)
# texto plano traducido entero
TXT_GLOBS = ("data/missions/", "data/codex/")

# No tocar identificadores, rutas, colores y numeros. OJO: el patron
# [\w./\\-]+ descartaba tambien cualquier PALABRA SUELTA ("Leave", "Continue"),
# que si hay que traducir. Ahora solo se descarta lo que parece codigo:
#   - contiene / \ _ o punto entre letras   (rutas, ids, claves)
#   - camelCase o TODO_MAYUSCULAS_CON_GUION
#   - colores #rrggbb y numeros
SKIP_RE = re.compile(
    r'^(?:'
    r'[\w.\-]*[/\\][\w./\\-]*'          # rutas
    r'|\w+_[\w_]+'                        # snake_case
    r'|[a-z]+[A-Z]\w*'                     # camelCase
    r'|[a-z]+\.[a-z][\w.]*'                # claves con punto
    r'|#[0-9a-fA-F]{3,8}'                  # colores
    r'|\d[\d.,%+-]*'                       # numeros
    r')$')


def enc_for(rel):
    return "utf-8" if rel.endswith(JSON_EXT) else "cp1252"


def read(rel, base=GAME):
    with open(os.path.join(base, rel), encoding=enc_for(rel), errors="replace",
              newline="") as f:
        return f.read()


def key(bucket, src):
    return hashlib.sha1(f"{bucket}\x00{src}".encode()).hexdigest()[:12]


# Valores de enumeracion: el juego los compara contra constantes fijas.
# Traducir "GLOW" a "RESPLANDOR" hace que no arranque:
#   Fatal: Key [type] has invalid value [RESPLANDOR]
# Van SIEMPRE en MAYUSCULAS y sin espacios, lo que los distingue del texto
# visible ("Intel", "News Report"), que si se traduce.
ENUM_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')


def translatable(v):
    v = v.strip()
    return (bool(v) and not SKIP_RE.match(v) and not ENUM_RE.match(v)
            and re.search(r"[A-Za-z]{2}", v))


# --- options: "optId:Texto visible" -> solo la parte tras el primer ':' ----
OPT_PRIO = re.compile(r"^\s*\d+:")

# La columna `script` es codigo del motor de reglas, pero lleva texto visible
# incrustado: AddText "...", SetTooltip "...". Son 722 cadenas y 51.000
# caracteres, entre ellos los dialogos de rescate de naves.
# Solo se tocan los argumentos entre comillas de estos comandos.
SCRIPT_CMDS = {
    "AddText", "AddTextSmall", "AddPara", "SetTooltip", "SetStoryOption",
    "AddBarEvent", "AddRaidObjective", "AddPopGrowth", "ApplyCRDamage",
    "MakeOtherFleetDoThing", "Highlight", "SetTextHighlights",
    "SetTooltipHighlights",
}
SCRIPT_LINEA = re.compile(r'^(\s*)(\w+)(\s+)(.*)$')
COMILLAS = re.compile(r'"((?:[^"\\]|\\.)*)"')


def script_partes(campo):
    """Rinde (linea_entera, texto) por cada argumento traducible del script."""
    for linea in campo.replace("\r\n", "\n").split("\n"):
        m = SCRIPT_LINEA.match(linea)
        if not m or m.group(2) not in SCRIPT_CMDS:
            continue
        for q in COMILLAS.findall(m.group(4)):
            if re.search(r"[A-Za-z]{3}\s+[A-Za-z]{3}", q):   # dos palabras minimo
                yield linea, q


def script_sub(campo, fn):
    """Reescribe el script aplicando fn a cada argumento traducible."""
    salida = []
    for linea in campo.split("\n"):
        m = SCRIPT_LINEA.match(linea.rstrip("\r"))
        if not m or m.group(2) not in SCRIPT_CMDS:
            salida.append(linea); continue
        def rep(q):
            t = q.group(1)
            if not re.search(r"[A-Za-z]{3}\s+[A-Za-z]{3}", t):
                return q.group(0)
            nuevo = fn(t)
            if nuevo == t:
                return q.group(0)      # sin cambios: devolver el original tal cual
            # el propio juego escapa las comillas internas como \" ; hacer
            # lo mismo. Sustituirlas por apostrofos alteraba scripts validos.
            nuevo = nuevo.replace("\\", "\\\\").replace('"', '\\"')
            return '"' + nuevo.replace("\n", " ") + '"'
        cr = "\r" if linea.endswith("\r") else ""
        salida.append(m.group(1) + m.group(2) + m.group(3)
                      + COMILLAS.sub(rep, m.group(4)) + cr)
    return "\n".join(salida)


def split_option(v):
    """Separa una opcion en (prefijo, texto visible).

    El motor admite DOS formatos, y confundirlos rompe el juego:
        id:Texto visible                 (7005 casos)
        prioridad:id:Texto visible       (494 casos)

    Partir siempre por el primer ':' mete el id dentro del texto: el juego no
    encuentra la regla ("no rule found for option N") y ademas el id acaba
    traducido y a la vista del jugador.
    """
    n = 2 if OPT_PRIO.match(v) else 1        # cuantos ':' son prefijo
    i = -1
    for _ in range(n):
        i = v.find(":", i + 1)
        if i < 0:
            return None, None
    return v[: i + 1], v[i + 1:]


def escapa(text):
    """Escapa comillas para meter texto en un literal de Java o de JSON.

    El traductor no sabe en que formato acabara su texto. Si escribe una
    comilla y se inserta cruda en "..." parte el archivo. Aqui si se sabe.
    """
    return text.replace("\\", "\\\\").replace('"', '\\"')


def safe_option(text):
    """Saneado del texto visible de una opcion.

    El motor parsea la columna `options` como "id:texto", una opcion por
    linea. Un ':' o un salto de linea de mas desplaza los campos y el juego
    revienta al arrancar con:
        Fatal: For input string: "<id de la opcion>"

    El español mete ':' de forma natural donde el ingles usa guion o coma
    ("One more thing- ..." -> "Una cosa mas: ..."), asi que esto no se puede
    dejar en manos del traductor: se sanea aqui, siempre.
    """
    return text.replace(":", " -").replace("\r", " ").replace("\n", " ")


def walk_targets():
    """Rinde (rel, kind) de todo lo traducible."""
    for rel in CSV_COLS:
        yield rel, "csv"
    for root, _, files in os.walk(os.path.join(GAME, "data")):
        for fn in files:
            rel = os.path.relpath(os.path.join(root, fn), GAME)
            if rel in CSV_COLS:
                continue
            if fn.endswith(JSON_EXT):
                yield rel, "json"
            elif fn.endswith(".txt") and any(rel.startswith(g) for g in TXT_GLOBS):
                yield rel, "txt"
            elif fn.endswith(".java"):
                yield rel, "java"


JAVA_STR = re.compile(r'"((?:[^"\\]|\\.)*)"')
JSON_PAIR = re.compile(r'("(' + "|".join(sorted(JSON_KEYS)) + r')"\s*:\s*)"((?:[^"\\]|\\.)*)"')


def scan(rel, kind, emit):
    """emit(bucket, src, pista) por cada string traducible.

    La pista es contexto que ayuda a traducir bien: en rules.csv, el id de la
    regla (delata faccion y situacion). No entra en el hash del id.
    """
    txt = read(rel)
    if kind == "csv":
        rows = list(csv.reader(txt.splitlines(True)))
        hdr = rows[0]
        idc = hdr.index("id") if "id" in hdr else None
        for col in CSV_COLS[rel]:
            if col not in hdr:
                continue
            i = hdr.index(col)
            for row in rows[1:]:
                if i >= len(row):
                    continue
                v = row[i]
                pista = row[idc].strip() if idc is not None and idc < len(row) else ""
                if col == "script":
                    for _, t in script_partes(v):
                        if translatable(t):
                            emit(f"{rel}#{col}", t, pista)
                elif col == "options":
                    for part in v.split("\n"):
                        _, t = split_option(part)
                        if t and translatable(t):
                            emit(f"{rel}#{col}", t, pista)
                elif translatable(v):
                    emit(f"{rel}#{col}", v, pista)
    elif kind == "json":
        if rel in JSON_TODO:
            # incluye las cadenas sueltas de array (los consejos de tips.json)
            for campo, valor in json_cadenas(txt):
                if translatable(valor):
                    emit(f"{rel}#{campo}", valor, "")
        else:
            for m in JSON_PAIR.finditer(txt):
                if translatable(m.group(3)):
                    emit(f"{rel}#{m.group(2)}", m.group(3), "")
    elif kind == "txt":
        if translatable(txt):
            emit(f"{rel}#file", txt, "")
    elif kind == "java":
        for m in JAVA_STR.finditer(txt):
            s = m.group(1)
            # solo frases: >=2 palabras o con espacio; descarta ids/rutas
            if translatable(s) and " " in s.strip():
                emit(f"{rel}#str", s, "")


def cmd_extract():
    os.makedirs(WORK, exist_ok=True)
    seen, out = {}, []
    def emit(bucket, src, pista=""):
        k = key(bucket, src)          # el hash NO incluye la pista: ids estables
        if k in seen:
            seen[k]["n"] += 1
            return
        e = {"k": k, "ctx": bucket, "h": pista, "n": 1, "s": src}
        seen[k] = e
        out.append(e)
    for rel, kind in walk_targets():
        scan(rel, kind, emit)
    p = os.path.join(WORK, "catalog.jsonl")
    with open(p, "w", encoding="utf-8") as f:
        for e in out:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    chars = sum(len(e["s"]) for e in out)
    print(f"{len(out)} strings unicos, {chars} chars -> {p}")


def load_trans():
    t = {}
    p = os.path.join(WORK, "trans.jsonl")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                d = json.loads(line)
                if d.get("es"):
                    t[d["k"]] = d["es"]
    return t


# Las fuentes del juego no pintan NINGUN caracter no-ASCII: los acentos, la
# ñ, los signos ¿ ¡ y la raya larga salen como apostrofes o basura. Con
# --sin-acentos se pasa todo a ASCII puro, que es lo unico que renderiza.
SIN_TILDE = {
    "á":"a","é":"e","í":"i","ó":"o","ú":"u","ü":"u","ñ":"n",
    "Á":"A","É":"E","Í":"I","Ó":"O","Ú":"U","Ü":"U","Ñ":"N",
    "à":"a","è":"e","ì":"i","ò":"o","ù":"u","â":"a","ê":"e","î":"i","ô":"o","û":"u",
    "¿":"", "¡":"",            # los signos de apertura no existen en ASCII
    "—":"-", "–":"-", "―":"-",  # rayas y guiones largos
    "«":'"', "»":'"', "“":'"', "”":'"', "„":'"',
    "‘":"'", "’":"'", "‚":"'",
    "…":"...", "•":"*", "·":"-", "°":" grados", "±":"+/-",
    "€":"cr", "×":"x", "÷":"/", "º":"o", "ª":"a",
}
SIN_TILDE = str.maketrans({k: v for k, v in SIN_TILDE.items()})


def a_ascii(t):
    """Deja el texto en ASCII puro. Lo que no tenga equivalente, se cae."""
    t = t.translate(SIN_TILDE)
    return "".join(c for c in t if ord(c) < 128)


def cmd_inject():
    T = load_trans()
    if "--sin-acentos" in sys.argv:
        T = {k: a_ascii(v) for k, v in T.items()}
        print("modo sin acentos: todo a ASCII puro (unico que renderiza el juego)")
    if not T:
        sys.exit("work/trans.jsonl vacio o inexistente")
    os.makedirs(MOD, exist_ok=True)
    hits = miss = 0
    for rel, kind in walk_targets():
        txt = read(rel)
        def tr(bucket, src, _pista=""):
            nonlocal hits, miss
            v = T.get(key(bucket, src))
            if v:
                hits += 1
                return v
            miss += 1
            return src
        if kind == "csv":
            rows = list(csv.reader(txt.splitlines(True)))
            hdr = rows[0]
            for col in CSV_COLS[rel]:
                if col not in hdr:
                    continue
                i = hdr.index(col)
                for row in rows[1:]:
                    if i >= len(row):
                        continue
                    v = row[i]
                    if col == "script":
                        row[i] = script_sub(v, lambda t: (
                            tr(f"{rel}#{col}", t) if translatable(t) else t))
                    elif col == "options":
                        parts = []
                        for part in v.split("\n"):
                            pre, t = split_option(part)
                            parts.append(pre + safe_option(tr(f"{rel}#{col}", t))
                                         if t and translatable(t) else part)
                        row[i] = "\n".join(parts)
                    elif translatable(v):
                        row[i] = tr(f"{rel}#{col}", v)
            buf = []
            w = csv.writer(_Sink(buf), lineterminator="\r\n")
            for row in rows:
                w.writerow(row)
            new = "".join(buf)
            # el CSV del juego no termina en salto de linea; csv.writer si
            if not txt.endswith(("\n", "\r")) and new.endswith("\r\n"):
                new = new[:-2]
        elif kind == "json":
            if rel in JSON_TODO:
                campos = dict((v, c) for c, v in json_cadenas(txt))
                new = json_sub(txt, lambda v: escapa(
                    tr(f"{rel}#{campos.get(v, 'item')}", v))
                    if translatable(v) else v)
            else:
                new = JSON_PAIR.sub(
                    lambda m: (m.group(1) + '"'
                               + escapa(tr(f"{rel}#{m.group(2)}", m.group(3))) + '"')
                    if translatable(m.group(3)) else m.group(0), txt)
        elif kind == "txt":
            new = tr(f"{rel}#file", txt) if translatable(txt) else txt
        elif kind == "java":
            new = JAVA_STR.sub(
                lambda m: '"' + escapa(tr(f"{rel}#str", m.group(1))) + '"'
                if translatable(m.group(1)) and " " in m.group(1).strip() else m.group(0), txt)
        dst = os.path.join(MOD, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding=enc_for(rel), errors="replace", newline="") as f:
            f.write(new)
    print(f"inject: {hits} aplicadas, {miss} sin traducir")


class _Sink:
    def __init__(self, buf): self.buf = buf
    def write(self, s): self.buf.append(s)


if __name__ == "__main__":
    {"extract": cmd_extract, "inject": cmd_inject}[sys.argv[1]]()

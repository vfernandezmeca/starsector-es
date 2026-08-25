"""Saca el texto visible de los jars del juego al catalogo de traduccion.

Los menus, botones y avisos del motor no salen de data/: son literales
dentro de las clases compiladas. Aqui se eligen cuales se pueden tocar.

Criterio: una cadena sin espacios es indistinguible de un identificador
(clave de memoria, id de spec, nombre de planeta), asi que solo entra si
esta en BOTONES. Con espacios se asume texto de pantalla.
"""
import csv
import hashlib
import json
import os
import re
import sys
import zipfile

import jarloc

JUEGO = os.environ.get("STARSECTOR", "/home/victor/Games/starsector")
WORK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "work")
JARS = ["starfarer_obf.jar", "starfarer.api.jar"]


def _virgen(nombre):
    """Ruta al jar sin parchear, que es de donde hay que extraer."""
    orig = os.path.join(JUEGO, nombre + ".orig")
    return orig if os.path.exists(orig) else os.path.join(JUEGO, nombre)

# Palabras sueltas que son botones y no claves. Ampliar solo tras verlas
# en pantalla: si una de estas resulta ser un id, la rompe en silencio.
BOTONES = {
    "Quit", "Back", "Continue", "Leave", "Cancel", "Confirm", "Accept",
    "Decline", "Close", "Done", "Next", "Previous", "Yes", "No", "Okay",
    "Missions", "Tutorials", "Codex", "Credits", "Settings", "Refit",
    "Dismiss", "Undo", "Redo", "Retreat", "Deploy", "Autofit", "Strip",
    "Confirmed", "Cancelled", "Victory", "Defeat", "Paused", "Loading",
}

MAL = re.compile(r"[{}]|\.(fnt|png|jpg|jpeg|csv|json|ogg|java|class|txt|xml)$")
# Una ruta lleva extension o va toda en minusculas ("data/hulls"). Con
# mayusculas y sin extension es una etiqueta: "Crew/Cargo".
RUTA = re.compile(r"^[a-z0-9_./\\-]+$|\.[A-Za-z0-9]{2,4}$")
GUION = re.compile(r"[-\d]")
# formas que delatan un identificador y no una etiqueta de pantalla
COMPUESTO = re.compile(r"[a-z][A-Z]|_|^[A-Z]{2,}[a-z]")   # ManagedFleetData, PLStatFuel
PUNTEADO = re.compile(r"[A-Za-z0-9]\.[A-Za-z0-9]")        # java.io.X, com.fs.Global
MAYUSCULA = re.compile(r"^[A-Z0-9_]+$")                   # MISSILE, GLOW: constantes
SUFIJO = re.compile(r"^\.\w+$")                          # .inprogress, .bak, .variant
LICENCIA = re.compile(r"^[A-Z0-9]{4,6}(-[A-Z0-9]{4,6}){2,}$")
LETRAS = re.compile(r"[A-Za-z]{2}")
FRASE = re.compile(r"[.!?]\s*$")


def traducible(s, claves=frozenset()):
    """True si la cadena es texto que ve el jugador y se puede reescribir.

    claves: literales que el codigo compara o usa para buscar. Son
    identificadores aunque parezcan texto, y no se tocan.
    """
    t = s.strip()
    if len(t) < 3 or not LETRAS.search(t):
        return False
    if MAL.search(t) or LICENCIA.match(t) or SUFIJO.match(t):
        return False
    if ("/" in t or "\\" in t) and RUTA.match(t):
        return False
    if s in claves:
        return False
    if " " not in t:
        # una palabra: es etiqueta de pantalla salvo que tenga forma de
        # identificador. Cuales sirven de clave lo dice el bytecode, no
        # la forma, asi que aqui solo se filtra lo que nunca es texto.
        if t in BOTONES:
            return True
        return not (COMPUESTO.search(t) or PUNTEADO.search(t)
                    or MAYUSCULA.match(t) or GUION.search(t))
    return True


def entrada(jar, clase, s):
    """Fila de catalogo. El id es hash del texto: repetido = una traduccion."""
    return {
        "k": hashlib.sha1(("jar|" + s).encode("utf-8")).hexdigest()[:12],
        "ctx": f"jar:{jar}#{clase}",
        "n": 1,
        "s": s,
    }


CLAVE_JSON = re.compile(r'"(\w[\w.]*)"\s*:')
DATOS_JSON = (".json", ".proj", ".wpn", ".ship", ".variant", ".system",
              ".faction", ".skin", ".sound", ".hullstyles")


def claves_de_datos(raiz):
    """Nombres de clave JSON y de columna CSV usados en los datos del juego.

    El codigo los busca por texto exacto: traducir 'behavior' o 'specClass'
    hace que el campo deje de encontrarse y la spec salga a null.
    """
    claves = set()
    for base, _, files in os.walk(raiz):
        for f in files:
            ruta = os.path.join(base, f)
            ext = os.path.splitext(f)[1].lower()
            try:
                if ext == ".csv":
                    with open(ruta, encoding="cp1252", errors="replace") as fh:
                        cabecera = fh.readline()
                    claves |= {c.strip().strip('"') for c in cabecera.split(",")}
                elif ext in DATOS_JSON:
                    with open(ruta, encoding="utf-8", errors="replace") as fh:
                        claves |= set(CLAVE_JSON.findall(fh.read()))
            except Exception:
                continue
    return {c for c in claves if c}


def trozos_de_ruta(raiz):
    """Nombres de carpeta y de archivo del arbol de recursos.

    El cargador monta rutas concatenando trozos sueltos ("proj"), asi que
    cualquiera de estos nombres puede estar en el codigo como literal.
    """
    trozos = set()
    for base, dirs, files in os.walk(raiz):
        trozos |= set(dirs)
        for f in files:
            trozos.add(os.path.splitext(f)[0])
    return {t for t in trozos if t}


TROZO = re.compile(r"[_\-.]")
CARGA = re.compile(r"^com/fs/starfarer/loading/")


def extensiones(raiz):
    """Extensiones de los datos, con y sin punto.

    El cargador filtra por extension suelta ("skin"): traducirla hace que
    no encuentre ningun archivo de ese tipo.
    """
    out = set()
    for base, _, files in os.walk(raiz):
        for f in files:
            _, e = os.path.splitext(f)
            if e:
                out.add(e)
                out.add(e.lstrip("."))
    return out


def piezas_de_id(raiz, literales_de_carga):
    """Trozos de nombre de fichero que ademas aparecen en el codigo de carga.

    Se exigen las dos evidencias: solo con los nombres de fichero se
    perdian etiquetas de pantalla ("Assault", "Missile"), y solo con el
    codigo de carga se perdian botones ("Cancel", "Exit").
    """
    trozos = set()
    for base, _, files in os.walk(raiz):
        for f in files:
            trozos |= set(TROZO.split(os.path.splitext(f)[0]))
    return {t for t in trozos if t and t in literales_de_carga}


COL_ID = re.compile(r"(^|\s)id$", re.I)
PAQUETE_IDS = re.compile(r"/campaign/ids/[^/]+\.class$")


def valores_de_id(raiz):
    """Valores de las columnas de id de los CSV del juego.

    Son los ids reales de objetos, armas, cascos y condiciones. En el
    codigo aparecen como constantes sin ninguna llamada alrededor, asi
    que el bytecode no los delata.
    """
    out = set()
    for base, _, files in os.walk(raiz):
        for f in files:
            if not f.endswith(".csv"):
                continue
            try:
                with open(os.path.join(base, f), encoding="cp1252",
                          errors="replace") as fh:
                    lector = csv.DictReader(fh)
                    cols = [c for c in (lector.fieldnames or [])
                            if c and COL_ID.search(c.strip())]
                    if not cols:
                        continue
                    for fila in lector:
                        for c in cols:
                            v = (fila.get(c) or "").strip()
                            if v:
                                out.add(v)
            except Exception:
                continue
    return out


CACHE = "identificadores.txt"


def identificadores(recalcula=False):
    """Cadenas que el juego busca por texto exacto y no se pueden traducir.

    Tres fuentes, cada una anadida tras una rotura real:
      - el bytecode las compara o las pasa a un getter
      - son clave JSON o columna CSV en los datos
      - son un trozo de ruta que el cargador concatena
    """
    cache = os.path.join(WORK, CACHE)
    if not recalcula and os.path.exists(cache):
        with open(cache, encoding="utf-8") as f:
            return {l.rstrip("\n") for l in f if l.rstrip("\n")}
    out = set()
    for jar in JARS:
        z = zipfile.ZipFile(_virgen(jar))
        for i in z.infolist():
            if not i.filename.endswith(".class"):
                continue
            try:
                out |= {b.decode("utf-8", "ignore")
                        for b in jarloc.literales_comparados(z.read(i))}
            except Exception:
                continue
    de_carga = set()
    for jar in JARS:
        z = zipfile.ZipFile(_virgen(jar))
        for i in z.infolist():
            if i.filename.endswith(".class") and CARGA.match(i.filename):
                try:
                    de_carga |= {b.decode("utf-8", "ignore")
                                 for b in jarloc.literales(z.read(i))}
                except Exception:
                    continue
    datos = os.path.join(JUEGO, "data")
    out |= claves_de_datos(datos)
    out |= trozos_de_ruta(datos)
    out |= extensiones(datos)
    out |= piezas_de_id(datos, de_carga)
    out |= valores_de_id(datos)
    # el paquete ids/ es una lista de identificadores y nada mas
    for jar in JARS:
        z = zipfile.ZipFile(_virgen(jar))
        for i in z.infolist():
            if i.filename.endswith(".class") and PAQUETE_IDS.search(i.filename):
                try:
                    out |= {b.decode("utf-8", "ignore")
                            for b in jarloc.literales(z.read(i))}
                except Exception:
                    continue
    os.makedirs(WORK, exist_ok=True)
    with open(cache, "w", encoding="utf-8") as f:
        for s in sorted(out):
            if "\n" not in s:
                f.write(s + "\n")
    return out


def recoge():
    """Recorre los jars y devuelve las entradas de catalogo, sin repetir."""
    # Un identificador lo es en todo el juego, no solo donde se le ve
    # comparar: se registra en una clase y se consulta en otra.
    claves = identificadores(recalcula=True)
    print(f"{len(claves)} cadenas intocables (codigo, datos y rutas)")
    vistas = {}
    for jar in JARS:
        z = zipfile.ZipFile(_virgen(jar))
        for i in z.infolist():
            if not i.filename.endswith(".class"):
                continue
            try:
                lits = jarloc.literales(z.read(i))
            except Exception:
                continue
            for b in lits:
                try:
                    s = b.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                if not traducible(s, claves):
                    continue
                e = entrada(jar, i.filename, s)
                if e["k"] in vistas:
                    vistas[e["k"]]["n"] += 1
                else:
                    vistas[e["k"]] = e
    return list(vistas.values())


def main():
    nuevas = recoge()
    cat = os.path.join(WORK, "catalog.jsonl")
    previas = set()
    if os.path.exists(cat):
        previas = {json.loads(l)["k"] for l in open(cat, encoding="utf-8")}
    pendientes = [e for e in nuevas if e["k"] not in previas]
    with open(cat, "a", encoding="utf-8") as f:
        for e in pendientes:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    chars = sum(len(e["s"]) for e in pendientes)
    print(f"{len(nuevas)} cadenas en los jars, {len(pendientes)} nuevas al catalogo")
    print(f"{chars} caracteres a traducir")


if __name__ == "__main__":
    main()

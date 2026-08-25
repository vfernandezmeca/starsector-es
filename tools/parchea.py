"""Traduce los menus del juego reescribiendo literales dentro de los jars.

Un mod no puede hacerlo: sus clases van en un classloader hijo y los menus
ya estan cargados por el padre. Por eso esto es un parche, no un mod.

Siempre se parte de una copia .orig intacta, asi que se puede repetir sin
acumular danos y se puede revertir con --restaura.
"""
import json
import os
import shutil
import sys
import zipfile

import jar_extrae
import jarloc

JUEGO = os.environ.get("STARSECTOR", "/home/victor/Games/starsector")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(RAIZ, "work")
JARS = ["starfarer_obf.jar", "starfarer.api.jar"]

# Prueba de humo: el menu principal a mano, para comprobar que el juego
# arranca parcheado antes de traducir los 350 KB restantes.
MENU = {
    "New Game": "Partida nueva",
    "Load Game": "Cargar partida",
    "Continue": "Continuar",
    "Settings": "Ajustes",
    "Missions": "Misiones",
    "Tutorials": "Tutoriales",
    "Codex": "Codice",
    "Credits": "Creditos",
    "Quit": "Salir",
    "Back": "Atras",
    "Fleet Command": "Mando de flota",
    "Edit Variants": "Editar variantes",
    "Combat (Basic)": "Combate (basico)",
    "Combat (Advanced)": "Combate (avanzado)",
}


def copia(ruta):
    """Guarda el jar virgen la primera vez y devuelve su ruta."""
    orig = str(ruta) + ".orig"
    if not os.path.exists(orig):
        shutil.copy2(str(ruta), orig)
    return orig


def claves_del_propio_jar(ruta):
    """Identificadores deducidos solo del jar indicado, sin mirar el juego."""
    out = set()
    with zipfile.ZipFile(ruta) as z:
        for n in z.namelist():
            if n.endswith(".class"):
                try:
                    out |= jarloc.literales_comparados(z.read(n))
                except Exception:
                    continue
    return out


def parchea_jar(ruta, mapa, claves=None):
    """Reescribe los literales de mapa. Devuelve cuantas cadenas cambiaron.

    claves: cadenas intocables. Por defecto la lista del juego entero, que
    es global a proposito: un identificador se registra en una clase y se
    consulta en otra, y las dos tienen que seguir coincidiendo.
    """
    ruta = str(ruta)
    orig = copia(ruta)
    if claves is None:
        claves = {s.encode("utf-8") for s in jar_extrae.identificadores()}
    cambios = 0
    saltadas = []
    tmp = ruta + ".tmp"
    with zipfile.ZipFile(orig) as ent, zipfile.ZipFile(tmp, "w") as sal:
        for i in ent.infolist():
            d = ent.read(i)
            if i.filename.endswith(".class"):
                try:
                    presentes = jarloc.literales(d) & mapa.keys()
                    # Hay frases que el juego recorre caracter a caracter para
                    # derivar el serial. Parecen texto y no lo son: traducirlas
                    # invalida codigos de licencia legitimos.
                    if presentes and jarloc.es_material_de_clave(d, presentes):
                        saltadas.append(i.filename)
                        presentes = set()
                    # en esta clase, las que el codigo compara son claves
                    presentes -= claves
                    if presentes:
                        d = jarloc.reescribe(d, {k: mapa[k] for k in presentes})
                        cambios += len(presentes)
                except Exception as e:
                    print(f"  aviso: {i.filename} sin tocar ({e})", file=sys.stderr)
                    d = ent.read(i)
            info = zipfile.ZipInfo(i.filename, date_time=i.date_time)
            info.compress_type = i.compress_type
            info.external_attr = i.external_attr
            sal.writestr(info, d)
    os.replace(tmp, ruta)
    for f in saltadas:
        print(f"  intacta (material de clave): {f}")
    return cambios


def restaura():
    for j in JARS:
        r = os.path.join(JUEGO, j)
        if os.path.exists(r + ".orig"):
            shutil.copy2(r + ".orig", r)
            print("restaurado", j)
        else:
            print("sin copia de", j)


MAPA = "mapa_jar.json"


def mapa_desde_trabajo():
    """{ingles: espanol} de las cadenas de jar ya traducidas.

    Si existe work/mapa_jar.json se usa tal cual: es lo que se distribuye,
    para no tener que repartir el catalogo entero ni las herramientas de
    extraccion. Si no, se construye desde catalogo + traducciones y se
    deja escrito.
    """
    listo = os.path.join(WORK, MAPA)
    if os.path.exists(listo):
        with open(listo, encoding="utf-8") as f:
            return {k.encode("utf-8"): v.encode("utf-8")
                    for k, v in json.load(f).items()}
    from ssloc import a_ascii
    cat = {}
    with open(os.path.join(WORK, "catalog.jsonl"), encoding="utf-8") as f:
        for l in f:
            e = json.loads(l)
            if e["ctx"].startswith("jar:"):
                cat[e["k"]] = e["s"]
    mapa = {}
    with open(os.path.join(WORK, "trans.jsonl"), encoding="utf-8") as f:
        for l in f:
            t = json.loads(l)
            src = cat.get(t["k"])
            if src and t["es"] and t["es"] != src:
                mapa[src] = a_ascii(t["es"])
    with open(listo, "w", encoding="utf-8") as f:
        json.dump(mapa, f, ensure_ascii=False, indent=0, sort_keys=True)
    return {k.encode("utf-8"): v.encode("utf-8") for k, v in mapa.items()}


def main():
    if "--restaura" in sys.argv:
        return restaura()
    if "--menu" in sys.argv:
        mapa = {k.encode("utf-8"): v.encode("utf-8") for k, v in MENU.items()}
    else:
        mapa = mapa_desde_trabajo()
    print(f"{len(mapa)} cadenas traducidas para los jars")
    for j in JARS:
        r = os.path.join(JUEGO, j)
        n = parchea_jar(r, mapa)
        print(f"  {j}: {n} literales reescritos")
    print("\nrevertir:  python3 tools/parchea.py --restaura")


if __name__ == "__main__":
    main()

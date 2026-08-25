"""Invariantes del jar parcheado. Cada una viene de una rotura real.

Se ejecuta despues de parchear y antes de dar nada por bueno:
    python3 tools/verifica_jar.py
"""
import os
import re
import sys
import zipfile

import jarloc

JUEGO = os.environ.get("STARSECTOR", "/home/victor/Games/starsector")
JARS = ["starfarer_obf.jar", "starfarer.api.jar"]
ELEM = re.compile(r"<([A-Za-z][\w.$-]*)[ />]")
MAYUS = re.compile(rb"^[A-Z0-9_]{2,}$")
REGEX = re.compile(rb"^\(\?[a-zA-Z]*[):]")


def pares():
    for j in JARS:
        o = os.path.join(JUEGO, j + ".orig")
        p = os.path.join(JUEGO, j)
        if os.path.exists(o):
            yield j, zipfile.ZipFile(o), zipfile.ZipFile(p)


def clases_parsean():
    """Ninguna clase puede quedar corrupta tras reescribir el pool."""
    malas = []
    for j, _, z in pares():
        for n in z.namelist():
            if not n.endswith(".class"):
                continue
            try:
                jarloc.literales(z.read(n))
            except Exception as e:
                malas.append(f"{j}:{n} ({e})")
    return malas


def constantes_intactas():
    """Nombres de enum y constantes en mayusculas: el juego los busca con
    valueOf desde los datos, traducirlos revienta el combate."""
    malas = []
    for j, z0, z1 in pares():
        for n in z1.namelist():
            if not n.endswith(".class"):
                continue
            try:
                a, b = jarloc.literales(z0.read(n)), jarloc.literales(z1.read(n))
            except Exception:
                continue
            for s in a - b:
                if MAYUS.match(s):
                    malas.append(f"{j}:{n} {s.decode('utf8', 'ignore')}")
    return malas


def alias_de_guardado():
    """Los nombres de elemento de las partidas existentes tienen que seguir
    registrados, o XStream no puede resolver la clase al cargar."""
    saves = os.path.join(JUEGO, "saves")
    if not os.path.isdir(saves):
        return []
    elems = set()
    for d in os.listdir(saves):
        f = os.path.join(saves, d, "campaign.xml")
        if os.path.exists(f):
            with open(f, encoding="utf-8", errors="replace") as fh:
                elems |= set(ELEM.findall(fh.read(6_000_000)))
    malas = []
    for j, z0, z1 in pares():
        for n in z1.namelist():
            if not n.endswith(".class"):
                continue
            try:
                d0 = z0.read(n)
                ident = jarloc.literales_comparados(d0)
                a, b = jarloc.literales(d0), jarloc.literales(z1.read(n))
            except Exception:
                continue
            for s in (a - b) & ident:
                if s.decode("utf-8", "ignore") in elems:
                    malas.append(f"{j}:{n} {s.decode('utf8', 'ignore')}")
    return malas


def material_de_clave_intacto():
    """Ninguna cadena que el codigo recorra caracter a caracter puede haber
    cambiado: asi es como el juego deriva el numero de serie."""
    malas = []
    for j, z0, z1 in pares():
        for n in z1.namelist():
            if not n.endswith(".class"):
                continue
            try:
                d0 = z0.read(n)
                cambiadas = jarloc.literales(d0) - jarloc.literales(z1.read(n))
                if cambiadas and jarloc.es_material_de_clave(d0, cambiadas):
                    malas.append(f"{j}:{n}")
            except Exception:
                continue
    return malas


def identificadores_sin_tocar():
    """Ninguna cadena de la lista de intocables puede haber cambiado:
    codigo que la compara, clave de los datos o trozo de ruta."""
    import jar_extrae
    claves = {s.encode("utf-8") for s in jar_extrae.identificadores()}
    malas = []
    for j, z0, z1 in pares():
        for n in z1.namelist():
            if not n.endswith(".class"):
                continue
            try:
                cambiadas = jarloc.literales(z0.read(n)) - jarloc.literales(z1.read(n))
            except Exception:
                continue
            for s in cambiadas & claves:
                malas.append(f"{j}:{n} {s.decode('utf8', 'ignore')}")
    return malas


def regex_intactos():
    """Un literal que empieza por (?i) o (?is) no es texto, es una expresion
    regular. `util/Oo0O` las pasa a String.replaceAll para abreviar nombres de
    arma que no caben. Si la traduccion se come el modificador, el juego peta
    al entrar en combate: 'Unknown inline modifier near index 3'."""
    malas = []
    for j, z0, z1 in pares():
        for n in z1.namelist():
            if not n.endswith(".class"):
                continue
            try:
                d0, d1 = z0.read(n), z1.read(n)
                u0 = jarloc._analiza(d0)[0]
                u1 = jarloc._analiza(d1)[0]
            except Exception:
                continue
            for i, tramo in u0.items():
                antes = d0[slice(*tramo)]
                if not antes.startswith(b"(?") or i not in u1:
                    continue
                despues = d1[slice(*u1[i])]
                a, b = REGEX.match(antes), REGEX.match(despues)
                if a and (b is None or a.group() != b.group()):
                    malas.append("%s:%s %s -> %s" % (
                        j, n, antes.decode("utf8", "ignore"),
                        despues.decode("utf8", "ignore")))
    return malas


COMPROBACIONES = [
    ("clases sin corromper", clases_parsean),
    ("constantes y enums intactos", constantes_intactas),
    ("alias de las partidas guardadas", alias_de_guardado),
    ("identificadores sin traducir", identificadores_sin_tocar),
    ("material de clave sin tocar", material_de_clave_intacto),
    ("expresiones regulares intactas", regex_intactos),
]


def main():
    fallos = 0
    for nombre, fn in COMPROBACIONES:
        malas = fn()
        fallos += len(malas)
        print(f"  {'FALLA' if malas else 'ok   '}  {nombre}"
              + (f"  ({len(malas)})" if malas else ""))
        for m in malas[:8]:
            print(f"           {m}")
    print("\nSIN PROBLEMAS" if not fallos else f"\n{fallos} PROBLEMAS")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())

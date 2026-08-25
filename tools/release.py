#!/usr/bin/env python3
"""Monta el archivo publicable: solo lo que se usa, nada mas.

    python3 tools/release.py

Contenido: una sola carpeta que arrastrar a mods/.

    Starsector Espanol/
        mod_info.json
        data/
        LEEME.txt
        parche-menus/        el parcheador de menus (Java, sin dependencias)

El parcheador va dentro del mod por comodidad, no porque sea parte de el:
el juego ignora las subcarpetas que no conoce, y parchear.jar no esta en
"jars" del mod_info, asi que no lo carga. Puesto ahi, el script se sabe
encontrar solo el juego (tres carpetas hacia arriba).

Requiere haber pasado antes:  ssloc.py inject, package.py, plan.py y la
compilacion de java/parchear.jar.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(RAIZ, "dist", "Starsector Espanol")
DIST = os.path.join(RAIZ, "dist")

# lo que NO viaja aunque este en dist/: el mod ya lleva el LEEME de la raiz
SOBRA = {"README.txt"}

DENTRO = "Starsector Espanol"

PIEZAS = [
    (os.path.join(RAIZ, "java", "parchear.jar"), "parche-menus/parchear.jar"),
    (os.path.join(RAIZ, "work", "plan.txt"), "parche-menus/plan.txt"),
    (os.path.join(RAIZ, "parche-menus", "parchear.sh"), "parche-menus/parchear.sh"),
    (os.path.join(RAIZ, "parche-menus", "parchear.bat"), "parche-menus/parchear.bat"),
]


def version():
    txt = open(os.path.join(MOD, "mod_info.json"), encoding="utf-8").read()
    return json.loads(re.sub(r"#.*", "", txt))["version"]


def leeme(ver):
    return LEEME.format(ver=ver)


def comprueba():
    """Nada a medias: si falta una pieza, mejor fallar que publicar un zip roto."""
    faltan = [o for o, _ in PIEZAS if not os.path.isfile(o)]
    if not os.path.isdir(MOD):
        faltan.append(MOD)
    if faltan:
        sys.exit("faltan piezas:\n  " + "\n  ".join(faltan))


def main():
    comprueba()
    ver = version()
    nombre = f"Starsector-Espanol-{ver}"
    destino = os.path.join(DIST, nombre + ".zip")
    if os.path.exists(destino):
        os.remove(destino)

    n_mod = 0
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr(DENTRO + "/LEEME.txt", leeme(ver))
        for base, dirs, files in os.walk(MOD):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for f in sorted(files):
                if f in SOBRA or f.startswith("."):
                    continue
                ruta = os.path.join(base, f)
                z.write(ruta, os.path.join(DENTRO, os.path.relpath(ruta, MOD)))
                n_mod += 1
        for origen, dentro in PIEZAS:
            z.write(origen, DENTRO + "/" + dentro)

    mb = os.path.getsize(destino) / 1024 / 1024
    print(f"{nombre}.zip  ({mb:.1f} MB)")
    print(f"  una sola carpeta: {n_mod} archivos del mod + LEEME + 4 del parche")
    print(f"  -> {destino}")


LEEME = """\
=====================================================================
 STARSECTOR EN ESPANOL   v{ver}
 Traduccion al espanol (Espana) para Starsector 0.98a-RC8
=====================================================================

Traduce el juego entero: dialogos, misiones, naves, armas, mods de
casco, habilidades, industrias, codex, y tambien los menus, ajustes y
paneles de flota y colonia.

---------------------------------------------------------------------
 INSTALAR          (esto ya traduce casi todo el juego)
---------------------------------------------------------------------

  1. Copia la carpeta "Starsector Espanol" dentro de la carpeta "mods"
     de tu Starsector. Debe quedar asi:

         Starsector/mods/Starsector Espanol/mod_info.json

  2. Abre el juego, entra en "Mods" en el lanzador, activa
     "Starsector en Espanol" y arranca.

Compatible con partidas ya empezadas: solo cambia textos. Se puede
desactivar cuando quieras desde el lanzador.


---------------------------------------------------------------------
 TRADUCIR TAMBIEN LOS MENUS          (opcional, un doble clic)
---------------------------------------------------------------------

Los menus, botones, ajustes y paneles no salen de ningun archivo de
datos: estan dentro del juego, ya compilados. Ningun mod puede llegar
ahi, asi que hace falta este paso aparte. Va dentro de esta misma
carpeta para no tener que buscarlo.

NO hace falta instalar nada. Usa la Java que ya trae Starsector.

Con el mod ya copiado en mods/, entra en la carpeta "parche-menus" y:

  Windows:      doble clic en  parchear.bat
  Linux / Mac:  ./parchear.sh

En Windows, si dice que no puede escribir: cierra el juego y vuelve a
lanzarlo con boton derecho > "Ejecutar como administrador" (con el
juego en Archivos de programa, Windows no deja tocarlo de otro modo).

Encuentra el juego solo. Si lo ejecutas desde otro sitio, pasale la
ruta:

  parchear.bat "C:\\Program Files (x86)\\Fractal Softworks\\Starsector"
  ./parchear.sh /ruta/a/tu/starsector

La primera vez guarda una copia intacta de los .jar (con extension
.orig) y siempre parte de ella, asi que puedes repetirlo sin acumular
danos.

Para dejarlo como estaba, lo mismo anadiendo --restaura:

  parchear.bat --restaura
  ./parchear.sh --restaura

AVISO: cada actualizacion del juego deshace el parche, porque
reemplaza los .jar. Se vuelve a pasar y listo. El mod no se toca.


---------------------------------------------------------------------
 POR QUE NO LLEVA TILDES
---------------------------------------------------------------------

Starsector no carga las fuentes que aportan los mods, asi que ningun
caracter acentuado se dibuja: sale un apostrofo en su lugar. Se
comprobo con otras traducciones ya publicadas, que arrastran el mismo
defecto ("comunica'es" por "comunicacoes"). Por eso el texto va en
ASCII: se pierde la ortografia, pero se lee.


---------------------------------------------------------------------
 QUE SIGUE EN INGLES, Y POR QUE
---------------------------------------------------------------------

Unas pocas palabras se quedan a proposito. El juego usa esa misma
cadena como etiqueta Y como identificador interno: si se traduce, deja
de encontrarse y el juego no arranca. Las mas visibles son las
pestanas Character, Fleet, Refit e Intel.

Tambien queda algun boton que sale de codigo compilado sin ningun
texto que tocar, como "Leave [Esc]" en ciertos dialogos.


---------------------------------------------------------------------
 SI ALGO FALLA
---------------------------------------------------------------------

  1. Deshaz el parche:   parchear.bat --restaura
  2. Desactiva el mod en el lanzador.
  3. Mira starsector.log en la carpeta del juego: la ultima linea de
     error dice exactamente que cadena no se encontro. Con ese dato se
     arregla en minutos.

Si ves texto mal traducido o sin traducir, indica en que pantalla
aparecio.


---------------------------------------------------------------------
 REDISTRIBUCION
---------------------------------------------------------------------

El mod se puede compartir sin problema: son archivos de datos
traducidos.

Los .jar parcheados NO. Son el juego de Fractal Softworks con cambios
dentro, y repartirlos es repartir el juego. Por eso este paquete
incluye el parcheador y no el resultado: cada uno lo aplica sobre su
propia copia.


---------------------------------------------------------------------
 CREDITOS
---------------------------------------------------------------------

Traduccion: vfernandezmeca
Starsector es de Fractal Softworks.
=====================================================================
"""


if __name__ == "__main__":
    main()

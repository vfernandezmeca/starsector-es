#!/usr/bin/env python3
"""Monta la carpeta instalable del mod: mod_info.json + fuentes + README."""
import json, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, "mod")
DIST = os.path.join(ROOT, "dist", "Starsector Espanol")
GAME = "/home/victor/Games/starsector"
# las 8 fuentes del juego base sin glifos acentuados; se toman parcheadas
PTBR = "/home/victor/Downloads/PTBR 154 0.0.7 2026-06-21T14-52Z yvgMZtERg/portugues-brasileiro"
FONTS = ["arial13", "arial14", "futura12", "futura16",
         "insignia12", "ursula12", "ursula14", "ursula16"]

INFO = {
    "id": "starsector_espanol",
    "name": "Starsector en Espanol",
    "author": "vfernandezmeca",
    "utility": "true",
    "totalConversion": "false",
    "version": "0.3.1",
    "description": ("Traduccion al espanol de Starsector. Se instala como mod, "
                    "no sobrescribe los archivos originales del juego."),
    "gameVersion": "0.98a-RC8",
    "modPlugin": "data.scripts.espanol.EspanolModPlugin",
}


README = """================================================================
  STARSECTOR EN ESPANOL  -  v{ver}
  Traduccion al espanol para Starsector {juego}
================================================================

INSTALACION
-----------
1. Descomprime el archivo.
2. Copia la carpeta "Starsector Espanol" dentro de la carpeta "mods"
   de tu instalacion de Starsector.

   Debe quedar asi:
     Starsector/mods/Starsector Espanol/mod_info.json
     Starsector/mods/Starsector Espanol/data/

3. Abre el launcher, entra en "Mods", activa "Starsector en Espanol"
   y arranca el juego.

Compatible con partidas ya empezadas: solo cambia textos.


POR QUE NO LLEVA TILDES
-----------------------
Starsector no carga las fuentes que aportan los mods, asi que ningun
caracter acentuado se dibuja: en su lugar sale un apostrofo. Se
comprobo con otras traducciones publicadas, que arrastran el mismo
defecto. Por eso el texto va en ASCII. Se pierde ortografia, pero se
lee bien, que es de lo que se trata.


QUE TRADUCE ESTE MOD
--------------------
Todo lo que sale de los archivos de datos: dialogos, misiones, naves,
armas, mods de casco, habilidades, industrias, descripciones y codex.


LOS MENUS VAN APARTE
--------------------
Los menus, botones y avisos no salen de ningun archivo de datos: estan
dentro del juego, ya compilados. Ningun mod puede llegar ahi.

Para traducirlos tambien, el paquete incluye la carpeta "parche-menus",
con un script que los reescribe sobre tu propia copia del juego. Es
opcional y reversible. Instrucciones en LEEME.txt.

Sin ese parche, la pantalla de inicio, los ajustes y los paneles de
flota y colonia se quedan en ingles, como en cualquier otra traduccion
de Starsector.


QUE SIGUE EN INGLES AUNQUE PARCHEES
-----------------------------------
Unas pocas palabras se quedan a proposito: el juego usa la misma cadena
como etiqueta y como identificador interno, y traducirla haria que deje
de encontrarse. Las mas visibles son las pestanas Character, Fleet,
Refit e Intel.


DESINSTALAR
-----------
Desactiva el mod en el launcher, o borra su carpeta dentro de "mods".


PROBLEMAS
---------
Si algo falla, starsector.log indica la linea. Si ves texto raro o mal
traducido, avisa indicando donde aparecio.


CREDITOS
--------
Traduccion: vfernandezmeca
"""


def game_version():
    """Lee la version del juego de su propio log si esta disponible."""
    p = os.path.join(GAME, "starsector.log")
    if os.path.exists(p):
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                if "Starsector " in line and "-RC" in line:
                    for tok in line.split():
                        if "-RC" in tok:
                            return tok.strip(".,")
    return INFO["gameVersion"]


def main():
    if not os.path.isdir(MOD):
        sys.exit("falta mod/ — ejecuta antes: python3 tools/ssloc.py inject")
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    shutil.copytree(MOD, DIST)

    # Fuera los archivos identicos al original: no traducen nada y encima
    # bloquean a otros mods que quieran tocar ese mismo archivo.
    import filecmp
    sobran = 0
    for root, _, files in os.walk(DIST):
        for fn in files:
            ruta = os.path.join(root, fn)
            rel = os.path.relpath(ruta, DIST).replace(os.sep, "/")
            orig = os.path.join(GAME, rel)
            if os.path.exists(orig) and filecmp.cmp(ruta, orig, shallow=False):
                os.remove(ruta)
                sobran += 1
    # y las carpetas que hayan quedado vacias
    for root, dirs, files in os.walk(DIST, topdown=False):
        for d in dirs:
            try:
                os.rmdir(os.path.join(root, d))
            except OSError:
                pass
    if sobran:
        print(f"  {sobran} archivos identicos al original, descartados")

    # scripts propios del mod (plugin de tokens de genero)
    srcdir = os.path.join(ROOT, "mod-src")
    if os.path.isdir(srcdir):
        shutil.copytree(srcdir, DIST, dirs_exist_ok=True)

    # Sin fuentes: Starsector NO coge las de los mods (comprobado con el mod
    # PT-BR publicado, que muestra los acentos igual de rotos). Por eso el mod
    # va en ASCII puro y las fuentes sobraban. Quitarlas ademas elimina la
    # dependencia de assets ajenos de cara a publicar.
    missing = []

    # replace: todo lo que el mod pisa del juego base
    replace = []
    for root, _, files in os.walk(DIST):
        for fn in files:
            rel = os.path.relpath(os.path.join(root, fn), DIST).replace(os.sep, "/")
            # SOLO archivos de data/. Los graphics/ NO van en "replace": el
            # mod PT-BR (que si muestra acentos) tiene 0 entradas de graphics
            # ahi, y listarlas impide que se sustituyan las fuentes.
            if (rel.startswith("data/") and "/espanol/" not in rel
                    and os.path.exists(os.path.join(GAME, rel))):
                replace.append(rel)
    info = dict(INFO, gameVersion=game_version(), replace=sorted(replace))
    with open(os.path.join(DIST, "mod_info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    with open(os.path.join(DIST, "README.txt"), "w", encoding="ascii") as f:
        f.write(README.format(ver=info["version"], juego=info["gameVersion"]))

    print(f"dist -> {DIST}")
    print(f"  {len(replace)} archivos en replace, version juego {info['gameVersion']}")
    if missing:
        print("  AVISO fuentes no copiadas:", missing)
    print(f"\nInstalar:  ln -sfn '{DIST}' '{GAME}/mods/Starsector Espanol'")


if __name__ == "__main__":
    main()

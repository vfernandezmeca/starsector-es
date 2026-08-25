"""Genera el plan de parcheo que consume el parcheador en Java.

Todo el analisis (que es texto y que es identificador) se hace aqui, una
vez, en esta maquina. El parcheador que se distribuye solo aplica: asi no
hay que reimplementar en Java el detector de identificadores, que es la
parte delicada.

Formato, una linea por registro, UTF-8:
    C <TAB> jar <TAB> ruta/de/la/Clase.class
    S <TAB> indice del constant pool <TAB> traduccion <TAB> texto original

Se manda el indice porque asi el parcheador no tiene que decidir que entrada
Utf8 es texto y cual es un nombre de metodo: esa decision ya esta tomada aqui.
Y va tambien el texto original porque el indice solo vale para el jar que se
analizo; si el usuario tiene otro build, ese mismo indice apunta a un nombre
de metodo. El parcheador comprueba el texto y, si no cuadra, salta la clase.

Escapes en los textos: \\ \t \n \r
"""
import os
import sys
import zipfile

import jar_extrae
import jarloc
import parchea

SALIDA = os.path.join(parchea.RAIZ, "work", "plan.txt")


def escapa(s):
    return (s.replace("\\", "\\\\").replace("\t", "\\t")
             .replace("\n", "\\n").replace("\r", "\\r"))


def main(salida=SALIDA):
    mapa = parchea.mapa_desde_trabajo()
    claves = {s.encode("utf-8") for s in jar_extrae.identificadores()}
    total = clases = 0
    with open(salida, "w", encoding="utf-8", newline="\n") as out:
        for jar in parchea.JARS:
            ruta = os.path.join(parchea.JUEGO, jar)
            with zipfile.ZipFile(parchea.copia(ruta)) as z:
                for i in z.infolist():
                    if not i.filename.endswith(".class"):
                        continue
                    d = z.read(i)
                    try:
                        utf8, seguros = jarloc._analiza(d)
                        presentes = {idx for idx in seguros
                                     if d[slice(*utf8[idx])] in mapa}
                        textos = {d[slice(*utf8[idx])] for idx in presentes}
                        if textos and jarloc.es_material_de_clave(d, textos):
                            continue
                        presentes = {idx for idx in presentes
                                     if d[slice(*utf8[idx])] not in claves}
                    except Exception:
                        continue
                    if not presentes:
                        continue
                    clases += 1
                    out.write("C\t%s\t%s\n" % (jar, i.filename))
                    for idx in sorted(presentes):
                        viejo = d[slice(*utf8[idx])]
                        out.write("S\t%d\t%s\t%s\n" % (
                            idx, escapa(mapa[viejo].decode("utf-8")),
                            escapa(viejo.decode("utf-8"))))
                        total += 1
    print(f"{clases} clases, {total} sustituciones -> {salida}")
    print(f"{os.path.getsize(salida)} bytes")


if __name__ == "__main__":
    # el jar de Windows es otra ofuscacion: su plan se genera aparte
    #   STARSECTOR=~/Games/starsector-win python3 tools/plan.py work/plan-windows.txt
    main(sys.argv[1] if len(sys.argv) > 1 else SALIDA)

"""El parcheador que se distribuye aplica el plan por indice de constant pool.

Si el jar del usuario no es exactamente el que se analizo aqui, ese indice
apunta a otra cosa: a un nombre de metodo, a un descriptor. Reescribirlo no
da error, deja el juego colgado. Por eso el plan lleva el texto original y
Parchear lo verifica antes de escribir.
"""
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(RAIZ / "tools"))
import jarloc
from test_parchea import clase


def clase_doble(uno, dos):
    """Class file con dos literales traducibles, en los indices 1 y 3."""
    a, b = uno.encode("utf-8"), dos.encode("utf-8")
    pool = (bytes([1]) + struct.pack(">H", len(a)) + a
            + bytes([8]) + struct.pack(">H", 1)
            + bytes([1]) + struct.pack(">H", len(b)) + b
            + bytes([8]) + struct.pack(">H", 3))
    return (b"\xca\xfe\xba\xbe" + struct.pack(">HH", 0, 52)
            + struct.pack(">H", 5) + pool
            + struct.pack(">7H", 0x21, 2, 0, 0, 0, 0, 0))


def busca(nombre):
    ruta = shutil.which(nombre)
    if ruta:
        return ruta
    for jvm in sorted(Path("/usr/lib/jvm").glob("*/bin/" + nombre), reverse=True):
        return str(jvm)
    return None


JAVAC, JAR, JAVA = busca("javac"), busca("jar"), busca("java")


@unittest.skipUnless(JAVAC and JAR and JAVA, "hace falta un JDK")
class TestParchearJar(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.build = tempfile.TemporaryDirectory()
        b = Path(cls.build.name)
        subprocess.run([JAVAC, "--release", "8", "-d", str(b / "clases"),
                        str(RAIZ / "java" / "Parchear.java")], check=True,
                       capture_output=True)
        subprocess.run([JAR, "cfm", str(b / "parchear.jar"),
                        str(RAIZ / "java" / "manifest.txt"),
                        "-C", str(b / "clases"), "."], check=True,
                       capture_output=True)
        cls.parcheador = b / "parchear.jar"

    @classmethod
    def tearDownClass(cls):
        cls.build.cleanup()

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.juego = Path(self.dir.name)
        # el parcheador exige que exista starfarer_obf.jar para dar por bueno
        # el directorio; el plan solo toca el que se le diga
        with zipfile.ZipFile(self.juego / "starfarer_obf.jar", "w") as z:
            z.writestr("a/Uno.class", clase("New Game"))
            z.writestr("a/Dos.class", clase_doble("New Game", "Load Game"))
        shutil.copy(self.parcheador, self.juego / "parchear.jar")

    def tearDown(self):
        self.dir.cleanup()

    def parchea(self, plan):
        (self.juego / "plan.txt").write_text(plan, encoding="utf-8")
        r = subprocess.run([JAVA, "-jar", str(self.juego / "parchear.jar"),
                            str(self.juego)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def literales(self, clase="a/Uno.class"):
        with zipfile.ZipFile(self.juego / "starfarer_obf.jar") as z:
            return jarloc.literales(z.read(clase))

    def test_sustituye_cuando_el_original_cuadra(self):
        self.parchea("C\tstarfarer_obf.jar\ta/Uno.class\n"
                     "S\t1\tPartida nueva\tNew Game\n")
        self.assertEqual(self.literales(), {b"Partida nueva"})

    def test_no_escribe_donde_el_original_no_cuadra(self):
        r = self.parchea("C\tstarfarer_obf.jar\ta/Uno.class\n"
                         "S\t1\tPartida nueva\tOtra Cosa\n")
        self.assertEqual(self.literales(), {b"New Game"})
        self.assertIn("a/Uno.class", r.stderr)

    def test_salta_la_cadena_mala_pero_traduce_el_resto(self):
        """Un indice que no cuadra no puede costar la clase entera: en los
        menus una sola cadena movida dejaba 2.000 sin traducir."""
        r = self.parchea("C\tstarfarer_obf.jar\ta/Dos.class\n"
                         "S\t1\tPartida nueva\tNew Game\n"
                         "S\t3\tCargar partida\tOtra Cosa\n")
        self.assertEqual(self.literales("a/Dos.class"),
                         {b"Partida nueva", b"Load Game"})
        self.assertIn("1 de 2", r.stderr)

    def test_elige_el_plan_que_cuadra_con_el_jar(self):
        """Windows y Linux traen ofuscaciones distintas del jar. Se manda un
        plan por build y el que decide es el jar que hay delante."""
        (self.juego / "plan-otro.txt").write_text(
            "C\tstarfarer_obf.jar\ta/NoExiste.class\n"
            "S\t1\tLo que sea\tLo que sea\n", encoding="utf-8")
        r = self.parchea("C\tstarfarer_obf.jar\ta/Uno.class\n"
                         "S\t1\tPartida nueva\tNew Game\n")
        self.assertEqual(self.literales(), {b"Partida nueva"})
        self.assertIn("plan.txt", r.stdout)

    def test_descarta_el_plan_del_build_que_no_es(self):
        (self.juego / "plan-windows.txt").write_text(
            "C\tstarfarer_obf.jar\ta/Uno.class\n"
            "S\t1\tPartida nueva\tNew Game\n", encoding="utf-8")
        r = self.parchea("C\tstarfarer_obf.jar\ta/NoExiste.class\n"
                         "S\t1\tLo que sea\tLo que sea\n")
        self.assertEqual(self.literales(), {b"Partida nueva"})
        self.assertIn("plan-windows.txt", r.stdout)

    def test_en_empate_se_queda_con_plan_txt(self):
        """starfarer.api.jar es identico en los dos builds: los dos planes lo
        cubren igual. Que salga el de otro sistema despista sin motivo."""
        (self.juego / "plan-windows.txt").write_text(
            "C\tstarfarer_obf.jar\ta/Uno.class\n"
            "S\t1\tPartida nueva\tNew Game\n", encoding="utf-8")
        r = self.parchea("C\tstarfarer_obf.jar\ta/Uno.class\n"
                         "S\t1\tPartida nueva\tNew Game\n")
        self.assertNotIn("plan-windows.txt", r.stdout)

    def test_avisa_de_las_clases_del_plan_que_no_estan(self):
        """Si el jar es otro build, media plan apunta a clases con otro
        nombre. Callarselo hace creer que se ha traducido todo."""
        r = self.parchea("C\tstarfarer_obf.jar\ta/Uno.class\n"
                         "S\t1\tPartida nueva\tNew Game\n"
                         "C\tstarfarer_obf.jar\ta/NoExiste.class\n"
                         "S\t1\tCargar partida\tLoad Game\n"
                         "S\t3\tSalir\tExit\n")
        self.assertIn("clases del plan que no estan en este jar: 1", r.stderr)
        self.assertIn("2 cadenas", r.stderr)

    def test_cuenta_solo_lo_que_ha_escrito(self):
        r = self.parchea("C\tstarfarer_obf.jar\ta/Dos.class\n"
                         "S\t1\tPartida nueva\tNew Game\n"
                         "S\t3\tCargar partida\tOtra Cosa\n")
        self.assertIn("1 literales traducidos", r.stdout)


if __name__ == "__main__":
    unittest.main()

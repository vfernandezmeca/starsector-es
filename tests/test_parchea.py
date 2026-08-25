"""El parcheador toca el jar del juego. Si se equivoca, no arranca."""
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import jarloc
import parchea


def clase(texto):
    """Class file minimo con un unico literal traducible."""
    b = texto.encode("utf-8")
    pool = (bytes([1]) + struct.pack(">H", len(b)) + b
            + bytes([8]) + struct.pack(">H", 1))
    return (b"\xca\xfe\xba\xbe" + struct.pack(">HH", 0, 52)
            + struct.pack(">H", 3) + pool
            + struct.pack(">7H", 0x21, 2, 0, 0, 0, 0, 0))


class TestParchea(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.jar = Path(self.dir.name) / "prueba.jar"
        with zipfile.ZipFile(self.jar, "w") as z:
            z.writestr("a/Uno.class", clase("New Game"))
            z.writestr("a/Dos.class", clase("Load Game"))
            z.writestr("META-INF/datos.properties", "clave=valor")
        self.original = self.jar.read_bytes()

    def tearDown(self):
        self.dir.cleanup()

    def literales_de(self, nombre):
        z = zipfile.ZipFile(self.jar)
        return jarloc.literales(z.read(nombre))

    def test_hace_copia_antes_de_tocar_nada(self):
        parchea.parchea_jar(self.jar, {b"New Game": b"Partida nueva"})
        copia = self.jar.with_suffix(".jar.orig")
        self.assertTrue(copia.exists())
        self.assertEqual(copia.read_bytes(), self.original)

    def test_sustituye_el_literal(self):
        parchea.parchea_jar(self.jar, {b"New Game": b"Partida nueva"})
        self.assertIn(b"Partida nueva", self.literales_de("a/Uno.class"))

    def test_deja_intacto_lo_que_no_esta_en_el_mapa(self):
        parchea.parchea_jar(self.jar, {b"New Game": b"Partida nueva"})
        self.assertEqual(self.literales_de("a/Dos.class"), {b"Load Game"})

    def test_conserva_las_entradas_que_no_son_clases(self):
        parchea.parchea_jar(self.jar, {b"New Game": b"Partida nueva"})
        z = zipfile.ZipFile(self.jar)
        self.assertEqual(z.read("META-INF/datos.properties"), b"clave=valor")

    def test_parchear_dos_veces_da_el_mismo_resultado(self):
        """Siempre parte del .orig, asi no se traduce lo ya traducido."""
        mapa = {b"New Game": b"Partida nueva"}
        parchea.parchea_jar(self.jar, mapa)
        primero = self.jar.read_bytes()
        parchea.parchea_jar(self.jar, mapa)
        self.assertEqual(self.jar.read_bytes(), primero)

    def test_cuenta_lo_que_ha_cambiado(self):
        n = parchea.parchea_jar(self.jar, {b"New Game": b"Partida nueva",
                                           b"Load Game": b"Cargar partida"})
        self.assertEqual(n, 2)

    def test_todas_las_clases_siguen_parseando(self):
        parchea.parchea_jar(self.jar, {b"New Game": b"Partida nueva"})
        z = zipfile.ZipFile(self.jar)
        for i in z.infolist():
            if i.filename.endswith(".class"):
                jarloc.literales(z.read(i))     # lanza si quedo corrupto


if __name__ == "__main__":
    unittest.main()


class TestNoTocaLaLicencia(unittest.TestCase):
    """La clase que deriva el serial no se toca ni aunque su texto este
    traducido: el juego indexa esa frase para validar el codigo."""

    CLASE = "com/fs/starfarer/campaign/accidents/oOOO.class"
    JUEGO = Path("/home/victor/Games/starsector")

    def setUp(self):
        origen = next((p for p in [self.JUEGO / "starfarer_obf.jar.orig",
                                   self.JUEGO / "starfarer_obf.jar"] if p.exists()), None)
        if not origen:
            raise unittest.SkipTest("juego no instalado")
        self.cruda = zipfile.ZipFile(origen).read(self.CLASE)
        self.dir = tempfile.TemporaryDirectory()
        self.jar = Path(self.dir.name) / "prueba.jar"
        with zipfile.ZipFile(self.jar, "w") as z:
            z.writestr(self.CLASE, self.cruda)
            z.writestr("a/Uno.class", clase("New Game"))

    def tearDown(self):
        self.dir.cleanup()

    def test_la_clase_del_serial_queda_intacta(self):
        mapa = {s: b"TRADUCIDO" for s in jarloc.literales(self.cruda)}
        mapa[b"New Game"] = b"Partida nueva"
        parchea.parchea_jar(self.jar, mapa)
        z = zipfile.ZipFile(self.jar)
        self.assertEqual(z.read(self.CLASE), self.cruda)

    def test_pero_las_demas_si_se_traducen(self):
        parchea.parchea_jar(self.jar, {b"New Game": b"Partida nueva"})
        z = zipfile.ZipFile(self.jar)
        self.assertIn(b"Partida nueva", jarloc.literales(z.read("a/Uno.class")))


class TestNoTocaClaves(unittest.TestCase):
    """Si una cadena se usa como clave en alguna clase, no se traduce en
    ninguna. Decidirlo por clase rompia el juego: la clase que registra y
    la que consulta dejaban de coincidir."""

    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from test_jarloc import clase_con_llamada
        self.dir = tempfile.TemporaryDirectory()
        self.jar = Path(self.dir.name) / "prueba.jar"
        with zipfile.ZipFile(self.jar, "w") as z:
            z.writestr("a/Compara.class", clase_con_llamada("Missile", "equals"))
            z.writestr("a/Muestra.class", clase_con_llamada("Missile", "addPara"))

    def tearDown(self):
        self.dir.cleanup()

    def claves(self):
        return parchea.claves_del_propio_jar(self.jar)

    def test_donde_se_compara_no_se_traduce(self):
        parchea.parchea_jar(self.jar, {b"Missile": b"Misil"}, self.claves())
        z = zipfile.ZipFile(self.jar)
        self.assertEqual(jarloc.literales(z.read("a/Compara.class")), {b"Missile"})

    def test_tampoco_donde_solo_se_muestra(self):
        parchea.parchea_jar(self.jar, {b"Missile": b"Misil"}, self.claves())
        z = zipfile.ZipFile(self.jar)
        self.assertEqual(jarloc.literales(z.read("a/Muestra.class")), {b"Missile"})

    def test_una_cadena_que_nadie_compara_si_se_traduce(self):
        from test_jarloc import clase_con_llamada
        with zipfile.ZipFile(self.jar, "a") as z:
            z.writestr("a/Solo.class", clase_con_llamada("Fragata", "addPara"))
        parchea.parchea_jar(self.jar, {b"Fragata": b"Frigate"}, self.claves())
        z = zipfile.ZipFile(self.jar)
        self.assertEqual(jarloc.literales(z.read("a/Solo.class")), {b"Frigate"})


class TestIdentificadorGlobal(unittest.TestCase):
    """Un identificador se registra en una clase y se consulta en otra.
    Si se traduce solo donde no se detecta, las dos dejan de coincidir y
    el juego no encuentra lo que busca. Decision global, no por clase."""

    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from test_jarloc import clase_con_llamada
        self.dir = tempfile.TemporaryDirectory()
        self.jar = Path(self.dir.name) / "prueba.jar"
        with zipfile.ZipFile(self.jar, "w") as z:
            z.writestr("a/Busca.class", clase_con_llamada("Campaign State", "equals"))
            z.writestr("a/Registra.class", clase_con_llamada("Campaign State", "addPara"))

    def tearDown(self):
        self.dir.cleanup()

    def test_no_se_traduce_en_ninguna_de_las_dos(self):
        parchea.parchea_jar(self.jar, {b"Campaign State": b"Estado de campana"},
                            parchea.claves_del_propio_jar(self.jar))
        z = zipfile.ZipFile(self.jar)
        for c in ("a/Busca.class", "a/Registra.class"):
            self.assertEqual(jarloc.literales(z.read(c)), {b"Campaign State"},
                             f"{c} deberia quedar intacta")

"""De donde sale la lista de cadenas que no se pueden traducir.

No basta con mirar el bytecode: el juego tambien busca por nombre de
clave JSON, por columna de CSV y por trozo de ruta. Cada rotura real ha
anadido una fuente a esta lista.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import jar_extrae as jx


class TestClavesDeDatos(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.raiz = Path(self.dir.name)
        (self.raiz / "weapons").mkdir()
        (self.raiz / "weapons" / "amblaster.wpn").write_text(
            '{"specClass":"projectile","projectileSpecId":"amblaster_shot",'
            '"behavior":"BALLISTIC","autocharge":true}')
        (self.raiz / "hulls").mkdir()
        (self.raiz / "hulls" / "ship_data.csv").write_text(
            "name,id,hitpoints,armor rating\nOnslaught,onslaught,20000,1500\n",
            encoding="cp1252")

    def tearDown(self):
        self.dir.cleanup()

    def test_saca_las_claves_json(self):
        c = jx.claves_de_datos(str(self.raiz))
        self.assertIn("projectileSpecId", c)
        self.assertIn("behavior", c)
        self.assertIn("autocharge", c)

    def test_saca_las_columnas_de_csv(self):
        c = jx.claves_de_datos(str(self.raiz))
        self.assertIn("hitpoints", c)
        self.assertIn("armor rating", c)

    def test_no_saca_los_valores(self):
        """Los valores si son texto: 'Onslaught' es el nombre de la nave."""
        c = jx.claves_de_datos(str(self.raiz))
        self.assertNotIn("Onslaught", c)


class TestTrozosDeRuta(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.raiz = Path(self.dir.name)
        (self.raiz / "weapons" / "proj").mkdir(parents=True)
        (self.raiz / "weapons" / "proj" / "amblaster_shot.proj").write_text("{}")

    def tearDown(self):
        self.dir.cleanup()

    def test_saca_los_nombres_de_carpeta(self):
        """'proj' es la carpeta de proyectiles: el cargador monta la ruta
        concatenandola, y traducirla deja la spec en null."""
        t = jx.trozos_de_ruta(str(self.raiz))
        self.assertIn("proj", t)
        self.assertIn("weapons", t)

    def test_saca_los_nombres_de_archivo_sin_extension(self):
        t = jx.trozos_de_ruta(str(self.raiz))
        self.assertIn("amblaster_shot", t)


if __name__ == "__main__":
    unittest.main()


class TestPiezasDeIdentificador(unittest.TestCase):
    """El cargador compone ids juntando trozos: hullId + "_" + "Standard",
    o filtra por extension ("skin"). Esos trozos parecen texto normal, pero
    traducirlos deja specs sin registrar y el juego no arranca.

    Se piden dos evidencias a la vez, no una: que el trozo aparezca en los
    nombres de fichero de los datos Y que el codigo de carga lo tenga como
    literal. Con una sola sobraban palabras de pantalla como 'Cancel'.
    """

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.raiz = Path(self.dir.name)
        (self.raiz / "variants").mkdir()
        (self.raiz / "variants" / "ox_Standard.variant").write_text("{}")
        (self.raiz / "hulls").mkdir()
        (self.raiz / "hulls" / "afflictor.skin").write_text("{}")

    def tearDown(self):
        self.dir.cleanup()

    def test_saca_las_extensiones(self):
        e = jx.extensiones(str(self.raiz))
        self.assertIn("skin", e)
        self.assertIn("variant", e)

    def test_el_trozo_solo_cuenta_si_el_cargador_lo_usa(self):
        piezas = jx.piezas_de_id(str(self.raiz), {"Standard", "Loading hull ["})
        self.assertIn("Standard", piezas)

    def test_un_trozo_que_el_cargador_no_menciona_no_cuenta(self):
        piezas = jx.piezas_de_id(str(self.raiz), {"Loading hull ["})
        self.assertNotIn("Standard", piezas)

    def test_una_palabra_del_cargador_que_no_es_nombre_de_fichero_no_cuenta(self):
        """'Cancel' esta en el codigo de carga pero no compone ningun id."""
        piezas = jx.piezas_de_id(str(self.raiz), {"Cancel", "Standard"})
        self.assertNotIn("Cancel", piezas)


class TestValoresDeColumnaId(unittest.TestCase):
    """Los ids de objeto viven como valor en la columna 'id' de los CSV y
    como constante en el paquete ids/. No hay ninguna llamada que los
    delate: son 'static final String', asi que el bytecode no ayuda."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.raiz = Path(self.dir.name)
        (self.raiz / "special_items.csv").write_text(
            "name,id,tier\nSynchrotron Core,synchrotron,3\n"
            "Planetkiller,planetkiller,4\n", encoding="cp1252")

    def tearDown(self):
        self.dir.cleanup()

    def test_saca_los_valores_de_la_columna_id(self):
        v = jx.valores_de_id(str(self.raiz))
        self.assertIn("synchrotron", v)
        self.assertIn("planetkiller", v)

    def test_no_saca_los_valores_de_otras_columnas(self):
        """'Synchrotron Core' es el nombre visible: eso si se traduce."""
        v = jx.valores_de_id(str(self.raiz))
        self.assertNotIn("Synchrotron Core", v)
        self.assertNotIn("3", v)

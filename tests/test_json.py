"""Extraccion de texto de los JSON traducidos enteros.

tips.json mezcla dos formas en el mismo array: objetos {"tip": "..."} y
cadenas sueltas. El extractor solo veia las primeras.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import ssloc

TIPS = '''{
\ttips:[
{"freq":0, "tip":"Puedes cambiar la frecuencia."},
"Lower your shields to dissipate \\"hard\\" flux.",
"Shields and weapons both generate flux.",
]
}'''


class TestJsonCadenas(unittest.TestCase):

    def textos(self, txt):
        return [v for _, v in ssloc.json_cadenas(txt)]

    def test_saca_los_valores_de_objeto(self):
        self.assertIn("Puedes cambiar la frecuencia.", self.textos(TIPS))

    def test_saca_las_cadenas_sueltas_del_array(self):
        t = self.textos(TIPS)
        self.assertIn('Lower your shields to dissipate \\"hard\\" flux.', t)
        self.assertIn("Shields and weapons both generate flux.", t)

    def test_no_saca_los_nombres_de_clave(self):
        self.assertNotIn("tip", self.textos(TIPS))
        self.assertNotIn("freq", self.textos(TIPS))

    def test_el_campo_identifica_de_donde_sale(self):
        campos = dict((v, c) for c, v in ssloc.json_cadenas(TIPS))
        self.assertEqual(campos["Puedes cambiar la frecuencia."], "tip")
        self.assertEqual(campos["Shields and weapons both generate flux."], "item")


if __name__ == "__main__":
    unittest.main()


class TestJsonSustituye(unittest.TestCase):
    """La inyeccion tiene que ver exactamente lo mismo que la extraccion,
    o el mod queda a medias."""

    def test_identidad_no_cambia_un_byte(self):
        self.assertEqual(ssloc.json_sub(TIPS, lambda s: s), TIPS)

    def test_traduce_la_cadena_suelta(self):
        out = ssloc.json_sub(TIPS, lambda s: "TRADUCIDO"
                             if s.startswith("Shields") else s)
        self.assertIn('"TRADUCIDO"', out)
        self.assertIn('"Lower your shields', out)

    def test_no_toca_los_nombres_de_clave(self):
        out = ssloc.json_sub(TIPS, lambda s: "X")
        self.assertIn('"tip":', out)
        self.assertIn('"freq":', out)

    def test_conserva_las_comillas_escapadas(self):
        out = ssloc.json_sub(TIPS, lambda s: s)
        self.assertIn('\\"hard\\"', out)

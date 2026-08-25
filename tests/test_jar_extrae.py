"""Que entra y que no en la traduccion de los jars.

Un falso positivo aqui no se ve: renombra una clave de memoria del motor
de reglas y la mision deja de dispararse sin ningun error.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import jar_extrae as jx


class TestTraducible(unittest.TestCase):

    def si(self, s):
        self.assertTrue(jx.traducible(s), f"deberia entrar: {s!r}")

    def no(self, s):
        self.assertFalse(jx.traducible(s), f"NO deberia entrar: {s!r}")

    # --- lo que si es texto de pantalla
    def test_frase_normal(self):
        self.si("Are you sure? This action can not be undone.")

    def test_etiqueta_de_dos_palabras(self):
        self.si("New Game")
        self.si("Fleet Command")

    def test_texto_con_formato(self):
        self.si("Recovered %s units of fuel")

    def test_palabra_suelta_de_la_lista_blanca(self):
        self.si("Quit")
        self.si("Leave")

    # --- lo que romperia el juego
    def test_clave_camel_case(self):
        self.no("ManagedFleetData")
        self.no("SITMMercWarning")
        self.no("GalatianAcademyStipend")

    def test_constante_en_mayusculas(self):
        self.no("PLAYER_FLEET")
        self.no("OPEN_MAP")

    def test_identificador_con_guion_bajo_o_medio(self):
        self.no("barren-desert")
        self.no("go_dark")

    def test_palabra_suelta_en_minusculas_es_texto(self):
        """armor, hull: el juego los pinta en mayusculas en el refit. Si
        ademas sirven de id, lo dice el bytecode y se descartan por ahi."""
        self.si("armor")
        self.si("weapon")

    def test_etiqueta_con_barra_y_mayusculas_no_es_una_ruta(self):
        self.si("Crew/Cargo")
        self.no("data/hulls")
        self.no("graphics/fonts/orbitron24aabold.fnt")

    def test_texto_en_minusculas_de_varias_palabras_entra(self):
        self.si("top speed")
        self.si("next tip")

    def test_ruta_o_recurso(self):
        self.no("graphics/fonts/orbitron24aabold.fnt")
        self.no("data/campaign/rules.csv")

    def test_nombre_de_clase_java(self):
        self.no("java.io.FilterOutputStream")
        self.no("com.fs.starfarer.api.Global")

    def test_clave_de_licencia(self):
        self.no("AA09C-XMR8A-X7REE-Z2A1I")

    def test_palabra_suelta_con_forma_de_etiqueta_si_entra(self):
        """Vistas en pantalla: son botones y cabeceras de columna. El riesgo
        de que sean claves lo cubre jarloc.literales_comparados, que mira
        como las usa el bytecode."""
        self.si("Assault")
        self.si("Vents")
        self.si("Hitpoints")

    def test_palabra_suelta_marcada_como_clave_no_entra(self):
        self.assertFalse(jx.traducible("Missile", claves={"Missile"}))

    def test_texto_con_barra_entra_si_lleva_espacios(self):
        """El bug que dejo 'Capture / Control' y 'Damage / second' en ingles."""
        self.si("Capture / Control")
        self.si("Damage / second")
        self.si("Show other floating text (weapons/engines disabled)")

    def test_vacio_y_simbolos(self):
        self.no("")
        self.no("   ")
        self.no("%s")
        self.no("...")


class TestExtraccion(unittest.TestCase):

    def test_entrada_de_catalogo_lleva_clase_y_jar(self):
        e = jx.entrada("starfarer_obf.jar", "com/fs/starfarer/title/ooOO.class",
                       "New Game")
        self.assertEqual(e["s"], "New Game")
        self.assertIn("starfarer_obf.jar", e["ctx"])
        self.assertIn("ooOO", e["ctx"])
        self.assertEqual(len(e["k"]), 12)

    def test_misma_cadena_mismo_id_en_distinta_clase(self):
        """Los ids son hash del texto: una cadena repetida se traduce una vez."""
        a = jx.entrada("starfarer_obf.jar", "a/B.class", "New Game")
        b = jx.entrada("starfarer.api.jar", "c/D.class", "New Game")
        self.assertEqual(a["k"], b["k"])


if __name__ == "__main__":
    unittest.main()

    def test_palabra_suelta_en_mayusculas_no_entra(self):
        """MISSILE, GLOW, CUSTOM: nombres de constante que el juego busca
        con valueOf desde los datos. Traducirlos revienta el combate."""
        self.no("MISSILE")
        self.no("GLOW")
        self.no("CUSTOM")

    def test_sufijo_de_fichero_no_entra(self):
        """El juego nombra los guardados temporales con .inprogress y .bak:
        traducir el sufijo rompe el guardado."""
        self.no(".inprogress")
        self.no(".bak")
        self.no(".variant")

    def test_una_frase_que_empieza_por_punto_si_entra(self):
        self.si(". Requires a spaceport.")

"""Tests del reescritor de literales en class files.

Si esto falla en produccion, el juego no arranca: el constant pool
mezcla texto visible con nombres de metodos.
"""
import struct
import sys
import zipfile
from pathlib import Path

import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import jarloc

JUEGO = Path("/home/victor/Games/starsector")
# el jar instalado puede estar parcheado; los tests van contra el virgen
JAR = next((p for p in [JUEGO / "starfarer_obf.jar.orig",
                        JUEGO / "starfarer_obf.jar"] if p.exists()),
           JUEGO / "starfarer_obf.jar")
CLASE_MENU = "com/fs/starfarer/title/ooOO.class"


def clase_real():
    if not JAR.exists():
        raise unittest.SkipTest("juego no instalado")
    return zipfile.ZipFile(JAR).read(CLASE_MENU)


def utf8(txt):
    b = txt.encode("utf8")
    return bytes([1]) + struct.pack(">H", len(b)) + b


COLA = struct.pack(">7H", 0x21, 2, 0, 0, 0, 0, 0)
"""access, this, super, y los cuatro contadores a cero."""


def sintetica(entradas, extra=COLA):
    """Class file minimo pero estructuralmente completo."""
    cuerpo = b"".join(entradas)
    return (b"\xca\xfe\xba\xbe" + struct.pack(">HH", 0, 52)
            + struct.pack(">H", len(entradas) + 1) + cuerpo + extra)


class TestJarloc(unittest.TestCase):
    def test_identidad_devuelve_bytes_identicos(self):
        d = clase_real()
        assert jarloc.reescribe(d, {}) == d


    def test_identidad_explicita_no_altera_nada(self):
        d = clase_real()
        mapa = {s: s for s in jarloc.literales(d)}
        assert jarloc.reescribe(d, mapa) == d


    def test_encuentra_los_literales_del_menu(self):
        lits = jarloc.literales(clase_real())
        assert b"New Game" in lits
        assert b"Quit" in lits


    def test_no_confunde_nombres_de_metodo_con_texto(self):
        lits = jarloc.literales(clase_real())
        assert b"advanceImpl" not in lits
        assert b"getFader" not in lits


    def test_reescribe_literal(self):
        d = clase_real()
        out = jarloc.reescribe(d, {b"Quit": b"Salir"})
        lits = jarloc.literales(out)
        assert b"Salir" in lits
        assert b"Quit" not in lits


    def test_literal_mas_largo_actualiza_la_longitud(self):
        d = clase_real()
        largo = b"Comandancia de la Flota"
        out = jarloc.reescribe(d, {b"Fleet Command": largo})
        assert largo in jarloc.literales(out)
        assert len(out) == len(d) + len(largo) - len(b"Fleet Command")


    def test_utf8_compartido_con_un_nombre_no_es_traducible(self):
        """javac deduplica: si 'run' es literal Y nombre de metodo,
        reescribirlo renombra el metodo y revienta la clase."""
        d = sintetica([
            utf8("run"),                                    # 1
            bytes([8]) + struct.pack(">H", 1),              # 2: String -> 1
            utf8("()V"),                                    # 3
            bytes([12]) + struct.pack(">HH", 1, 3),         # 4: NameAndType -> 1
        ])
        assert jarloc.literales(d) == set()


    def test_utf8_solo_de_literal_si_es_traducible(self):
        d = sintetica([
            utf8("Quit"),                                   # 1
            bytes([8]) + struct.pack(">H", 1),              # 2: String -> 1
        ])
        assert jarloc.literales(d) == {b"Quit"}


    def test_rechaza_lo_que_no_es_class(self):
        with self.assertRaises(ValueError):
            jarloc.literales(b"PK\x03\x04nope")


if __name__ == "__main__":
    unittest.main()


class TestMaterialDeClave(unittest.TestCase):
    """El juego deriva el serial indexando una frase larga escondida en
    campaign/accidents. Traducirla invalida codigos de licencia legitimos."""

    def clase(self, nombre):
        if not JAR.exists():
            raise unittest.SkipTest("juego no instalado")
        return zipfile.ZipFile(JAR).read(nombre)

    def test_detecta_la_frase_que_genera_el_serial(self):
        d = self.clase("com/fs/starfarer/campaign/accidents/oOOO.class")
        self.assertTrue(jarloc.es_material_de_clave(d, jarloc.literales(d)))

    def test_la_clase_del_menu_no_es_material_de_clave(self):
        d = self.clase(CLASE_MENU)
        self.assertFalse(jarloc.es_material_de_clave(d, jarloc.literales(d)))

    def test_sin_literales_candidatos_no_marca_nada(self):
        d = self.clase("com/fs/starfarer/campaign/accidents/oOOO.class")
        self.assertFalse(jarloc.es_material_de_clave(d, set()))


def _u(txt):
    b = txt.encode("utf8")
    return bytes([1]) + struct.pack(">H", len(b)) + b


def clase_con_llamada(literal, metodo, receptor=True):
    """Class file con un literal y una llamada a `metodo` sobre el.

    receptor=True  -> "literal".metodo(x)   : ldc, aload, invoke
    receptor=False -> x.metodo("literal")   : aload, ldc, invoke
    """
    pool = [
        _u(literal),                                   # 1
        bytes([8]) + struct.pack(">H", 1),             # 2 String -> 1
        _u(metodo),                                    # 3
        _u("(Ljava/lang/Object;)Z"),                   # 4
        bytes([12]) + struct.pack(">HH", 3, 4),        # 5 NameAndType
        _u("java/lang/String"),                        # 6
        bytes([7]) + struct.pack(">H", 6),             # 7 Class
        bytes([10]) + struct.pack(">HH", 7, 5),        # 8 Methodref
        _u("Code"),                                    # 9
        _u("m"),                                       # 10
        _u("()V"),                                     # 11
    ]
    ldc = bytes([0x12, 2])                             # ldc #2
    inv = bytes([0xb6]) + struct.pack(">H", 8)         # invokevirtual #8
    code = (ldc + b"\x2a" + inv) if receptor else (b"\x2a" + ldc + inv)
    cuerpo = struct.pack(">HHHH", 0, 0, len(code) // 1, 0)[:4] + b""
    # atributo Code: max_stack, max_locals, code_length, code, exc=0, attrs=0
    payload = (struct.pack(">HHI", 2, 1, len(code)) + code
               + struct.pack(">HH", 0, 0))
    attr = struct.pack(">HI", 9, len(payload)) + payload
    metodo_bytes = struct.pack(">HHHH", 0x0001, 10, 11, 1) + attr
    return (b"\xca\xfe\xba\xbe" + struct.pack(">HH", 0, 52)
            + struct.pack(">H", len(pool) + 1) + b"".join(pool)
            + struct.pack(">5H", 0x21, 7, 0, 0, 0)      # access,this,super,ifaces,fields
            + struct.pack(">H", 1) + metodo_bytes       # methods
            + struct.pack(">H", 0))                     # attrs


class TestLiteralComparado(unittest.TestCase):
    """Una palabra suelta es texto de pantalla salvo que el codigo la
    compare: entonces es una clave y traducirla rompe la comparacion."""

    def test_literal_como_receptor_de_equals_es_clave(self):
        d = clase_con_llamada("Missile", "equals", receptor=True)
        self.assertEqual(jarloc.literales_comparados(d), {b"Missile"})

    def test_literal_como_argumento_de_equals_es_clave(self):
        d = clase_con_llamada("Missile", "equals", receptor=False)
        self.assertEqual(jarloc.literales_comparados(d), {b"Missile"})

    def test_literal_solo_mostrado_no_es_clave(self):
        d = clase_con_llamada("Missile", "addPara", receptor=False)
        self.assertEqual(jarloc.literales_comparados(d), set())

    def test_equalsIgnoreCase_tambien_cuenta(self):
        d = clase_con_llamada("Missile", "equalsIgnoreCase", receptor=True)
        self.assertEqual(jarloc.literales_comparados(d), {b"Missile"})

    # El caso "un getter aparece cerca por casualidad" lo cubre
    # TestDecodificacionPrecisa: aqui el fixture lo pone pegado al literal,
    # que si es una busqueda por id y debe contar.

    def test_map_get_si_es_busqueda(self):
        d = clase_con_llamada("Missile", "get", receptor=False)
        self.assertEqual(jarloc.literales_comparados(d), {b"Missile"})


class TestConstantesDeEnum(unittest.TestCase):
    """Los nombres de enum viven como literales: new Tipo("MISSILE", 0).
    El juego los busca con valueOf desde los .proj, asi que traducirlos
    hace que el dato original deje de encontrarse y revienta en combate.
    """

    ENUM = "com/fs/starfarer/loading/specs/o00o$o.class"

    def clase(self, nombre):
        if not JAR.exists():
            raise unittest.SkipTest("juego no instalado")
        return zipfile.ZipFile(JAR).read(nombre)

    def test_no_ofrece_el_nombre_de_la_constante(self):
        lits = jarloc.literales(self.clase(self.ENUM))
        self.assertNotIn(b"MISSILE", lits)

    def test_reconoce_la_clase_como_enum(self):
        self.assertTrue(jarloc.es_enum(self.clase(self.ENUM)))
        self.assertFalse(jarloc.es_enum(self.clase(CLASE_MENU)))

    def test_en_un_enum_el_texto_con_espacios_si_se_traduce(self):
        """DamageType es un enum y ademas guarda descripciones visibles."""
        api = next((q for q in [JUEGO / "starfarer.api.jar.orig",
                                JUEGO / "starfarer.api.jar"] if q.exists()), None)
        if not api:
            raise unittest.SkipTest("juego no instalado")
        d = zipfile.ZipFile(api).read("com/fs/starfarer/api/combat/DamageType.class")
        lits = jarloc.literales(d)
        self.assertTrue(any(b" vs " in s for s in lits))
        self.assertNotIn(b"FRAGMENTATION", lits)


class TestAliasDeSerializacion(unittest.TestCase):
    """XStream guarda las partidas usando alias como nombre de elemento
    XML: <Hyperspace>. Traducir el alias hace que los saves ya existentes
    no carguen, aunque la misma palabra sea texto de pantalla en la interfaz."""

    GESTOR = "com/fs/starfarer/campaign/save/CampaignGameManager.class"

    def test_el_alias_se_detecta_como_identificador(self):
        if not JAR.exists():
            raise unittest.SkipTest("juego no instalado")
        d = zipfile.ZipFile(JAR).read(self.GESTOR)
        self.assertIn(b"Hyperspace", jarloc.literales_comparados(d))

    def test_en_una_clase_de_interfaz_la_misma_palabra_sigue_siendo_texto(self):
        d = clase_con_llamada("Hyperspace", "addPara", receptor=False)
        self.assertEqual(jarloc.literales_comparados(d), set())


def clase_con_codigo(literal, instrucciones, metodos):
    """Class file con un literal y una secuencia de instrucciones concreta.

    metodos: lista de nombres; el Methodref i-esimo queda en el indice 8+i.
    instrucciones: bytes ya montados del cuerpo del metodo.
    """
    pool = [
        _u(literal),                                   # 1
        bytes([8]) + struct.pack(">H", 1),             # 2 String
        _u("()V"),                                     # 3
        _u("java/lang/String"),                        # 4
        bytes([7]) + struct.pack(">H", 4),             # 5 Class
        _u("Code"),                                    # 6
        _u("m"),                                       # 7
    ]
    idx = 8
    for nombre in metodos:
        pool.append(_u(nombre))                        # idx
        pool.append(bytes([12]) + struct.pack(">HH", idx, 3))     # idx+1 NaT
        pool.append(bytes([10]) + struct.pack(">HH", 5, idx + 1))  # idx+2 Ref
        idx += 3
    payload = (struct.pack(">HHI", 4, 2, len(instrucciones)) + instrucciones
               + struct.pack(">HH", 0, 0))
    attr = struct.pack(">HI", 6, len(payload)) + payload
    met = struct.pack(">HHHH", 0x0001, 7, 3, 1) + attr
    return (b"\xca\xfe\xba\xbe" + struct.pack(">HH", 0, 52)
            + struct.pack(">H", len(pool) + 1) + b"".join(pool)
            + struct.pack(">5H", 0x21, 5, 0, 0, 0)
            + struct.pack(">H", 1) + met + struct.pack(">H", 0))


LDC = bytes([0x12, 2])
ALOAD0 = b"\x2a"


def ref(i):
    """Methodref del metodo i-esimo pasado a clase_con_codigo."""
    return struct.pack(">H", 10 + i * 3)


class TestDecodificacionPrecisa(unittest.TestCase):
    """La deteccion mira instrucciones, no bytes sueltos: un getter que
    aparece cerca por casualidad no convierte el texto en identificador."""

    def test_equals_pegado_al_literal_si_cuenta(self):
        # x.equals("lit")
        d = clase_con_codigo("Stars", ALOAD0 + LDC + b"\xb6" + ref(0) + b"\x57\xb1",
                             ["equals"])
        self.assertEqual(jarloc.literales_comparados(d), {b"Stars"})

    def test_getter_a_dos_instrucciones_no_cuenta(self):
        # sb.append("lit"); sb.append(x.getSpeed())  -> el ldc va con append
        codigo = (ALOAD0 + LDC + b"\xb6" + ref(0)      # append("Stars")
                  + ALOAD0 + b"\xb6" + ref(1)          # getSpeed()
                  + b"\x57\xb1")
        d = clase_con_codigo("Stars", codigo, ["append", "getSpeed"])
        self.assertEqual(jarloc.literales_comparados(d), set())

    def test_getter_pegado_al_literal_si_cuenta(self):
        # settings.getString("lit")
        d = clase_con_codigo("Stars", ALOAD0 + LDC + b"\xb6" + ref(0) + b"\x57\xb1",
                             ["getString"])
        self.assertEqual(jarloc.literales_comparados(d), {b"Stars"})

    def test_no_confunde_operandos_con_opcodes(self):
        """Un operando puede valer 0xb6 sin ser un invokevirtual."""
        # sipush 0xb600 ; ldc ; areturn   -> no hay ninguna llamada
        d = clase_con_codigo("Stars", b"\x11\xb6\x00" + LDC + b"\xb0", ["equals"])
        self.assertEqual(jarloc.literales_comparados(d), set())


class TestRegistroDeCampos(unittest.TestCase):
    """XStream registra campos con llamadas de varios argumentos:
    addImplicitMap(cls, "demands", "key", Tipo.class). El literal queda a
    cuatro instrucciones de la llamada, no a una como en equals()."""

    def codigo_con_relleno(self, metodo, huecos):
        relleno = ALOAD0 * huecos
        return clase_con_codigo(
            "demands", ALOAD0 + LDC + relleno + b"\xb6" + ref(0) + b"\x57\xb1",
            [metodo])

    def test_registro_lejano_si_cuenta(self):
        d = self.codigo_con_relleno("addImplicitMap", 3)
        self.assertEqual(jarloc.literales_comparados(d), {b"demands"})

    def test_alias_lejano_si_cuenta(self):
        d = self.codigo_con_relleno("aliasField", 3)
        self.assertEqual(jarloc.literales_comparados(d), {b"demands"})

    def test_una_llamada_normal_lejana_no_cuenta(self):
        """Para equals la ventana sigue siendo corta: si esta lejos, el
        literal no es su argumento sino parte de otra expresion."""
        d = self.codigo_con_relleno("equals", 3)
        self.assertEqual(jarloc.literales_comparados(d), set())

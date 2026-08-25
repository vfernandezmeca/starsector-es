"""Lectura y reescritura de literales de texto en class files de Java.

El constant pool mezcla texto visible con nombres de metodos y descriptores.
Reescribir a ciegas renombra metodos y revienta la clase, asi que solo se
considera traducible una entrada Utf8 que unicamente alimente a CONSTANT_String.
"""
import re
import struct

MAGIA = b"\xca\xfe\xba\xbe"

# tag -> bytes que ocupa la entrada sin contar el tag
FIJO = {3: 4, 4: 4, 5: 8, 6: 8, 7: 2, 8: 2, 9: 4, 10: 4, 11: 4,
        12: 4, 15: 3, 16: 2, 17: 4, 18: 4, 19: 2, 20: 2}
DOBLE = {5, 6}          # Long y Double ocupan dos huecos
LITERAL = 8             # CONSTANT_String


def _pool(data):
    """Devuelve (utf8, literales, usados, fin).

    utf8:      indice -> (inicio, fin) del texto crudo dentro de data
    literales: indices Utf8 a los que apunta algun CONSTANT_String
    usados:    indices Utf8 a los que apunta cualquier otra cosa
    fin:       offset donde acaba el constant pool
    """
    if data[:4] != MAGIA:
        raise ValueError("no es un class file")
    total = struct.unpack(">H", data[8:10])[0]
    p, i = 10, 1
    utf8, literales, usados = {}, set(), set()
    while i < total:
        tag = data[p]
        if tag == 1:
            n = struct.unpack(">H", data[p + 1:p + 3])[0]
            utf8[i] = (p + 3, p + 3 + n)
            p += 3 + n
        elif tag in FIJO:
            destino = literales if tag == LITERAL else usados
            if tag in (7, 8, 16, 19, 20):
                destino.add(struct.unpack(">H", data[p + 1:p + 3])[0])
            elif tag == 12:                       # NameAndType: nombre y tipo
                a, b = struct.unpack(">HH", data[p + 1:p + 5])
                usados.update((a, b))
            p += 1 + FIJO[tag]
        else:
            raise ValueError("tag desconocido %d" % tag)
        i += 2 if tag in DOBLE else 1
    return utf8, literales, usados, p


def _nombres(data, p, utf8):
    """Indices Utf8 usados como nombre o descriptor fuera del constant pool.

    Recorre interfaces, campos, metodos y atributos. Devuelve tambien el
    offset final: si no coincide con el tamano del fichero, la clase esta
    mal formada y no hay que tocarla.
    """
    usados = set()

    def atributos(p, cuantos):
        for _ in range(cuantos):
            usados.add(struct.unpack(">H", data[p:p + 2])[0])
            largo = struct.unpack(">I", data[p + 2:p + 6])[0]
            p += 6 + largo
        return p

    p += 6                                        # access, this_class, super
    p += 2 + 2 * struct.unpack(">H", data[p:p + 2])[0]        # interfaces
    for _ in range(2):                            # campos y luego metodos
        cuantos = struct.unpack(">H", data[p:p + 2])[0]
        p += 2
        for _ in range(cuantos):
            nombre, tipo = struct.unpack(">HH", data[p + 2:p + 6])
            usados.update((nombre, tipo))
            p = atributos(p + 8, struct.unpack(">H", data[p + 6:p + 8])[0])
    p = atributos(p + 2, struct.unpack(">H", data[p:p + 2])[0])
    return usados, p


IDENT = re.compile(rb"^[A-Za-z][A-Za-z0-9_]*$")


def es_enum(data):
    """True si la clase extiende java/lang/Enum."""
    ent = _refs(data)
    p = _pool(data)[3]
    super_idx = struct.unpack(">H", data[p + 4:p + 6])[0]
    cls = ent.get(super_idx)
    if not cls or cls[0] != "cls":
        return False
    return ent.get(cls[1], ("", b""))[1] == b"java/lang/Enum"


def _analiza(data):
    utf8, literales, usados, p = _pool(data)
    fuera, fin = _nombres(data, p, utf8)
    if fin != len(data):
        raise ValueError("class mal formado: sobran %d bytes" % (len(data) - fin))
    seguros = literales - usados - fuera
    if es_enum(data):
        # En un enum el nombre de la constante es un literal: new T("MISSILE", 0).
        # El nombre del campo Java esta ofuscado, asi que no lo delata; lo que
        # lo delata es la forma. El texto con espacios o simbolos si es texto.
        seguros = {i for i in seguros if not IDENT.match(data[slice(*utf8[i])])}
    return utf8, seguros


def literales(data):
    """Textos traducibles con seguridad de esta clase."""
    utf8, seguros = _analiza(data)
    return {data[a:b] for i, (a, b) in utf8.items() if i in seguros}


def reescribe(data, mapa):
    """Sustituye literales segun mapa (bytes -> bytes). Ignora los inseguros."""
    utf8, seguros = _analiza(data)
    cambios = sorted((utf8[i] for i in seguros if data[slice(*utf8[i])] in mapa),
                     reverse=True)
    out = bytearray(data)
    for a, b in cambios:
        nuevo = mapa[bytes(data[a:b])]
        out[a - 2:b] = struct.pack(">H", len(nuevo)) + nuevo
    fuera = bytes(out)
    _analiza(fuera)                               # el resultado debe seguir parseando
    return fuera


# --- deteccion de texto que en realidad es material de clave -----------------
# El juego deriva el serial recorriendo caracter a caracter una frase larga
# escondida en campaign/accidents. Si se traduce, los codigos legitimos dejan
# de validar. El patron general: un literal se carga con ldc y acto seguido se
# indexa. Eso no es texto de pantalla, es un dato.

LDC, LDC_W, INVOKEVIRTUAL = 0x12, 0x13, 0xb6
INDEXAR = (b"charAt", b"codePointAt")
VENTANA = 60          # bytes de margen entre cargar el literal e indexarlo


def _refs(data):
    """Constant pool completo: indice -> (tipo, valor)."""
    n = struct.unpack(">H", data[8:10])[0]
    p, i, ent = 10, 1, {}
    while i < n:
        tag = data[p]
        if tag == 1:
            ln = struct.unpack(">H", data[p + 1:p + 3])[0]
            ent[i] = ("utf8", data[p + 3:p + 3 + ln]); p += 3 + ln
        elif tag == 8:
            ent[i] = ("str", struct.unpack(">H", data[p + 1:p + 3])[0]); p += 3
        elif tag == 12:
            ent[i] = ("nat", struct.unpack(">HH", data[p + 1:p + 5])); p += 5
        elif tag in (9, 10, 11):
            ent[i] = ("ref", struct.unpack(">HH", data[p + 1:p + 5])); p += 5
        elif tag == 7:
            ent[i] = ("cls", struct.unpack(">H", data[p + 1:p + 3])[0]); p += 3
        elif tag in FIJO:
            p += 1 + FIJO[tag]
        else:
            raise ValueError("tag desconocido %d" % tag)
        i += 2 if tag in DOBLE else 1
    return ent


def es_material_de_clave(data, textos):
    """True si alguno de textos se carga como literal y luego se indexa."""
    if not textos:
        return False
    ent = _refs(data)
    literales_idx = {i for i, (t, v) in ent.items()
                     if t == "str" and ent.get(v, ("", b""))[1] in textos}
    if not literales_idx:
        return False
    indexadores = set()
    for i, (t, v) in ent.items():
        if t != "ref":
            continue
        nat = ent.get(v[1])
        if nat and nat[0] == "nat" and ent.get(nat[1][0], ("", b""))[1] in INDEXAR:
            indexadores.add(i)
    if not indexadores:
        return False
    for j in range(len(data) - 3):
        if data[j] == LDC and data[j + 1] in literales_idx:
            ancho = 2
        elif data[j] == LDC_W and struct.unpack(">H", data[j + 1:j + 3])[0] in literales_idx:
            ancho = 3
        else:
            continue
        trozo = data[j + ancho:j + ancho + VENTANA]
        for k in range(len(trozo) - 2):
            if (trozo[k] == INVOKEVIRTUAL
                    and struct.unpack(">H", trozo[k + 1:k + 3])[0] in indexadores):
                return True
    return False


# --- deteccion de literales usados como clave de comparacion ----------------
# Una palabra suelta ("Missile", "Assault") puede ser texto de pantalla o un
# identificador. La diferencia esta en como la usa el codigo: si la compara,
# es una clave y traducirla rompe la comparacion. Si solo la pasa a la
# interfaz, es texto.

COMPARA = {b"equals", b"equalsIgnoreCase", b"compareTo", b"compareToIgnoreCase",
           b"contentEquals", b"startsWith", b"endsWith", b"contains",
           b"get", b"containsKey", b"remove", b"matches", b"put",
           # XStream: el alias es el nombre del elemento en el XML del
           # guardado. Traducirlo hace que las partidas viejas no carguen.
           b"alias", b"aliasType", b"aliasField", b"aliasAttribute",
           b"aliasSystemAttribute", b"omitField", b"useAttributeFor",
           b"addImplicitCollection", b"registerLocalConverter"}
INVOCAR = (0xb6, 0xb7, 0xb8, 0xb9)      # invokevirtual/special/static/interface
CERCA = 12                              # bytes entre el literal y la llamada


def _metodos_por_indice(ent):
    """indice de Methodref -> nombre del metodo."""
    out = {}
    for i, (t, v) in ent.items():
        if t != "ref":
            continue
        nat = ent.get(v[1])
        if nat and nat[0] == "nat":
            out[i] = ent.get(nat[1][0], ("", b""))[1]
    return out


# --- decodificacion de instrucciones ----------------------------------------
# Escanear bytes crudos confunde operandos con opcodes y da falsos positivos:
# addPara("Top speed: " + x.getSpeed()) parecia una busqueda por id y dejaba
# el texto sin traducir. Hay que recorrer el codigo instruccion a instruccion.

LARGO = {}
for _op in range(0x100):
    LARGO[_op] = 1
for _op in (0x10, 0x12, 0x15, 0x16, 0x17, 0x18, 0x19, 0x36, 0x37, 0x38, 0x39,
            0x3a, 0xa9, 0xbc):
    LARGO[_op] = 2
for _op in (0x11, 0x13, 0x14, 0x84, 0xbb, 0xbd, 0xc0, 0xc1, 0xc6, 0xc7,
            0xb2, 0xb3, 0xb4, 0xb5, 0xb6, 0xb7, 0xb8):
    LARGO[_op] = 3
for _op in range(0x99, 0xa9):
    LARGO[_op] = 3
LARGO[0xb9] = LARGO[0xba] = 5
LARGO[0xc5] = 4
LARGO[0xc8] = LARGO[0xc9] = 5
CONMUTA = (0xaa, 0xab)      # tableswitch y lookupswitch: largo variable
ANCHO = 0xc4                # wide


def _instrucciones(code):
    """(opcode, operando) de cada instruccion del cuerpo de un metodo."""
    p, n = 0, len(code)
    while p < n:
        op = code[p]
        if op in CONMUTA:
            q = p + 1 + ((4 - (p + 1) % 4) % 4)          # relleno a multiplo de 4
            if op == 0xaa:
                bajo, alto = struct.unpack(">ii", code[q + 4:q + 12])
                fin = q + 12 + 4 * (alto - bajo + 1)
            else:
                pares = struct.unpack(">i", code[q + 4:q + 8])[0]
                fin = q + 8 + 8 * pares
            yield op, b""
            p = fin
            continue
        if op == ANCHO:
            largo = 6 if code[p + 1] == 0x84 else 4
        else:
            largo = LARGO[op]
        yield op, code[p + 1:p + largo]
        p += largo


def _codigos(data):
    """Cuerpo de cada metodo de la clase."""
    utf8, _, _, p = _pool(data)
    ent = _refs(data)
    nombre = {i: ent[i][1] for i in ent if ent[i][0] == "utf8"}
    out = []

    def attrs(p, cuantos, recoge):
        for _ in range(cuantos):
            idx = struct.unpack(">H", data[p:p + 2])[0]
            largo = struct.unpack(">I", data[p + 2:p + 6])[0]
            cuerpo = data[p + 6:p + 6 + largo]
            if recoge and nombre.get(idx) == b"Code":
                n = struct.unpack(">I", cuerpo[4:8])[0]
                out.append(cuerpo[8:8 + n])
            p += 6 + largo
        return p

    p += 6
    p += 2 + 2 * struct.unpack(">H", data[p:p + 2])[0]
    for es_metodo in (False, True):
        cuantos = struct.unpack(">H", data[p:p + 2])[0]
        p += 2
        for _ in range(cuantos):
            p = attrs(p + 8, struct.unpack(">H", data[p + 6:p + 8])[0], es_metodo)
    return out


CERCANIA = 2        # instrucciones entre cargar el literal y usarlo
# Los metodos de registro llevan varios argumentos, asi que el literal queda
# mas lejos de la llamada: addImplicitMap(cls, "demands", "key", Tipo.class).
REGISTRA = (b"alias", b"addImplicit", b"omitField", b"useAttributeFor",
            b"registerLocalConverter")
CERCANIA_REGISTRO = 6


def literales_comparados(data):
    """Literales de esta clase que el codigo usa para comparar, no para mostrar."""
    ent = _refs(data)
    texto = {i: ent[v][1] for i, (t, v) in ent.items()
             if t == "str" and v in ent and ent[v][0] == "utf8"}
    if not texto:
        return set()
    # Con la decodificacion instruccion a instruccion, get* vuelve a ser
    # fiable: solo cuenta si la llamada va pegada al literal, no si aparece
    # cerca por casualidad dentro de una concatenacion.
    comparadores = {i for i, n in _metodos_por_indice(ent).items()
                    if n in COMPARA or n.startswith((b"get", b"opt", b"has"))}
    registro = {i for i, n in _metodos_por_indice(ent).items()
                if n.startswith(REGISTRA)}
    comparadores |= registro
    if not comparadores:
        return set()
    fuera = set()
    for code in _codigos(data):
        try:
            seq = list(_instrucciones(code))
        except Exception:
            continue
        for i, (op, arg) in enumerate(seq):
            if op == LDC and arg and arg[0] in texto:
                lit = texto[arg[0]]
            elif op == LDC_W and len(arg) >= 2 and struct.unpack(">H", arg[:2])[0] in texto:
                lit = texto[struct.unpack(">H", arg[:2])[0]]
            else:
                continue
            # el literal es receptor o argumento: la llamada va detras
            for salto, (op2, arg2) in enumerate(
                    seq[i + 1:i + 1 + CERCANIA_REGISTRO], start=1):
                if op2 not in INVOCAR or len(arg2) < 2:
                    continue
                destino = struct.unpack(">H", arg2[:2])[0]
                if destino in registro or (destino in comparadores
                                           and salto <= CERCANIA):
                    fuera.add(lit)
                break        # la primera llamada es la que consume el literal
    return fuera

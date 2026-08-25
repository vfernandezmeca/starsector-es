#!/usr/bin/env python3
"""Traduce lotes con un modelo local via Ollama.

Los tokens locales son gratis, asi que aqui se puede ser estricto: cada trozo
se valida y se reintenta hasta que pasa. Eso es lo contrario de lo que se
podia hacer con agentes de pago, donde repetir un lote costaba ~200K tokens.

Uso:
    python3 tools/local.py 006 008 009        # lotes concretos
    python3 tools/local.py --faltan           # todos los que falten
    python3 tools/local.py --faltan --modelo qwen3:32b
"""
import json, os, re, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import batch as B

API = "http://127.0.0.1:11434/api/chat"
MODELO = "gemma4:26b"   # medido contra gemma3:27b: 0 Title Case (vs 6) y 132 c/s (vs 72)
TROZO = 7000        # chars de TEXTO por peticion
BLOQUES_MAX = 60    # tope de bloques: con cadenas cortas, 355 ids ahogan al
                    # modelo y deja de traducir para ponerse a describir        # chars por peticion. El glosario (13 KB) se procesa una
                    # vez por peticion: trozos grandes lo amortizan mejor.
REINTENTOS = 4

GLOSARIO = open(os.path.join(ROOT, "GLOSARIO.md"), encoding="utf-8").read()
CONTEXTO = open(os.path.join(ROOT, "CONTEXTO.md"), encoding="utf-8").read()

SISTEMA = """Eres traductor profesional de videojuegos. Traduces del inglés al \
español de España el juego de ciencia ficción espacial Starsector.

Primero, de qué va el juego (para que entiendas quién habla y por qué):

""" + CONTEXTO + """

Y este glosario es VINCULANTE. Respétalo aunque una frase suelta suene mejor de \
otra forma: la coherencia entre miles de textos importa más.

""" + GLOSARIO + """

CONTEXTO:
Cada bloque trae, tras el id, una etiqueta que dice QUÉ es esa cadena. Úsala:
cambia el registro y hasta el modo verbal.

- "opcion que ELIGE EL JUGADOR": es lo que el jugador dice o hace. Si habla,
  aplica tú/usted según a quién se dirige. Si es una acción (marcharse,
  atacar), va en infinitivo: "Marcharse", "Pedir más créditos".
- "narracion o dialogo de un PNJ": el jugador lee esto. La narración en
  segunda persona va en tú.
- "etiqueta corta": tiene hueco fijo en pantalla. Busca la forma más breve.
- "NOMBRE PROPIO de una nave": normalmente NO se traduce.
- "CLASE de nave": es nombre común, sí se traduce (destructor, fragata).
- "[regla: xxx]": el id interno. Suele delatar la facción o la misión
  (lke_ = Luddic, ga = Academia de Galatia, pirate/smug = piratas y
  contrabandistas). Úsalo para acertar el tú/usted.

FORMATO DE SALIDA (crítico):
La entrada son bloques así:
###ID a1b2c3d4e5f6 | etiqueta de contexto
texto en inglés
###ID 998877665544
otro texto

Devuelve EXACTAMENTE los mismos ###ID, en el mismo orden, cada uno seguido de \
su traducción al español. En la salida basta con "###ID <id>", sin la etiqueta. Sin comentarios, sin encabezados, sin ```. Empieza \
directamente por "###ID ".

REGLAS QUE ROMPEN EL JUEGO:
- Los tokens $loQueSea se copian literales, misma capitalización, sin traducir.
  $Market y $market son distintos. No inventes tokens nuevos.
- Mismo número de saltos de línea que el original en cada bloque.
- [corchetes], {llaves}, %s, %d: literales.
- Nunca dejes un bloque vacío.

ERRORES QUE MÁS SE CUELAN:
- Title Case inglés. "Informe de Noticias" está MAL, es "Informe de noticias".
  En español solo va mayúscula la primera palabra y los nombres propios.
- Calcos: "resultando en", "puede ser cargado", "muy lejos por debajo".
  La pasiva inglesa se vuelve pasiva refleja con "se".
- Palabras inventadas. Si no sabes un término, usa una perífrasis clara.
- $hisOrHer sale como "su", que es SINGULAR. Detrás de él el sustantivo va en
  singular: "$HisOrHer mirada", nunca "$HisOrHer ojos" (daría "su ojos").
  Si necesitas plural, quita el token: "le temblaban las manos"."""


def pide(mensajes, modelo, temp=0.2):
    datos = json.dumps({
        "model": modelo, "messages": mensajes, "stream": False,
        "keep_alive": "2h",
        # Gemma 4 y otros razonadores gastan TODO el presupuesto pensando y
        # devuelven contenido vacio. Aqui no hay nada que razonar: se traduce.
        "think": False,
        "options": {"temperature": temp, "num_ctx": 24576,
                    "num_batch": 512, "num_predict": 8192},
    }).encode()
    req = urllib.request.Request(API, datos, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        return json.load(r)["message"]["content"]


def limpia(t):
    """Quita vallas de codigo y texto previo al primer ###ID."""
    t = re.sub(r"^```[a-z]*\n?|```$", "", t.strip(), flags=re.M)
    i = t.find("###ID ")
    return t[i:] if i > 0 else t


def parsea(t):
    out, cur, buf = {}, None, []
    for ln in t.split("\n"):
        if ln.startswith("###ID "):
            if cur:
                out[cur] = "\n".join(buf).rstrip("\n")
            cur, buf = ln[6:].strip().split()[0], []
        elif ln.strip() == "###END":
            break
        elif cur is not None:
            buf.append(ln)
    if cur:
        out[cur] = "\n".join(buf).rstrip("\n")
    return out


def rescata_ids(esperados, devueltos):
    """Empareja ids que el modelo copio mal por un caracter.

    Los ids son hashes de 12 digitos hexadecimales y a los modelos se les da
    fatal copiarlos: se comen o cambian un caracter ("ac516505ad72" ->
    "ac51650ad72"). La traduccion venia perfecta y se tiraba entera por eso.

    Solo se acepta si la correccion es INEQUIVOCA: un unico candidato a
    distancia 1. Si hay dos, se descarta, que confundir bloques es peor.
    """
    fuera = [k for k in devueltos if k not in esperados]
    if not fuera:
        return devueltos
    libres = [k for k in esperados if k not in devueltos]
    salida = dict(devueltos)
    for malo in fuera:
        cand = [b for b in libres if cerca(malo, b)]
        if len(cand) == 1:
            salida[cand[0]] = salida.pop(malo)
            libres.remove(cand[0])
    return salida


def cerca(a, b):
    """True si a y b difieren en un solo caracter (insercion, borrado o cambio)."""
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    corto, largo = (a, b) if len(a) < len(b) else (b, a)
    for i in range(len(largo)):
        if largo[:i] + largo[i + 1:] == corto:
            return True
    return False


def valida(orig, trad):
    """Devuelve lista de ids malos."""
    malos = []
    for k, s in orig.items():
        v = trad.get(k)
        if v is None or not v.strip():
            malos.append(k)
        elif not B.token_ok(s, v):
            malos.append(k)
        elif s.count("\n") != v.count("\n"):
            malos.append(k)
    return malos


def traduce_trozo(trozo, modelo, ctx=None, cabecera=""):
    ctx = ctx or {}
    def bloque(d):
        # solo el id de regla por linea; la etiqueta larga va en la cabecera
        cuerpo = "".join(
            f"###ID {k}{' [' + ctx[k] + ']' if ctx.get(k) else ''}\n{v}\n"
            for k, v in d.items())
        return (f"CONTEXTO: {cabecera}\n\n{cuerpo}" if cabecera else cuerpo)
    texto = bloque(trozo)
    msgs = [{"role": "system", "content": SISTEMA},
            {"role": "user", "content": texto}]
    mejor, mejor_malos = {}, list(trozo)
    for intento in range(REINTENTOS):
        try:
            r = rescata_ids(set(trozo), parsea(limpia(pide(
                msgs, modelo, temp=0.2 + 0.1 * intento))))
        except Exception as e:
            pass  # reintento silencioso; el fallo se refleja en la barra
            time.sleep(2)
            continue
        malos = valida(trozo, r)
        # quedarse con lo mejor visto hasta ahora
        for k in trozo:
            if k not in malos and k in r:
                mejor[k] = r[k]
        mejor_malos = [k for k in trozo if k not in mejor]
        if not mejor_malos:
            return mejor, []
        # reintentar solo lo que fallo
        pend = {k: trozo[k] for k in mejor_malos}
        texto = bloque(pend)
        msgs = [{"role": "system", "content": SISTEMA},
                {"role": "user", "content": texto}]
        pass  # el recuento de fallos ya sale en la barra
    return mejor, mejor_malos


def barra(hecho, total, t0, lote, i, n, fallidos):
    """Una linea que se reescribe: progreso global, velocidad y ETA."""
    frac = hecho / total if total else 1
    ancho = 28
    lleno = int(ancho * frac)
    dt = time.time() - t0
    vel = hecho / dt if dt > 0 else 0
    queda = (total - hecho) / vel if vel > 0 else 0
    h, m = int(queda // 3600), int(queda % 3600 // 60)
    sys.stdout.write(
        f"\r[{'#' * lleno}{'.' * (ancho - lleno)}] {frac*100:5.1f}%  "
        f"lote {lote} ({i}/{n})  {hecho:,}/{total:,} chars  "
        f"{vel:.0f} c/s  faltan {h}h{m:02d}m  fallos {fallidos}   ")
    sys.stdout.flush()


def haz_lote(num, modelo, prog=None):
    ent = os.path.join(ROOT, "work", "batches", f"{num}.txt")
    sal = os.path.join(ROOT, "work", "out", f"{num}.txt")
    if not os.path.exists(ent):
        print(f"{num}: no existe el lote"); return
    orig = B.parse(ent)
    etiqueta, regla = {}, {}
    for ln in open(ent, encoding="utf-8"):
        if ln.startswith("###ID ") and "|" in ln:
            i, _, c = ln[6:].partition("|")
            c = c.strip()
            # separar la etiqueta general del id de regla, que si varia
            base, _, r = c.partition("[regla:")
            etiqueta[i.strip()] = base.strip()
            regla[i.strip()] = ("regla: " + r.strip(" ]")) if r else ""
    # agrupar por etiqueta: asi se dice una sola vez por peticion
    grupos = {}
    for k in orig:
        grupos.setdefault(etiqueta.get(k, ""), []).append(k)
    trozos = []
    for etq, ks in grupos.items():
        cur, n = {}, 0
        for k in ks:
            if cur and (n + len(orig[k]) > TROZO or len(cur) >= BLOQUES_MAX):
                trozos.append((etq, cur)); cur, n = {}, 0
            cur[k] = orig[k]; n += len(orig[k])
        if cur:
            trozos.append((etq, cur))
    t0 = time.time()
    todo, fallidos = {}, []
    for i, (etq, tz) in enumerate(trozos, 1):
        r, malos = traduce_trozo(tz, modelo, regla, etq)
        todo.update(r); fallidos += malos
        if prog:
            prog["hecho"] += sum(len(v) for v in tz.values())
            barra(prog["hecho"], prog["total"], prog["t0"], num, i, len(trozos),
                  prog["fallos"] + len(fallidos))
    if prog:
        prog["fallos"] += len(fallidos)
    for k in fallidos:
        todo[k] = orig[k]
    with open(sal, "w", encoding="utf-8") as f:
        for k in orig:
            f.write(f"###ID {k}\n{todo[k]}\n")
        f.write("###END\n")
    print(f"\n{num}: listo en {time.time()-t0:.0f}s, {len(orig)} bloques, "
          f"{len(fallidos)} sin traducir", flush=True)


def main():
    args = sys.argv[1:]
    modelo = MODELO
    if "--modelo" in args:
        i = args.index("--modelo"); modelo = args[i+1]; del args[i:i+2]
    if "--faltan" in args:
        hechos = {f[:3] for f in os.listdir(os.path.join(ROOT, "work", "out"))
                  if f.endswith(".txt")}
        # enumerar los lotes que existen de verdad; su numero cambia cada vez
        # que se regeneran (el troceo depende del texto pendiente)
        todos = sorted(f[:-4] for f in os.listdir(os.path.join(ROOT, "work", "batches"))
                       if f.endswith(".txt"))
        args = [n for n in todos if n not in hechos]
    if not args:
        print(__doc__); return
    total = 0
    for n in args:
        p = os.path.join(ROOT, "work", "batches", f"{n}.txt")
        if os.path.exists(p):
            total += sum(len(v) for v in B.parse(p).values())
    print(f"modelo: {modelo}")
    print(f"lotes:  {len(args)}  ({' '.join(args)})")
    print(f"texto:  {total:,} caracteres\n")
    prog = {"hecho": 0, "total": total, "t0": time.time(), "fallos": 0}
    mayus = "--mayusculas" in sys.argv   # gemma4 no lo necesita; gemma3 si
    for n in args:
        haz_lote(n, modelo, prog)
        if mayus:
            repasa_mayusculas(n, modelo)
    dt = time.time() - prog["t0"]
    print(f"\nTERMINADO: {total:,} chars en {dt/3600:.1f}h "
          f"({total/dt:.0f} c/s), {prog['fallos']} bloques sin traducir")


if __name__ == "__main__":
    main()

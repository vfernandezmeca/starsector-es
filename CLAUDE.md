# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Idioma: el repo esta escrito en espanol (codigo, comentarios, identificadores,
docs). Sigue esa convencion.

## Que es esto

Traduccion al espanol de Starsector 0.98a-RC8. No es una app: es una **tuberia
de traduccion** en Python que produce dos artefactos independientes:

- **El mod** (`mod/` -> `dist/`): traduce lo que sale de `data/`. Se activa en
  el launcher, no toca el juego.
- **El parche de menus** (`tools/parchea.py`, `java/Parchear.java`): reescribe
  literales dentro de `starfarer_obf.jar` y `starfarer.api.jar`. Es la unica
  via para menus y paneles; un mod no llega ahi (los menus ya los cargo el
  classloader padre). Reversible via copias `.orig`.

## Comandos

```bash
python3 -m unittest discover -s tests              # 80 tests
python3 -m unittest tests.test_jarloc -v           # un modulo
python3 -m unittest tests.test_jarloc.TestReescribe.test_x   # un test

# ciclo completo (el orden importa)
python3 tools/ssloc.py extract      # datos -> work/catalog.jsonl (SOBRESCRIBE)
python3 tools/jar_extrae.py         # jars -> anade al catalogo (siempre DESPUES)
python3 tools/batch.py make         # catalogo -> work/batches/NNN.txt
python3 tools/local.py --faltan     # Ollama (gemma4:26b) -> work/out/NNN.txt
python3 tools/batch.py collect      # valida -> work/trans.jsonl
cp work/trans.jsonl work/hecho.jsonl          # promociona lo aceptado
python3 tools/ssloc.py inject --sin-acentos   # el flag es OBLIGATORIO
python3 tools/audit.py                        # nunca saltarselo
python3 tools/parchea.py                      # parchea los jars (desde .orig)
python3 tools/verifica_jar.py                 # ni esto
python3 tools/package.py                      # dist/Starsector Espanol/

# publicar
python3 tools/plan.py                         # -> work/plan.txt (Linux)
STARSECTOR=~/Games/starsector-win python3 tools/plan.py work/plan-windows.txt
cd java && javac --release 8 -d clases Parchear.java \
  && jar cfm parchear.jar manifest.txt -C clases . && cd ..
python3 tools/release.py                      # -> dist/*.zip

python3 tools/parchea.py --restaura           # deshacer el parche
```

Ruta del juego: `/home/victor/Games/starsector`, **hardcodeada** en
`ssloc.py`, `audit.py`, `package.py`, `barrido.py`, `measure.py`, `analyze*.py`.
Solo `parchea.py`, `jar_extrae.py` y `verifica_jar.py` respetan `$STARSECTOR`.

## Flujo de datos

`work/catalog.jsonl` — una linea por cadena unica: `k` (hash id), `s` (ingles),
`ctx` (`ruta#columna`), `h` (id de fila). Es la entrada de todo.

`work/trans.jsonl` — traducciones **con tildes**, salida de `batch.py collect`.
`work/hecho.jsonl` — lo promocionado a mano; `batch.py make` lo resta del
catalogo para no re-traducir y `collect` lo re-inyecta como base. Ambos van al
repo; el resto de `work/` esta en `.gitignore`.

El texto acentuado vive solo en esos jsonl: `inject --sin-acentos` lo pasa a
ASCII porque Starsector no carga fuentes de mods y cualquier tilde sale rota.
Si algun dia se arregla, se recupera ejecutando `inject` sin el flag.

`mod/` es **generado** por `inject` pero esta versionado. `mod-src/` es lo unico
escrito a mano (`EspanolTokens.java`, `EspanolModPlugin.java`, que resuelven
`$heOrShe` y compania). `package.py` fusiona los dos en `dist/`.

## Lo dificil: saber que NO traducir

Traducir un identificador no da un error de traduccion: el juego no arranca, o
falla en silencio. `ESTADO.md` documenta 7 roturas del parche y 4 del mod, cada
una convertida en un invariante automatico. Leelo antes de tocar el detector.

- La lista de intocables (21.009 cadenas) se **deriva** de seis evidencias del
  propio juego (bytecode, enums, claves JSON/columnas CSV, rutas, columnas `id`,
  cadenas indexadas con `charAt`). No se escribe a mano.
- **La decision es global, no por clase**: un identificador se registra en una
  clase y se consulta en otra. Decidir por clase las desincroniza (crash real).
- `tools/jarloc.py` es el nucleo: lee y reescribe el constant pool. Solo se
  considera traducible una entrada Utf8 que **unicamente** alimente a
  `CONSTANT_String`.
- `audit.py` y `verifica_jar.py` no son formalidad: cada comprobacion viene de
  un crash. `verifica_jar.py` corre contra la instalacion real y las partidas
  guardadas.
- La ida y vuelta con traduccion identidad no basta como prueba (748/748
  archivos identicos y el juego petaba igual).

## Distribucion partida en dos

El analisis no viaja. `tools/plan.py` hace todo el trabajo aqui y congela
`work/plan.txt` con **indices de constant pool**, no texto a buscar.
`java/Parchear.java` (Java 8, sin dependencias, corre con la JRE del juego)
solo aplica el plan. Si cambias el detector, revalida comparando su salida con
`parchea.py` entrada por entrada (6.468 identicas la ultima vez).

El `.jar` parcheado no se redistribuye: se reparte el parcheador y el plan.

**Un plan por build.** `starfarer_obf.jar` viene con una ofuscacion distinta
en cada sistema: entre Linux y Windows hay 1.221 clases renombradas y 1.267
mas con otro contenido. `starfarer.api.jar` en cambio es identico. Por eso se
publican `plan.txt` y `plan-windows.txt`, y quien elige es el jar, no el
sistema operativo: `Parchear` carga todos los `plan*.txt` que encuentre y se
queda con el que mas clases suyas ve dentro (en empate, `plan.txt`).

El plan lleva el texto original ademas del indice, y no se escribe donde no
coincida. Sin eso, un jar de otro build hace que el indice apunte a un nombre
de metodo: no da error, deja el juego colgado en el launcher.

## Traducir texto

`GLOSARIO.md` es vinculante (terminologia, tu/usted por faccion, calcos
prohibidos, genero neutro para el jugador). `CONTEXTO.md` da el tono y quien
habla. `work/INSTRUCCIONES.md` es el prompt del traductor.

Reglas que rompen el juego al traducir: tokens `$loQueSea` copiados literales
con su capitalizacion, mismo numero de saltos de linea, `%s`/`[]`/`{}` intactos,
nunca un bloque vacio. `batch.py collect` valida todo eso y descarta lo que
falle; `qa.py` e `ingles.py` informan sin rechazar.

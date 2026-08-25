<p align="center"><img src="logo.jpg" width="280" alt="Starsector en Español"></p>

# Starsector en Español

Traducción al español (España) de Starsector 0.98a-RC8.

**Descargar: [última versión](https://github.com/vfernandezmeca/starsector-es/releases/latest)** — un zip que se arrastra a `mods/`.

Son **dos piezas independientes**:

| | Qué traduce | Cómo |
|---|---|---|
| **El mod** | Todo lo que sale de archivos de datos: diálogos, misiones, naves, armas, mods de casco, habilidades, industrias, códex | Mod normal, se activa en el launcher |
| **El parche de menús** | Menús, botones, ajustes, avisos y paneles de flota y colonia | Reescribe literales dentro de los `.jar` del juego |

El mod no toca nada del juego. El parche sí, y por eso va aparte: es opcional
y reversible.

## Instalar

**El mod.** Copia la carpeta a `Starsector/mods/`:

```text
Starsector/mods/Starsector Espanol/mod_info.json
Starsector/mods/Starsector Espanol/data/
```

Abre el launcher, entra en `Mods`, activa `Starsector en Español` y arranca.

**El parche** (opcional). Va **dentro de la carpeta del mod**, en
`parche-menus/`, así que se instala en el mismo arrastre. **No hace falta
instalar nada**: usa la Java que ya trae Starsector.

```bash
./parchear.sh              # Linux / Mac, desde parche-menus/
./parchear.sh --restaura

parchear.bat               # Windows: doble clic
parchear.bat --restaura
```

Con el mod ya en `mods/`, el script encuentra el juego solo (tres carpetas
hacia arriba). Desde otro sitio, se le pasa la ruta como argumento.

Que el parcheador viva ahí es comodidad, no que sea parte del mod: el juego
ignora las subcarpetas que no conoce y `parchear.jar` no está en el campo
`jars` del `mod_info.json`, así que ni lo mira.

Guarda una copia `.orig` la primera vez y siempre parte de ella, así que se
puede repetir sin acumular daños. Cada actualización del juego lo borra: se
vuelve a pasar.

Desde el repo, con Python, el equivalente es `tools/parchea.py` — ver
*Cómo está hecho*.

El `.jar` parcheado **no se puede redistribuir** — es el juego de Fractal
Softworks con cambios dentro. Lo que se reparte es el parcheador y el plan,
y cada uno lo aplica sobre su copia.

## Sobre los acentos

El mod va en **ASCII puro**: `Anos` en vez de `Años`. No es una chapuza.
Starsector no carga las fuentes de los mods, así que ningún carácter acentuado
se dibuja: sale un apóstrofo en su lugar. Se comprobó con el mod
[Starsector Português Brasileiro](https://www.nexusmods.com/starsector/mods/154),
publicado y con fuentes parcheadas incluidas: muestra los acentos igual de
rotos ("comunica'es" por "comunicações").

El texto con tildes está guardado en `work/trans.jsonl`. Si algún día se
resuelve, se recupera ejecutando `inject` sin `--sin-acentos`.

## Lo que sigue en inglés, y por qué

Unas pocas palabras se quedan a propósito: **el juego usa la misma cadena como
etiqueta y como identificador interno**. Las más visibles son las pestañas
`Character`, `Fleet`, `Refit` e `Intel`; el bytecode las registra con `addTab`
y las busca con `getTab`, así que traducirlas rompería la navegación.

También queda algún botón que sale de código compilado sin literal que tocar,
como `Leave [Esc]` en ciertos diálogos.

## Cómo está hecho

El texto no se traduce editando archivos a mano.

**Extracción y traducción** (`tools/`):

1. `ssloc.py extract` saca los strings traducibles de los archivos de datos;
   `jar_extrae.py` hace lo propio con los literales de los `.jar`.
   Total: 26.198 cadenas únicas (16.053 de datos, 10.145 de los jar).
2. `batch.py make` los reparte en lotes.
3. `local.py` traduce con un modelo local vía Ollama (`gemma4:26b`), con
   `GLOSARIO.md` y `CONTEXTO.md` como referencia vinculante.
4. `batch.py collect` valida (tokens `$x`, formatos `%s`, espacios, longitud)
   y descarta lo que no pasa.
5. `ssloc.py inject` reconstruye los archivos desde los originales;
   `parchea.py` reescribe los literales dentro de los jar.
6. `package.py` monta el mod en `dist/`, y `release.py` el zip publicable.

**Distribución: el análisis no viaja.** Decidir qué cadena es texto y cuál es
identificador es la parte delicada — seis fuentes de evidencia, siete roturas
y 80 tests. Reimplementar eso en otro lenguaje sería reintroducir los mismos
bugs, así que el reparto está partido en dos:

| | Dónde corre | Qué hace |
|---|---|---|
| `tools/plan.py` (Python) | aquí, una vez | todo el análisis; escribe `work/plan.txt` |
| `java/Parchear.java` | en la máquina del usuario | solo aplica el plan |

`plan.txt` no lleva texto que buscar, lleva **índices del constant pool**:

```text
C	starfarer_obf.jar	com/fs/starfarer/BaseGameState.class
S	186	Bucle principal en
```

El parcheador no decide nada ni puede equivocarse de entrada. Se compila
contra Java 8 para que corra con cualquier JRE que traiga el juego:

```bash
python3 tools/plan.py
cd java && javac --release 8 -d clases Parchear.java \
  && jar cfm parchear.jar manifest.txt -C clases .
```

Se valida comparando su salida con la de `parchea.py` entrada por entrada:
**6.468 entradas byte a byte idénticas**. Es decir, todo lo verificado con las
herramientas de Python sigue valiendo, porque el resultado es el mismo archivo.

## Publicar

```bash
python3 tools/release.py
```

Monta `dist/Starsector-Espanol-<version>.zip` con **solo lo que se usa**, en
una sola carpeta que arrastrar a `mods/`:

```text
Starsector Espanol/
    mod_info.json
    data/
    LEEME.txt
    parche-menus/     parchear.jar, plan.txt, parchear.sh, parchear.bat
```

Falla si falta una pieza en vez de publicar un zip a medias. Zip y no rar:
Windows lo abre sin instalar nada.

**Lo difícil no es traducir: es saber qué NO traducir.** Dentro de los jar
conviven texto de pantalla e identificadores con la misma pinta. Traducir un
identificador no da un error de traducción: el juego no arranca.

La lista de intocables (**21.009 cadenas**) no está escrita a mano. Sale de
seis evidencias del propio juego:

| Fuente | Qué detecta |
|---|---|
| Bytecode: el literal se compara o se pasa a un getter | claves de mapas, ids de pestaña |
| Constantes de enum (clase que extiende `java/lang/Enum`) | `MISSILE`, `GLOW` — el juego los busca con `valueOf` |
| Claves JSON y columnas CSV de los datos | `behavior`, `specClass` |
| Nombres de carpeta, archivo y extensiones | `proj`, `skin` |
| Valores de las columnas `id` y el paquete `ids/` | `synchrotron`, `planetkiller` |
| Cadenas indexadas carácter a carácter | la frase que deriva el número de serie |

La decisión es **global, no por clase**: un identificador se registra en una
clase y se consulta en otra, y las dos tienen que seguir coincidiendo.

## Comprobaciones

```bash
python3 -m unittest discover -s tests   # 80 tests
python3 tools/audit.py                  # estructura de los archivos de datos
python3 tools/verifica_jar.py           # invariantes de los jar parcheados
```

`verifica_jar.py` corre contra la instalación real y las partidas guardadas:

- ninguna clase queda corrupta
- constantes y enums intactos
- los nombres de elemento de las partidas existentes siguen registrados
- ninguna cadena de la lista de intocables ha cambiado
- la clase que deriva el serial no cambia ni un byte

Cada invariante viene de una rotura real encontrada jugando. Ver `ESTADO.md`.

## Créditos y licencia

Traducción: vfernandezmeca. Starsector es de
[Fractal Softworks](https://fractalsoftworks.com/); los textos traducidos
derivan de su contenido y se publican solo como mod de traducción. Las
herramientas (`tools/`, `java/`) se pueden reutilizar libremente.

Se agradecen correcciones: abre un issue indicando la pantalla donde
aparece el texto, o un PR sobre `work/hecho.jsonl`.

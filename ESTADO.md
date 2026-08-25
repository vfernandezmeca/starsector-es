# Estado — Starsector en Espanol

Ultima sesion: 25 ago 2026.

## Donde esta

- Proyecto: `/home/victor/Dev/starsector-es/`
- Juego: `/home/victor/Games/starsector` (Linux: `data/` cuelga de la raiz)
- Mod instalado por symlink en `mods/Starsector Espanol`
- Jars parcheados; copias intactas en `starfarer_obf.jar.orig` y
  `starfarer.api.jar.orig`

## Progreso

| | |
|---|---|
| Catalogo | 26.198 cadenas (16.053 de datos, 10.145 de los jar) |
| Mod | 20.606 aplicadas, 16 sin traducir |
| Jar | 10.754 literales reescritos |
| Lista de intocables | 21.009 cadenas |
| Tests | 80 |
| Auditoria y verificacion | limpias |
| Paquete | `dist/Starsector-Espanol-0.3.0.zip` (1,9 MB) |

El zip lo monta `tools/release.py`: **una sola carpeta** que arrastrar a
`mods/`, con el `LEEME.txt` y `parche-menus/` (parchear.jar, plan.txt y los
dos lanzadores) dentro del propio mod. Los lanzadores encuentran el juego
solos si el mod ya esta instalado. No lleva jars parcheados: no se pueden
redistribuir.

Que el parcheador viva dentro del mod es comodidad: el juego ignora las
subcarpetas que no conoce y `parchear.jar` no esta en `jars` del mod_info.

## Las dos mitades

**El mod** traduce los archivos de datos. Se instala y se desactiva desde el
launcher, no toca el juego.

**El parche** (`tools/parchea.py`) reescribe literales dentro de los `.jar`.
Es lo unico que puede traducir menus, ajustes y paneles. Un mod no llega ahi:
sus clases van en un classloader hijo y los menus ya los cargo el padre.

```bash
python3 tools/parchea.py              # aplica (siempre desde el .orig)
python3 tools/verifica_jar.py         # cinco invariantes
python3 tools/parchea.py --restaura   # vuelve atras
```

## Lo dificil no es traducir: es saber que NO traducir

Dentro de los jar conviven texto de pantalla e identificadores con la misma
pinta. Traducir un identificador no da un error de traduccion: el juego no
arranca, o peor, falla en silencio.

La lista de intocables **no esta escrita a mano**. Sale de seis evidencias del
propio juego, y cada una se anadio despues de una rotura real:

| Fuente | Ejemplo que destapo |
|---|---|
| El bytecode compara el literal o lo pasa a un getter | ids de pestana |
| Cadena indexada caracter a caracter | la frase que deriva el serial |
| Constante de enum (clase que extiende `java/lang/Enum`) | `MISSILE`, `GLOW` |
| Clave JSON o columna CSV de los datos | `behavior`, `specClass` |
| Nombre de carpeta, archivo o extension | `proj`, `skin` |
| Valor de columna `id` y paquete `ids/` | `synchrotron`, `planetkiller` |

**La decision es global, no por clase.** Un identificador se registra en una
clase y se consulta en otra; si se traduce solo donde se detecta, las dos
dejan de coincidir. Ese error de diseno costo un crash entero.

## Los siete fallos del parche, y su patron

Todos la misma forma: **el juego busca una cadena por texto exacto y yo no
sabia que ese sitio existia**. Ninguno se veia sin arrancar el juego.

1. **El numero de serie.** `campaign/accidents/oOOO.class` guarda una parrafada
   de coña sobre pirateria. No es un huevo de pascua: el juego la recorre con
   `charAt` para derivar el serial valido. Traducida, los codigos legitimos
   dejan de validar.
2. **Nombres de enum.** `new MissileType("MISSILE", 0)`. El juego lee
   `"missileType":"MISSILE"` del `.proj` y hace `valueOf`. El ofuscador
   renombra el campo Java pero no puede tocar la cadena, asi que la
   comprobacion "el Utf8 tambien es nombre de campo" no lo detecta.
3. **Alias de XStream.** El guardado usa el alias como nombre de elemento XML.
   Traducir `Hyperspace` hace que las partidas viejas no carguen.
4. **Registro y consulta en clases distintas.** `CampaignState` registra
   `"Campaign State"`, `CombatEngine` lo consulta. Decidir por clase los
   desincronizo. De aqui salio la regla global.
5. **Claves JSON y carpetas.** `proj` es la carpeta `data/weapons/proj`;
   `behavior` y `autocharge` son campos del `.wpn`. La spec salia `null`.
6. **Constantes sin llamada.** `Items.class` tiene `synchrotron` y
   `planetkiller` como `static final String`. No hay ninguna llamada
   alrededor, asi que el bytecode no dice nada: hubo que ir a los datos.
7. **Ventana de deteccion corta.** `addImplicitMap(cls, "demands", ...)` deja
   el literal a cuatro instrucciones de la llamada; la ventana era de dos,
   calibrada para `equals`. Ahora hay dos ventanas.

`verifica_jar.py` es lo que quedo de todo esto. Corre contra la instalacion
real y las partidas guardadas:

```
clases sin corromper
constantes y enums intactos
alias de las partidas guardadas      <- 718 nombres de las partidas reales
identificadores sin traducir
material de clave sin tocar
```

## Los cuatro crashes del mod (anteriores, ya cerrados)

Todos **traducir algo que era codigo, no texto**. Cada uno dejo una
comprobacion en `audit.py`:

1. **`:` en las opciones.** El espanol usa dos puntos donde el ingles pone
   guion; en `rules.csv#options` eso desplaza el campo.
2. **Formato `prioridad:id:texto`.** Partir por el primer `:` metia el id
   dentro del texto. Peor: `audit.py` tenia el MISMO error, asi que se daban
   la razon mutuamente.
3. **Comillas sin escapar en literales Java.**
4. **Valores de enumeracion.** `"type":"GLOW"` traducido a `"RESPLANDOR"`.

## Decidido y cerrado

**Acentos: ASCII puro.** Se probo el mod PT-BR publicado en Nexus, con sus
fuentes parcheadas, y muestra los acentos igual de rotos ("comunica'es").
Starsector carga las fuentes antes de leer los mods. El texto con tildes sigue
en `work/trans.jsonl`; se recupera con `inject` sin `--sin-acentos`.

**Menus: SI se pueden traducir**, pero con un parche al jar, no con un mod.
(La sesion anterior concluyo lo contrario buscando las cadenas mal; estan ahi,
en texto plano, y el jar no esta firmado.)

**Un mod NO puede sustituir clases del juego. Probado, no deducido.** Se monto
un mod de prueba con un jar que traia su propia copia de la clase del menu
principal, con "Continuar" cambiado a "XXX PRUEBA XXX". El log confirma que el
juego leyo el jar ("Preparando la carga del archivo jar [...]"), y el menu
siguio mostrando el texto del juego. Repetido con los jars sin parchear:
salio "Continue". Motivo: los jars de mod van en un URLClassLoader sin
subclasear, con delegacion al padre primero, y el padre solo sobrescribe
loadClass para anadir una lista negra de seguridad antes de llamar a super.
Ademas la reflexion y la escritura de archivos estan prohibidas a los mods,
asi que tampoco valen los atajos. El unico proyecto que si transforma clases
del nucleo (SSME) sustituye al lanzador y arranca el juego el mismo.

**Pestanas `Character`, `Fleet`, `Refit`, `Intel`: se quedan en ingles.** El
bytecode las registra con `addTab` y las busca con `getTab`: etiqueta e id son
el mismo literal. Se verifico que ningun archivo de datos ni las partidas las
usan como id, asi que traducirlas de forma consistente *deberia* funcionar,
pero es un riesgo que no se ha tomado. Decision pendiente del usuario.

**Fuentes borradas del paquete.** Las 8 de `graphics/fonts/` venian del mod
PT-BR, el juego no las usaba, y con ellas desaparece el problema de permisos
para publicar en Nexus. El mod ya solo lleva `data/`.

## Sin verificar

`EspanolTokens.java` — el plugin que traduce `$heOrShe`, `$manOrWoman`, etc.
Hace falta hablar con un PNJ: "El levanta una mano" = funciona;
"He levanta una mano" = el orden de registro va al reves. No rompe nada.

## Como seguir

```bash
cd /home/victor/Dev/starsector-es

# 1. catalogo (el extract del mod SOBRESCRIBE catalog.jsonl: jar_extrae despues)
python3 tools/ssloc.py extract
python3 tools/jar_extrae.py

# 2. traducir lo que falte
python3 tools/batch.py make
python3 tools/local.py --faltan          # gemma4:26b, think:false
python3 tools/batch.py collect
cp work/trans.jsonl work/hecho.jsonl     # promociona lo aceptado

# 3. construir
python3 tools/ssloc.py inject --sin-acentos   # el flag es OBLIGATORIO
python3 tools/audit.py                        # nunca saltarselo
python3 tools/parchea.py
python3 tools/verifica_jar.py                 # ni esto
python3 tools/package.py

# 4. publicar (el parcheador que se reparte es Java, no Python)
python3 tools/plan.py
cd java && javac --release 8 -d clases Parchear.java \
  && jar cfm parchear.jar manifest.txt -C clases . && cd ..
python3 tools/release.py
```

## El parcheador que se distribuye

Python no viaja. El analisis (que es texto y que identificador) se hace aqui
una vez y se congela en `work/plan.txt`, que lleva **indices de constant
pool**, no texto que buscar:

```
C  starfarer_obf.jar  com/fs/starfarer/BaseGameState.class
S  186                Bucle principal en
```

`java/Parchear.java` solo aplica ese plan. Compilado con `--release 8` para
que corra con la JRE que trae el juego (`jre_linux`, `jre`), asi que el
usuario no instala nada.

Se valida comparando su salida con la de `parchea.py` entrada por entrada:
**6.468 entradas byte a byte identicas**. Si algun dia cambia el detector,
repetir esa comparacion es la unica prueba que hace falta.

Si el juego peta: **la linea de `starsector.log` da el valor exacto** que no se
encontro, y eso localiza el fallo en un minuto. Buscar la cadena original con
`jarloc.literales()` sobre el `.orig` dice en que clase vive.

## Lecciones que costaron caro

1. **Si algo falla al 100%, sospecha del arnes, no del modelo.** Gemma 4
   devolvia vacio (razonador gastando el presupuesto pensando; `think:false`),
   el contexto ahogaba la senal (la etiqueta repetida inflaba 6.410 chars a
   47.067) y el rango de lotes estaba escrito a mano.

2. **El validador se equivoco tres veces y el traductor ninguna**: umbral de
   longitud (el espanol es ~25% mas largo), pronombres (el espanol elide el
   sujeto) y `$fwt_itOrThem`.

3. **La ida y vuelta con traduccion identidad no basta**, pero es
   imprescindible. Dio 748/748 archivos identicos y el juego petaba igual. En
   el parche del jar si salvo el pellejo: 39 de 6.387 scripts alterados por
   una identidad, detectados antes de traducir nada.

4. **Un contador no puede contar lo que no ve.** La cobertura decia 99% y era
   mentira: se medi­a contra el mismo catalogo que tenia el agujero. De ahi
   salio `barrido.py`, que recorre `data/` sin usar las listas del proyecto.

5. **Medir antes de aplicar una regla.** Para el ultimo fallo se probaron tres
   reglas: tokens de nombre de fichero (perdia 38 cadenas visibles), palabra
   suelta en clase de carga (perdia 103), y el cruce de las dos (perdia 3). La
   buena exige dos evidencias a la vez.

6. **Nada sustituye a abrir el juego.** Siete fallos del parche, y los siete
   los encontro el usuario jugando. Lo unico que escala es convertir cada uno
   en un invariante automatico.

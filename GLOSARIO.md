# Glosario y guia de estilo — Starsector en Español (España)

Vinculante. Ante duda entre naturalidad y glosario, **gana el glosario**: la
coherencia entre 13.815 strings importa mas que la frase perfecta aislada.

## Registro

Ciencia ficcion sobria, seca, con poso noir. Frases cortas. Nada de epica
grandilocuente ni de coloquialismo moderno. Español de **España**.

- Prohibido: "chevere", "carro" (coche), "computadora" (ordenador), "celular",
  "jalar", "platicar", "ustedes" como plural informal (usar "vosotros").
- Prohibido tambien el calco del ingles: "asumir" por "suponer", "eventualmente"
  por "finalmente", "remover" por "quitar", "aplicar" por "solicitar",
  "soportar" por "admitir/aguantar", "encriptar" por "cifrar".
- Comillas: usar « » solo si el original ya usaba comillas tipograficas;
  si el original usa " normal, mantener " normal.

## Tratamiento: tú vs usted

Depende de **quien habla al jugador**:

- **usted** — militares, autoridades, burocracia, clero y academia:
  Hegemonia, Diktat Sindriano, Liga Perseana, Iglesia Ludica, Academia de
  Galatia, Tri-Tachyon (corporativo), oficiales, administradores, portmasters.
- **tú** — piratas, la Senda Ludica, contrabandistas, mercenarios, chatarreros,
  gente de baja estofa, colegas de confianza y cualquier trato informal.
- Narracion en segunda persona (descripciones de lo que hace el jugador): **tú**.
- Una vez elegido, mantenerlo dentro del mismo string. No mezclar.

## Genero del jugador

El jugador puede ser de cualquier genero. Los tokens `$heOrShe`, `$hisOrHer`,
`$himOrHer` y sus variantes en mayuscula lo resuelven en tiempo de ejecucion.
Por eso **el español debe evitar concordancia de genero referida al jugador**:

- Mal: "Estas seguro?" / "Bienvenido, capitan."
- Bien: "Seguro?" / "Te damos la bienvenida, capitania." o reformular:
  "Bienvenida a bordo." (referido al lugar, no a la persona)
- Recurso habitual: cambiar adjetivo por sustantivo o por perifrasis neutra.
  "Estas listo" -> "Todo en orden?" / "Cuando quieras."
- Si es imposible reformular, usar masculino generico. No inventar "-e"/"-x".

## Facciones y nombres propios

| Ingles | Español |
|---|---|
| Hegemony | Hegemonía |
| Hegemon | Hegemón |
| Tri-Tachyon | Tri-Tachyon *(sin traducir, marca)* |
| Persean League | Liga Perseana |
| Luddic Church | Iglesia Lúdica |
| Luddic Path | Senda Lúdica |
| Pather(s) | sendista(s) |
| Ludd | Ludd *(profeta, sin traducir)* |
| Sindrian Diktat | Diktat Sindriano |
| Knights of Ludd | Caballeros de Ludd |
| Galatia Academy | Academia de Galatia |
| the Domain | el Dominio |
| the Sector | el Sector |
| Remnant(s) | Remanente(s) |
| Persean Sector | Sector Perseano |
| Independent | Independiente |
| Free Port | Puerto Franco |

Nombres de persona, de nave y de sistema estelar **no se traducen**:
Baird, Macario, Kanta, Andrada, Sebestyen, Coureuse, Menes, Elek, Scylla,
Yaribay, Hyder, Virens, Rao, Caden, Galatia, Askonia, Corvus, Magec...

Rangos y cargos si se traducen: Captain -> capitán, Provost -> preboste,
Executor -> ejecutor, Academician -> académico, Excubitor -> excubitor,
administrator -> administrador, portmaster -> capitán de puerto.

## Terminos de juego (obligatorios)

| Ingles | Español |
|---|---|
| flux | flujo |
| hard flux / soft flux | flujo duro / flujo blando |
| flux dissipation | disipación de flujo |
| venting | ventilación |
| ordnance points (OP) | puntos de armamento (PA) |
| hull | casco |
| hullmod | mod de casco |
| armor | blindaje |
| shield | escudo |
| combat readiness (CR) | preparación de combate (PC) |
| deployment points | puntos de despliegue |
| supplies | suministros |
| fuel | combustible |
| crew | tripulación |
| marines | infantes de marina |
| credits | créditos |
| burn level | nivel de propulsión |
| salvage (v/n) | rescatar / rescate |
| derelict | pecio |
| colony | colonia |
| market | mercado |
| commodity | mercancía |
| faction | facción |
| fleet | flota |
| ship | nave |
| frigate / destroyer / cruiser / capital | fragata / destructor / crucero / capital |
| fighter / bomber / interceptor | caza / bombardero / interceptor |
| fighter bay | hangar |
| wing | escuadrón |
| ballistic / energy / missile | balístico / energía / misiles |
| point defense (PD) | defensa de punto (DP) |
| officer | oficial |
| skill / aptitude | habilidad / aptitud |
| story point | punto de historia |
| transponder | transpondedor |
| hyperspace | hiperespacio |
| jump point | punto de salto |
| Gate | Portal *(el de la red del Dominio, en mayúscula)* |
| nanoforge | nanoforja |
| Alpha/Beta/Gamma Core | Núcleo Alfa/Beta/Gamma |
| AI core | núcleo de IA |
| sensor profile / sensor strength | perfil de sensores / potencia de sensores |
| bounty | recompensa |
| contact | contacto |
| stability | estabilidad |
| accessibility | accesibilidad |
| hazard rating | índice de peligrosidad |
| phase (ship/cloak) | fase |
| peak performance time | tiempo de rendimiento máximo |
| malfunction | avería |
| d-mod | mod de daño (d-mod) |
| mothballed | en reserva |
| scuttle | barrenar |
| planetkiller | matamundos |
| slipstream | corriente *(de hiperespacio)* |
| slipsurge | oleada de corriente |
| Battlestation | estación de combate |
| star fortress | fortaleza estelar |
| cryosleep / cryopod | criosueño / criocápsula |
| survey (v/n) | prospectar / prospección |
| decivilized | descivilizado |
| pristine nanoforge | nanoforja intacta |
| corrupted nanoforge | nanoforja corrupta |
| techmining / techminer | tecnominería / tecnominero |
| Go Dark *(habilidad)* | Sigilo |
| Cryosleeper | nave de criosueño |
| spacer | espacial *(sustantivado)* |
| sensor array | matriz de sensores |
| tanker | buque cisterna |
| tithe | diezmo |
| Warlord | señor de la guerra |
| the Threat | la Amenaza |
| datacore | núcleo de datos |
| datapad | datapad *(sin traducir)* |
| comm sniffer | interceptor de comunicaciones |
| sitrep | informe de situación |
| wormhole | agujero de gusano |
| Luddie *(despectivo)* | ludita |
| the Path *(a secas)* | la Senda |
| the Abyss | el Abismo |
| the Fringe | el Confín |
| hypercomm(s) | hipercomunicaciones |
| hyperdrive | hipermotor |
| datavault | bóveda de datos |
| brain-interfacer | interfaz cerebral |
| agrav plate | placa antigravedad |
| Gate Hauler | Transportador del Portal |
| Kanta's Den | el Antro de Kanta |
| sensor package | paquete de sensores |
| Chief High Inspector | inspector jefe superior |
| Grand Star Marshal | Gran Mariscal Estelar |
| Lion / Spider of Sindria | León / Araña de Sindria |
| Gens *(casa)* | gens *(sin traducir)* |
| hypershunt | hiperderivación *("shunt" = derivación de energía)* |
| coronal hypershunt | hiperderivación coronal |
| coronal tap | extractor coronal |
| Heggies *(despectivo)* | Hegemos |
| hivescum *(despectivo)* | escoria de colmena |
| Janus | Janus *(sin traducir)* |
| Gargoyle | Gargoyle *(alias, sin traducir)* |
| hyperwave | hiperonda |
| navarch(ship) | navarca |
| exarch | exarca |
| Sindies *(despectivo)* | sindris |
| ivory torus | toro de marfil |
| Engineering / Tech *(mote)* | Ingeniería / Técnica |

## Reglas mecanicas — romper esto rompe el juego

1. **Tokens `$loQueSea` se copian tal cual**, con la misma capitalizacion y sin
   traducir: `$playerName`, `$heOrShe`, `$HeOrShe`, `$hisOrHer`, `$shipOrFleet`,
   `$faction`, `$market`, `$rank`, `$post`, `$global.jethroName`...
   Un token en mayuscula inicial (`$HeOrShe`) va donde en español toque
   inicio de frase; si no cabe, dejalo donde estaba.
2. **No añadir ni quitar tokens.** Si el original tiene 3, la traduccion tiene 3.
3. **Saltos de linea `\r\n` y `\n` se conservan exactamente**, mismo numero y
   misma posicion relativa entre parrafos.
4. **Corchetes `[algo]`, llaves `{algo}`, `%s`, `%d`**: copiar literal.
5. **Espacios iniciales y finales** del string se conservan.
6. En la columna `options` solo llega ya el texto visible; traducelo entero.
7. Nunca devolver cadena vacia. Si algo no se puede traducir, devuelve el
   original.

## Longitud

Muchos strings son etiquetas de interfaz con hueco fijo. Para strings de
**menos de 40 caracteres**, la traduccion no debe pasar de **+30%** de la
longitud original. Prioriza la forma corta: "Ventilar" antes que
"Ventilación de flujo".

## Mayusculas: español, no ingles

El ingles capitaliza Todas Las Palabras De Un Titulo. **El español no.**
Solo mayuscula en la primera palabra y en los nombres propios.

- Mal: "Canal de Comunicaciones Seguro", "Informe de Noticias",
  "Datos de Prospeccion", "Estacion de Batalla - Alta Tecnologia"
- Bien: "Canal de comunicaciones seguro", "Informe de noticias",
  "Datos de prospeccion", "Estacion de combate - alta tecnologia"

Excepcion: nombres propios y de faccion (Hegemonia, Liga Perseana, Senda
Ludica, Academia de Galatia, Portal).

## Prohibido calcar el ingles

Estos son los errores que mas se cuelan. Reescribe siempre:

| Calco (mal) | Español (bien) |
|---|---|
| "puede ser cargado", "pueden ser cosechados" | "se puede cargar", "se pueden recolectar" |
| "resultando en menos defectos" | "lo que reduce los defectos" |
| "muy lejos por debajo de" | "muy por debajo de" |
| "redundante muchas veces" | "con redundancia multiple" |
| "asalto de tierra" | "asalto terrestre" |
| "efectividad de combate" | "eficacia en combate" |
| "en orden de" | "para" |
| "es capaz de producir" | "produce" |
| "provee", "provisto de" | "proporciona", "dotado de" |
| "terran" | "terrestre" |
| "adicionalmente" | "ademas" |
| "significantemente" | "notablemente", "mucho" |

Regla general: **la pasiva inglesa se vuelve pasiva refleja con "se"**.
El ingles encadena sustantivos; el español usa preposiciones. Si al releer
suena a traduccion, esta mal: reescribe la frase entera desde la idea.

## No inventes palabras

Si no conoces el termino español de algo tecnico, usa una perifrasis
descriptiva. **Nunca** te inventes un compuesto.

- Mal: "criopasculas", "Corrienteimpulso", "antinavales"
- Bien: "criocapsulas", "oleada de corriente", "antinave"

Ante duda entre un neologismo dudoso y una perifrasis clara, gana la
perifrasis.

## Quien habla: opciones de dialogo del jugador

Los textos de la columna `options` son lo que **el jugador dice**, no lo que
le dicen. Sin contexto de interlocutor, la regla es:

- Por defecto **usted** en opciones que suenan a gestion, negocio o tramite
  ("Quisiera hablar de...", "Sobre el contrato...").
- **tú** solo si la propia opcion ya trae marca informal clara (insulto,
  amenaza, jerga, tuteo explicito en el original).
- Las opciones de salir/cancelar van en infinitivo o sustantivo, sin persona:
  "Marcharse", "Dejarlo", "Volver", "Nada mas". Nunca "Se marcha usted".

## Tokens de genero: este mod los traduce

El juego base resuelve estos tokens a **palabras inglesas** ("he", "woman",
"sir"). Este mod incluye un plugin (`EspanolTokens.java`) que los pisa con
valores españoles. Traduce contando con estos valores:

| Token | Sale como |
|---|---|
| `$heOrShe` / `$HeOrShe` | él / ella *(Él / Ella)* |
| `$himOrHer` | él / ella |
| `$hisOrHer` / `$HisOrHer` | **su** *(vale para ambos generos)* |
| `$himOrHerself` | sí mismo / sí misma |
| `$manOrWoman` | hombre / mujer |
| `$brotherOrSister` | hermano / hermana |
| `$sirOrMadam` | señor / señora |
| `$playerSirOrMadam` | señor / señora *(referido al jugador)* |

`$hisOrHer` resuelve a **"su"**, que vale para ambos generos: en español el
posesivo concuerda con lo poseido, no con el poseedor.

**PERO "su" es SINGULAR.** Ante sustantivo plural haria falta "sus", y el token
no lo da. Asi que **detras de `$hisOrHer` el sustantivo va siempre en singular**:

- Mal: "$HisOrHer ojos se desvian"   -> saldria "su ojos"
- Bien: "$HisOrHer mirada se desvia" -> "su mirada se desvia"
- Mal: "$hisOrHer manos temblaban"   -> "su manos"
- Bien: "le temblaban las manos"     (reformular y quitar el token: se puede,
  los pronombres son elidibles)

**Lo mas sencillo: no uses el token.** En español "su" y "sus" NO dependen del
genero del poseedor, solo del numero de lo poseido. "his hands" y "her hands"
son las dos "sus manos". Asi que puedes escribir directamente "su" o "sus" y
siempre sera correcto. Los pronombres son elidibles, asi que quitarlo es valido.

### Tokens de concordancia (solo estos se pueden añadir)

Para lo demas, el mod aporta tokens propios. **Son la unica excepcion a la
regla de "no añadir tokens"**:

| Token | Sale como |
|---|---|
| `$unUna` / `$UnUna` | un / una |
| `$elLa` / `$ElLa` | el / la |
| `$oA` | o / a *(terminacion de adjetivo)* |

Uso: en vez de "un(a) $manOrWoman" (chapuza que arrastra el mod portugues),
escribe **"$unUna $manOrWoman"**. Y para un adjetivo referido a esa persona:
"parece muy segur$oA de sí mism$oA".

No inventes otros tokens: cualquiera fuera de esta tabla rompe el juego.

## Jerarquia de la Iglesia Ludica (fijada, no improvisar)

Los agentes anteriores propusieron versiones distintas del mismo rango. La
forma canonica es esta y no se discute:

| Ingles | Español |
|---|---|
| Curate | cura |
| Subcurate | subcura *(invariable: "la subcura Cedra")* |
| Archcurate | archicura |
| Demarchon | demarconte *(paralelo a "arconte")* |
| Prime Demarchon | Primer Demarconte |
| Provost | preboste |
| Excubitor | excubitor |
| Brother / Sister | hermano / hermana |

Los cargos antepuestos a nombre propio van en **minuscula**, salvo al empezar
frase: "el preboste Baird", "la excubitor Orbis".

## "Burn bright" (despedida ludica)

Dos formas segun el registro, y solo estas dos:

- tuteo: **"Que arda tu luz"**
- usted: **"Que arda su luz"**

## Comillas: rectas, no latinas

Usa siempre `"` recta. **No uses « »**: las fuentes `futura12` y `futura16`
del juego no traen esos glifos (el mod portugues no los parcheo porque el
portugues no los usa) y saldrian rotos en pantalla.

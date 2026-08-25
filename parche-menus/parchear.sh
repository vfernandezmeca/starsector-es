#!/bin/sh
# Traduce los menus de Starsector. No hace falta instalar nada:
# usa la Java que ya trae el juego.
#
#   ./parchear.sh                      (si el mod ya esta en mods/)
#   ./parchear.sh /ruta/a/starsector
#   ./parchear.sh --restaura
set -e
cd "$(dirname "$0")"

JUEGO=""
RESTAURA=""
for a in "$@"; do
  if [ "$a" = "--restaura" ]; then RESTAURA="--restaura"; else JUEGO="$a"; fi
done

# si el mod esta instalado, el juego son tres carpetas hacia arriba:
#   <juego>/mods/Starsector Espanol/parche-menus
if [ -z "$JUEGO" ] && [ -f "../../../starfarer_obf.jar" ]; then
  JUEGO="$(cd ../../.. && pwd)"
fi
[ -z "$JUEGO" ] && JUEGO="${STARSECTOR:-$HOME/Games/starsector}"

if [ ! -f "$JUEGO/starfarer_obf.jar" ]; then
  echo "No encuentro Starsector en: $JUEGO"
  echo "Pasa la ruta:  ./parchear.sh /ruta/a/starsector"
  exit 1
fi

JAVA=""
for c in "$JUEGO/jre_linux/bin/java" "$JUEGO/jre/bin/java" \
         "$JUEGO/Contents/Home/bin/java" "$JUEGO/jre_macos/Contents/Home/bin/java"; do
  [ -x "$c" ] && JAVA="$c" && break
done
[ -z "$JAVA" ] && command -v java >/dev/null 2>&1 && JAVA="java"
if [ -z "$JAVA" ]; then
  echo "No encuentro ninguna Java, ni la del juego ni la del sistema."
  exit 1
fi

echo "Juego: $JUEGO"
if [ -n "$RESTAURA" ]; then
  exec "$JAVA" -jar parchear.jar "$JUEGO" --restaura
else
  exec "$JAVA" -jar parchear.jar "$JUEGO"
fi

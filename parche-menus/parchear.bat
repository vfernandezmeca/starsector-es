@echo off
REM Traduce los menus de Starsector. No hace falta instalar nada:
REM usa la Java que ya trae el juego.
REM
REM   parchear.bat                       (si el mod ya esta en mods\)
REM   parchear.bat "C:\ruta\a\Starsector"
REM   parchear.bat --restaura
setlocal
cd /d "%~dp0"

set "JUEGO="
set "RESTAURA="

:args
if "%~1"=="" goto fin_args
if /i "%~1"=="--restaura" (set "RESTAURA=--restaura") else (set "JUEGO=%~1")
shift
goto args
:fin_args

REM si el mod ya esta en mods\, el juego son tres carpetas hacia arriba:
REM   <juego>\mods\Starsector Espanol\parche-menus
if not defined JUEGO for %%d in ("%~dp0..\..\..") do set "JUEGO=%%~fd"

REM en Windows los .jar no estan en la raiz sino en starsector-core\
if not exist "%JUEGO%\starfarer_obf.jar" if exist "%JUEGO%\starsector-core\starfarer_obf.jar" set "JUEGO=%JUEGO%\starsector-core"

if not exist "%JUEGO%\starfarer_obf.jar" (
  echo No encuentro Starsector en: %JUEGO%
  echo Pasa la ruta:  parchear.bat "C:\ruta\a\Starsector"
  pause
  exit /b 1
)

REM la Java del juego cuelga de la raiz, no de starsector-core
for %%d in ("%JUEGO%\..") do set "RAIZ=%%~fd"
set "JAVA="
for %%j in ("%RAIZ%\jre" "%JUEGO%\jre" "%RAIZ%\jre_windows" "%JUEGO%\jre_windows") do (
  if not defined JAVA if exist "%%~j\bin\java.exe" set "JAVA=%%~j\bin\java.exe"
)
if not defined JAVA set "JAVA=java"

echo Juego: %JUEGO%
echo Java:  %JAVA%
"%JAVA%" -jar parchear.jar "%JUEGO%" %RESTAURA%
if errorlevel 1 (
  echo.
  echo No se pudo parchear. Dos causas tipicas en Windows:
  echo   - el juego esta abierto: cierralo del todo y repite.
  echo   - acceso denegado: el juego suele estar en Archivos de programa, y ahi
  echo     Windows no deja escribir. Boton derecho ^> Ejecutar como administrador.
)
pause

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
for %%a in (%*) do (
  if "%%~a"=="--restaura" (set "RESTAURA=--restaura") else (set "JUEGO=%%~a")
)

REM si el mod ya esta en mods\, el juego son tres carpetas hacia arriba
if "%JUEGO%"=="" if exist "..\..\..\starfarer_obf.jar" (
  pushd ..\..\..
  set "JUEGO=%CD%"
  popd
)
if "%JUEGO%"=="" set "JUEGO=C:\Program Files (x86)\Fractal Softworks\Starsector"

if not exist "%JUEGO%\starfarer_obf.jar" (
  echo No encuentro Starsector en: %JUEGO%
  echo Pasa la ruta:  parchear.bat "C:\ruta\a\Starsector"
  pause
  exit /b 1
)

set "JAVA=%JUEGO%\jre\bin\java.exe"
if not exist "%JAVA%" set "JAVA=%JUEGO%\jre_windows\bin\java.exe"
if not exist "%JAVA%" set "JAVA=java"

echo Juego: %JUEGO%
"%JAVA%" -jar parchear.jar "%JUEGO%" %RESTAURA%
pause

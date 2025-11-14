@echo off
setlocal

if not exist bin mkdir bin
if not exist tmp\build mkdir tmp\build

rmdir /s /q tmp\build 2>nul
rmdir /s /q bin 2>nul
del Magus.spec 2>nul
mkdir bin
mkdir tmp\build

pyinstaller client\src\client\__main__.py ^
  --onefile ^
  --noconsole ^
  --paths=common ^
  --add-data "assets;assets" ^
  --name "Magus" ^
  --distpath bin ^
  --workpath tmp\build ^
  --collect-all client ^
  --collect-all common ^
  --clean 

echo Build complete: bin\Magus.exe
pause

@echo off
setlocal

set "PROJECT_ROOT=%~dp0"

powershell -NoProfile -Command ^
  "& { $ErrorActionPreference = 'Stop'; Set-Location '%PROJECT_ROOT%';" ^
  "  $srcRoot = 'src/main/java'; $outDir = 'out';" ^
  "  Remove-Item $outDir -Recurse -Force -ErrorAction SilentlyContinue;" ^
  "  New-Item -ItemType Directory -Path $outDir | Out-Null;" ^
  "  $javaFiles = Get-ChildItem -Path $srcRoot -Recurse -Filter *.java | ForEach-Object { $_.FullName };" ^
  "  javac -encoding UTF-8 -d $outDir @javaFiles;" ^
  "  java -cp $outDir practice.ddd.uml.Main }"

exit /b %errorlevel%

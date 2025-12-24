$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$srcRoot = Join-Path $projectRoot "src/main/java"
$outDir = Join-Path $projectRoot "out"

if (-not (Test-Path $srcRoot)) {
  throw "Source directory not found: $srcRoot"
}

Remove-Item $outDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $outDir | Out-Null

$javaFiles = Get-ChildItem -Path $srcRoot -Recurse -Filter *.java | ForEach-Object { $_.FullName }
if ($javaFiles.Count -eq 0) {
  throw "No Java files found under: $srcRoot"
}

javac -encoding UTF-8 -d $outDir @javaFiles
java -cp $outDir practice.ddd.uml.Main


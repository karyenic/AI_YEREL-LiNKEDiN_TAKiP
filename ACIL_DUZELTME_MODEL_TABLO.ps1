$ErrorActionPreference = "Stop"

$Project = "C:\AI_YEREL\LiNKEDiN_TAKiP"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $Project "BACKUP_ACIL_$Stamp"

Set-Location $Project

Write-Host "=== ACIL MODEL + TABLO DUZELTMESI ===" -ForegroundColor Cyan

$Files = @("Baslat.bat","config.py","static\style.css")
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

foreach ($File in $Files) {
    $src = Join-Path $Project $File
    if (-not (Test-Path $src)) { throw "Dosya bulunamadi: $src" }
    $dst = Join-Path $BackupDir $File
    New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
    Copy-Item $src $dst -Force
}

# 1) Baslat.bat: birlesmis iki SET komutunu ayir
$BatPath = Join-Path $Project "Baslat.bat"
$Bat = Get-Content $BatPath -Raw
$bad = 'set OLLAMA_EXE=C:\AI_IPEX\Ollama\portable\ollama.exeset OLLAMA_KEEP_ALIVE=30m'
if ($Bat.Contains($bad)) {
    $Bat = $Bat.Replace($bad, "set OLLAMA_EXE=C:\AI_IPEX\Ollama\portable\ollama.exe`r`nset OLLAMA_KEEP_ALIVE=30m")
} elseif ($Bat -match '(?m)^set OLLAMA_EXE=C:\\AI_IPEX\\Ollama\\portable\\ollama\.exe.*$') {
    $Bat = [regex]::Replace($Bat, '(?m)^set OLLAMA_EXE=C:\\AI_IPEX\\Ollama\\portable\\ollama\.exe.*$', "set OLLAMA_EXE=C:\AI_IPEX\Ollama\portable\ollama.exe`r`nset OLLAMA_KEEP_ALIVE=30m")
} else {
    throw "Baslat.bat icinde OLLAMA_EXE satiri bulunamadi."
}
[IO.File]::WriteAllText($BatPath,$Bat,[Text.UTF8Encoding]::new($false))

# 2) config.py: sadece ministral-3:14b iceren satirlari kaldir
$ConfigPath = Join-Path $Project "config.py"
$Config = Get-Content $ConfigPath -Raw
$before = ([regex]::Matches($Config,'ministral-3:14b')).Count
$Config = [regex]::Replace($Config,'(?m)^[ \t]*.*ministral-3:14b.*\r?\n?','')
if (([regex]::Matches($Config,'ministral-3:14b')).Count -ne 0) {
    throw "ministral-3:14b config.py icinden temizlenemedi."
}
[IO.File]::WriteAllText($ConfigPath,$Config,[Text.UTF8Encoding]::new($false))

# 3) style.css: dikey scroll + sticky header
$CssPath = Join-Path $Project "static\style.css"
$Css = Get-Content $CssPath -Raw
$newBlock = @'
.table-scroll {
  width: 100% !important;
  max-width: 100% !important;
  max-height: calc(100vh - 300px) !important;
  overflow-x: auto !important;
  overflow-y: auto !important;
  position: relative !important;
}
'@

if ($Css -match '(?s)\.table-scroll\s*\{.*?\}') {
    $Css = [regex]::Replace($Css,'(?s)\.table-scroll\s*\{.*?\}',$newBlock.TrimEnd(),1)
} else {
    $Css += "`r`n`r`n$newBlock"
}

if ($Css -notmatch '(?s)thead\s+th\s*\{[^}]*position:\s*sticky') {
    $Css += @'

/* ACIL DUZELTME: tablo basligi satirlar kayarken sabit kalir. */
thead th {
  position: sticky;
  top: 0;
  z-index: 20;
  background: #0d1117;
}
'@
}
[IO.File]::WriteAllText($CssPath,$Css,[Text.UTF8Encoding]::new($false))

# Kontroller
if (Get-Command python -ErrorAction SilentlyContinue) {
    python -m py_compile $ConfigPath
    if ($LASTEXITCODE -ne 0) { throw "config.py syntax hatasi." }
}

if ((Get-Content $BatPath -Raw) -match 'ollama\.exeset\s+OLLAMA_KEEP_ALIVE') { throw "Baslat.bat SET hatasi devam ediyor." }
if ((Get-Content $ConfigPath -Raw) -match 'ministral-3:14b') { throw "ministral-3:14b hala mevcut." }

$CssCheck = Get-Content $CssPath -Raw
if ($CssCheck -notmatch '(?s)\.table-scroll\s*\{[^}]*overflow-y:\s*auto') { throw "overflow-y:auto bulunamadi." }
if ($CssCheck -notmatch '(?s)thead\s+th\s*\{[^}]*position:\s*sticky') { throw "sticky header bulunamadi." }

Write-Host ""
Write-Host "DUZELTME TAMAMLANDI." -ForegroundColor Green
Write-Host "Yedek: $BackupDir" -ForegroundColor Cyan
Write-Host ""
git status --short
Write-Host ""
git diff -- Baslat.bat config.py static/style.css
Write-Host ""
Write-Host "app.py ve core\ollama_client.py bu adimda DEGISTIRILMEDI." -ForegroundColor Yellow

# push_to_github.ps1
# KULLANIM: Bu dosyayı, GitHub'a bagli yerel proje klasorunun ICINE koy
# (yani .git klasorunun yaninda), sonra PowerShell'de:
#   powershell -ExecutionPolicy Bypass -File .\push_to_github.ps1
#
# Eger bu proje henuz senin bilgisayarinda git deposu degilse, once
# GitHub'daki repo'yu klonlaman gerekir:
#   git clone https://github.com/karyenic/AI_YEREL-LiNKEDiN_TAKiP.git
# ve guncel dosyalari o klasorun icine kopyaladiktan sonra bu betigi
# o klasorde calistir.

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

if (-not (Test-Path ".git")) {
    Write-Host "[HATA] Bu klasor bir git deposu degil." -ForegroundColor Red
    Write-Host "       Bu betigi, icinde .git klasoru olan proje kok dizininde calistirmalisin." -ForegroundColor Red
    Read-Host "Kapatmak icin Enter'a bas"
    exit 1
}

Write-Host "============================================================" -ForegroundColor DarkCyan
Write-Host " GITHUB PUSH" -ForegroundColor DarkCyan
Write-Host "============================================================" -ForegroundColor DarkCyan

Write-Host "[1/4] Durum kontrol ediliyor..." -ForegroundColor Cyan
git status --short

$degisiklikVar = (git status --porcelain)
if ([string]::IsNullOrWhiteSpace($degisiklikVar)) {
    Write-Host "Gonderilecek bir degisiklik yok. Cikiliyor." -ForegroundColor Yellow
    Read-Host "Kapatmak icin Enter'a bas"
    exit 0
}

Write-Host "[2/4] Degisiklikler ekleniyor (git add -A)..." -ForegroundColor Cyan
git add -A

$mesaj = Read-Host "Commit mesaji (bos birakirsan otomatik tarih yazilir)"
if ([string]::IsNullOrWhiteSpace($mesaj)) {
    $mesaj = "Guncelleme: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
}

Write-Host "[3/4] Commit yapiliyor: $mesaj" -ForegroundColor Cyan
git commit -m "$mesaj"

$branch = (git rev-parse --abbrev-ref HEAD).Trim()
Write-Host "[4/4] '$branch' dalina push ediliyor..." -ForegroundColor Cyan
git push origin $branch

Write-Host ""
Write-Host "TAMAM! GitHub guncellendi -> https://github.com/karyenic/AI_YEREL-LiNKEDiN_TAKiP" -ForegroundColor Green
Read-Host "Kapatmak icin Enter'a bas"

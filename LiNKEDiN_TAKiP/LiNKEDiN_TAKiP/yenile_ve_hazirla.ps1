# yenile_ve_hazirla.ps1
# KULLANIM:
#   powershell -ExecutionPolicy Bypass -File .\yenile_ve_hazirla.ps1 -RepoYolu "C:\...\git-repo-klasoru" -YeniYolu "C:\...\zipten-cikan-klasor"
#
# Ne yapar:
#   1) RepoYolu icinde .git klasoru VAR MI diye kontrol eder (yoksa hicbir sey silmez, guvenli cikis)
#   2) RepoYolu icindeki .git DISINDAKI her seyi siler
#   3) YeniYolu icindeki tum dosyalari RepoYolu'na kopyalar
#
# Sonra push_to_github.ps1'i RepoYolu icinde calistirabilirsin.

param(
    [Parameter(Mandatory=$true)][string]$RepoYolu,
    [Parameter(Mandatory=$true)][string]$YeniYolu
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

if (-not (Test-Path $RepoYolu)) {
    Write-Host "[HATA] RepoYolu bulunamadi: $RepoYolu" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $YeniYolu)) {
    Write-Host "[HATA] YeniYolu bulunamadi: $YeniYolu" -ForegroundColor Red
    exit 1
}
$gitYolu = Join-Path $RepoYolu ".git"
if (-not (Test-Path $gitYolu)) {
    Write-Host "[HATA] '$RepoYolu' icinde .git klasoru yok - guvenlik icin HICBIR SEY SILINMEDI." -ForegroundColor Red
    Write-Host "        Dogru klasoru mu verdin, kontrol et." -ForegroundColor Red
    exit 1
}

Write-Host "============================================================" -ForegroundColor DarkCyan
Write-Host " ESKI: $RepoYolu" -ForegroundColor DarkCyan
Write-Host " YENI: $YeniYolu" -ForegroundColor DarkCyan
Write-Host "============================================================" -ForegroundColor DarkCyan
$onay = Read-Host "Bu klasordeki .git DISINDAKI HER SEY silinecek. Devam? (E/H)"
if ($onay -ne "E" -and $onay -ne "e") {
    Write-Host "Iptal edildi." -ForegroundColor Yellow
    exit 0
}

Write-Host "[1/2] Eski dosyalar temizleniyor (.git korunuyor)..." -ForegroundColor Cyan
Get-ChildItem -Path $RepoYolu -Force | Where-Object { $_.Name -ne ".git" } | Remove-Item -Recurse -Force

Write-Host "[2/2] Yeni dosyalar kopyalaniyor..." -ForegroundColor Cyan
Copy-Item -Path (Join-Path $YeniYolu "*") -Destination $RepoYolu -Recurse -Force

Write-Host ""
Write-Host "TAMAM. Simdi push_to_github.ps1'i su klasorde calistir:" -ForegroundColor Green
Write-Host "  $RepoYolu" -ForegroundColor Green
Read-Host "Kapatmak icin Enter'a bas"

# temizle_yedekler.ps1
# KULLANIM: Repo kok dizininde calistir:
#   powershell -ExecutionPolicy Bypass -File .\temizle_yedekler.ps1
#
# Ne yapar: *.yedek*, *.DURAK2_BACKUP*, *.bak uzantili yedek dosyalarini
# git'ten ve diskten kaldirir, .gitignore'a bir daha eklenmesinler diye
# kural ekler.

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

if (-not (Test-Path ".git")) {
    Write-Host "[HATA] Bu klasor bir git deposu degil - repo kok dizininde calistir." -ForegroundColor Red
    exit 1
}

$desenler = @("*.yedek*", "*.DURAK2_BACKUP*", "*.bak")
$bulunan = @()
foreach ($d in $desenler) {
    $bulunan += Get-ChildItem -Path . -Recurse -Filter $d -File -ErrorAction SilentlyContinue
}

if ($bulunan.Count -eq 0) {
    Write-Host "Temizlenecek yedek dosya bulunamadi." -ForegroundColor Yellow
} else {
    Write-Host "Su dosyalar silinecek:" -ForegroundColor Cyan
    $bulunan | ForEach-Object { Write-Host "  $($_.FullName)" -ForegroundColor DarkGray }
    $onay = Read-Host "Devam? (E/H)"
    if ($onay -eq "E" -or $onay -eq "e") {
        foreach ($f in $bulunan) {
            git rm --cached --ignore-unmatch "$($f.FullName.Substring((Get-Location).Path.Length + 1))" | Out-Null
            Remove-Item $f.FullName -Force
        }
        Write-Host "Silindi." -ForegroundColor Green
    } else {
        Write-Host "Iptal edildi." -ForegroundColor Yellow
    }
}

Write-Host "[.gitignore guncelleniyor]" -ForegroundColor Cyan
$ekler = @("*.yedek*", "*.DURAK2_BACKUP*", "*.bak")
$mevcutIcerik = if (Test-Path ".gitignore") { Get-Content ".gitignore" -Raw } else { "" }
foreach ($e in $ekler) {
    if ($mevcutIcerik -notmatch [regex]::Escape($e)) {
        Add-Content ".gitignore" $e
    }
}

Write-Host ""
Write-Host "Tamam. Simdi push_to_github.ps1'i calistirip gonderebilirsin." -ForegroundColor Green
Read-Host "Kapatmak icin Enter'a bas"

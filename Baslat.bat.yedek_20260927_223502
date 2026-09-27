@echo off
chcp 65001 >nul
title LinkedIn Takip - Flask
color 0A

echo ================================================
echo   LinkedIn Takip Asistani (Flask)
echo ================================================

set OLLAMA_EXE=C:\AI_IPEX\Ollama\portable\ollama.exe

if not exist "%OLLAMA_EXE%" (
    echo [UYARI] IPEX Ollama bulunamadi: %OLLAMA_EXE%
    echo         Standart Ollama ile devam edilecek, Intel Arc hizlandirmasi CALISMAYACAK.
    set OLLAMA_EXE=ollama
)

REM --- GK_STUDIO_V3'te dogrulanmis, gercekten calisan Intel Arc / IPEX ayarlari ---
set OLLAMA_NUM_GPU=999
set ONEAPI_DEVICE_SELECTOR=level_zero:0
set ZES_ENABLE_SYSMAN=1
set SYCL_CACHE_PERSISTENT=1
set OLLAMA_FLASH_ATTENTION=false
set NO_PROXY=localhost,127.0.0.1
set OLLAMA_HOST=127.0.0.1:11434
set OLLAMA_NUM_PARALLEL=1
set OLLAMA_KEEP_ALIVE=30m

echo [0/3] Intel Arc/IPEX ortam degiskenleri ayarlandi.
echo        Kullanilan Ollama: %OLLAMA_EXE%

taskkill /f /im ollama.exe >nul 2>&1
taskkill /f /im ollama-lib.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [1/3] Ollama (IPEX) baslatiliyor...
start "Ollama-IPEX" /min cmd /c ""%OLLAMA_EXE%" serve"

echo [2/3] Ollama portu bekleniyor...
set /a n=0
:W
timeout /t 1 /nobreak >nul
curl -s http://127.0.0.1:11434 >nul 2>&1
if %errorlevel%==0 goto HAZIR
set /a n+=1
if %n% GEQ 30 goto HATA
goto W

:HAZIR
echo        Ollama hazir.

echo [3/3] Flask baslatiliyor...
cd /d "%~dp0"
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:5050"
python app.py

pause
goto :eof

:HATA
echo [HATA] Ollama 30 saniyede acilmadi.
pause
@echo off
cd /d "%~dp0"
py -3 -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
where ffmpeg >nul 2>&1
if errorlevel 1 goto ffmpeg
where ffprobe >nul 2>&1
if errorlevel 1 goto ffmpeg
where deno >nul 2>&1
if errorlevel 1 goto deno
echo Cai xong. Mo CHAY_MAY_CHU.cmd.
pause
exit /b 0
:ffmpeg
echo Thieu FFmpeg/ffprobe. Hay cai FFmpeg va mo lai cua so.
start https://ffmpeg.org/download.html
pause
exit /b 1
:deno
echo Thieu Deno. Hay cai Deno va mo lai cua so.
start https://deno.com/
pause
exit /b 1
:fail
echo Cai chua thanh cong. Kiem tra Python va Internet; gui anh loi de duoc ho tro.
pause
exit /b 1

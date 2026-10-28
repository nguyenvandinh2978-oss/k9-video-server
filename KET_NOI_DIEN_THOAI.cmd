@echo off
set "TS=%ProgramFiles%\Tailscale\tailscale.exe"
if not exist "%TS%" (
 echo Cai Tailscale tren Windows va dien thoai, dang nhap cung tai khoan.
 start https://tailscale.com/download
 pause
 exit /b 1
)
"%TS%" serve --bg http://127.0.0.1:8765
if errorlevel 1 (
 echo Lam theo huong dan dang nhap/bat HTTPS tren man hinh roi chay lai tep nay.
) else (
 echo Mo dia chi HTTPS ben tren tren dien thoai da bat Tailscale.
)
pause

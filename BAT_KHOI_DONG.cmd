@echo off
cd /d "%~dp0"
powershell -NoProfile -Command "$w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut([IO.Path]::Combine([Environment]::GetFolderPath('Startup'),'K9 Video Server.lnk')); $s.TargetPath=[IO.Path]::Combine((Get-Location).Path,'CHAY_MAY_CHU.cmd'); $s.WorkingDirectory=(Get-Location).Path; $s.WindowStyle=7; $s.Save()"
if errorlevel 1 (
 echo Chua tao duoc loi tat khoi dong.
) else (
 echo Da tao loi tat: may chu se chay sau khi anh dang nhap Windows.
)
pause

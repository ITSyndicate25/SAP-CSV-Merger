@echo off
setlocal EnableExtensions

:: SAP CSV Merger Uninstaller
:: install.bat copies this file next to SAP_CSV_Merger.exe.
:: No goto/labels in this file on purpose: it must work with LF or CRLF endings.

set "APP_NAME=SAP CSV Merger"
set "APP_EXE_NAME=SAP_CSV_Merger.exe"
set "INSTALL_DIR=%~dp0"
if "%INSTALL_DIR:~-1%"=="\" set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"
set "START_MENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\%APP_NAME%"
set "UNINSTALL_REG_KEY=HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\SAP_CSV_Merger"

title %APP_NAME% Uninstaller
color 0C

set "QUIET="
if /I "%~1"=="/S" set "QUIET=1"

if not defined QUIET (
    echo.
    echo ============================================================
    echo           %APP_NAME% Uninstaller
    echo ============================================================
    echo.
    echo This will remove %APP_NAME% from:
    echo   %INSTALL_DIR%
    echo.
    echo Your exported CSV files are not touched.
    echo.
)

:: Read the answer outside any block: %CONFIRM% expands when a block is parsed.
set "CONFIRM=Y"
if not defined QUIET set "CONFIRM="
if not defined QUIET set /p "CONFIRM=Are you sure you want to uninstall? (Y/N): "
if /I not "%CONFIRM%"=="Y" if /I not "%CONFIRM%"=="y" (
    echo Uninstall cancelled.
    pause
    exit /b 0
)

:: A running app holds SAP_CSV_Merger.exe open; deletion would silently fail.
tasklist /FI "IMAGENAME eq %APP_EXE_NAME%" 2>nul | find /I "%APP_EXE_NAME%" >nul
if not errorlevel 1 (
    echo ERROR: %APP_NAME% is running. Close it, then run the uninstaller again.
    if not defined QUIET pause
    exit /b 1
)

echo Removing shortcuts...
:: The Desktop folder may be redirected (OneDrive, domain policy); ask Windows.
set "SAP_APP_NAME=%APP_NAME%"
powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "$ErrorActionPreference='SilentlyContinue'; Remove-Item -LiteralPath (Join-Path ([Environment]::GetFolderPath('Desktop')) ($env:SAP_APP_NAME + '.lnk')) -Force" >nul 2>&1
rmdir /S /Q "%START_MENU_DIR%" >nul 2>&1

echo Removing registry entries...
reg delete "%UNINSTALL_REG_KEY%" /f >nul 2>&1

echo Removing application files...
del /Q "%INSTALL_DIR%\%APP_EXE_NAME%" >nul 2>&1
for /D %%D in ("%INSTALL_DIR%\*") do rmdir /S /Q "%%~fD" >nul 2>&1

if not defined QUIET (
    echo.
    echo %APP_NAME% has been uninstalled successfully.
    echo You can close this window.
    pause
)

:: A running batch file is held open by cmd, so the folder cannot be removed
:: here. Detach a shell that waits for this one to exit, then removes it.
start "" /b cmd /c "ping -n 3 127.0.0.1 >nul & rmdir /S /Q "%INSTALL_DIR%" >nul 2>&1"
exit /b 0

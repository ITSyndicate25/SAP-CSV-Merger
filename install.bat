@echo off
setlocal EnableExtensions

:: SAP CSV Merger Installer
:: No goto/labels in this file on purpose: it must work with LF or CRLF endings.
set "APP_NAME=SAP CSV Merger"
set "APP_VERSION=1.1.0"
set "APP_EXE_NAME=SAP_CSV_Merger.exe"
set "APP_DIR_NAME=SAP_CSV_Merger"

set "DEFAULT_DIR=%LOCALAPPDATA%\%APP_NAME%"
set "START_MENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\%APP_NAME%"
set "UNINSTALL_REG_KEY=HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\SAP_CSV_Merger"

title %APP_NAME% Installer
color 0A

:: Resolve payload paths against this script, not the caller's working directory.
cd /d "%~dp0"

echo.
echo ============================================================
echo           %APP_NAME% Installer v%APP_VERSION%
echo ============================================================
echo.
echo This installer will install %APP_NAME% on your computer.
echo.
echo Requirements:
echo   - Windows 10 or later
echo   - 50 MB free disk space
echo.
echo ============================================================
echo.

:: PyInstaller builds either a one-file executable or a one-directory tree.
:: Accept both layouts, plus an unpacked release folder.
set "SOURCE_DIR="
set "SOURCE_EXE="
if exist "%~dp0dist\%APP_DIR_NAME%\%APP_EXE_NAME%" set "SOURCE_DIR=%~dp0dist\%APP_DIR_NAME%"
if not defined SOURCE_DIR if exist "%~dp0dist\%APP_EXE_NAME%" set "SOURCE_EXE=%~dp0dist\%APP_EXE_NAME%"
if not defined SOURCE_DIR if not defined SOURCE_EXE if exist "%~dp0%APP_EXE_NAME%" set "SOURCE_EXE=%~dp0%APP_EXE_NAME%"

if not defined SOURCE_DIR if not defined SOURCE_EXE (
    echo ERROR: Application files not found.
    echo.
    echo Looked for:
    echo   dist\%APP_DIR_NAME%\%APP_EXE_NAME%   ^(one-directory build^)
    echo   dist\%APP_EXE_NAME%                  ^(one-file build^)
    echo   %APP_EXE_NAME%
    echo.
    echo Build the application first:
    echo   pyinstaller sap_csv_merger.spec --clean
    echo.
    pause
    exit /b 1
)

if not exist "%~dp0uninstall.bat" (
    echo ERROR: uninstall.bat is missing next to install.bat.
    echo.
    pause
    exit /b 1
)

:: The Inno Setup build registers under its own AppId. Running both would leave
:: two entries in Programs and Features pointing at the same folder.
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}_is1" >nul 2>&1
if not errorlevel 1 (
    echo ERROR: %APP_NAME% was installed with SAP_CSV_Merger_Setup.exe.
    echo.
    echo Uninstall it from Programs and Features first, or keep using it.
    echo This script and the Setup installer cannot both own the app.
    echo.
    pause
    exit /b 1
)

echo Installation directory:
echo   Default: %DEFAULT_DIR%
echo.
set "CUSTOM_DIR="
set /p "CUSTOM_DIR=Press Enter to use default, or type custom path: "

:: No delayed expansion here: user paths may contain "!" and must survive intact.
set "INSTALL_DIR=%DEFAULT_DIR%"
if defined CUSTOM_DIR set "INSTALL_DIR=%CUSTOM_DIR%"
set INSTALL_DIR=%INSTALL_DIR:"=%
if "%INSTALL_DIR:~-1%"=="\" set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"
if "%INSTALL_DIR%"=="" set "INSTALL_DIR=%DEFAULT_DIR%"

if exist "%INSTALL_DIR%" if not exist "%INSTALL_DIR%\" (
    echo.
    echo ERROR: %INSTALL_DIR% is a file, not a folder.
    echo.
    pause
    exit /b 1
)

echo.
echo Installing to: %INSTALL_DIR%
echo.

echo [1/5] Creating installation directory...
if not exist "%INSTALL_DIR%\" mkdir "%INSTALL_DIR%" >nul 2>&1
if not exist "%INSTALL_DIR%\" (
    echo ERROR: Cannot create %INSTALL_DIR%
    echo Check that the path is valid and writable.
    echo.
    pause
    exit /b 1
)

echo [2/5] Copying application files...
:: A running app holds SAP_CSV_Merger.exe open, so the overwrite fails.
tasklist /FI "IMAGENAME eq %APP_EXE_NAME%" 2>nul | find /I "%APP_EXE_NAME%" >nul
if not errorlevel 1 (
    echo ERROR: %APP_NAME% is running. Close it, then run this installer again.
    echo.
    pause
    exit /b 1
)

set "COPY_FAILED="
if defined SOURCE_DIR (
    xcopy /E /I /Y /Q "%SOURCE_DIR%\*" "%INSTALL_DIR%\" >nul
    if errorlevel 1 set "COPY_FAILED=1"
) else (
    copy /Y "%SOURCE_EXE%" "%INSTALL_DIR%\%APP_EXE_NAME%" >nul
    if errorlevel 1 set "COPY_FAILED=1"
)
if not defined COPY_FAILED copy /Y "%~dp0uninstall.bat" "%INSTALL_DIR%\uninstall.bat" >nul
if not defined COPY_FAILED if not exist "%INSTALL_DIR%\%APP_EXE_NAME%" set "COPY_FAILED=1"
if not defined COPY_FAILED if not exist "%INSTALL_DIR%\uninstall.bat" set "COPY_FAILED=1"

if defined COPY_FAILED (
    echo ERROR: Failed to copy files into %INSTALL_DIR%
    echo.
    echo The folder is not writable, has less than 50 MB free, or
    echo %APP_NAME% is running. Close the app and run this installer again.
    echo.
    pause
    exit /b 1
)

echo [3/5] Creating Start Menu shortcuts...
if not exist "%START_MENU_DIR%" mkdir "%START_MENU_DIR%" >nul 2>&1
:: Pass paths through the environment: the PowerShell command line is single-quoted.
set "SAP_INSTALL_DIR=%INSTALL_DIR%"
powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ws=New-Object -ComObject WScript.Shell; $sc=$ws.CreateShortcut((Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\SAP CSV Merger\SAP CSV Merger.lnk')); $sc.TargetPath=(Join-Path $env:SAP_INSTALL_DIR 'SAP_CSV_Merger.exe'); $sc.WorkingDirectory=$env:SAP_INSTALL_DIR; $sc.IconLocation=(Join-Path $env:SAP_INSTALL_DIR 'SAP_CSV_Merger.exe') + ',0'; $sc.Description='SAP CSV Merger Application'; $sc.Save()" >nul 2>&1
if errorlevel 1 echo WARNING: Could not create the Start Menu shortcut.

echo [4/5] Creating Desktop shortcut...
:: Ask Windows for the Desktop folder: OneDrive and domain policy redirect it.
powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ws=New-Object -ComObject WScript.Shell; $sc=$ws.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'SAP CSV Merger.lnk')); $sc.TargetPath=(Join-Path $env:SAP_INSTALL_DIR 'SAP_CSV_Merger.exe'); $sc.WorkingDirectory=$env:SAP_INSTALL_DIR; $sc.IconLocation=(Join-Path $env:SAP_INSTALL_DIR 'SAP_CSV_Merger.exe') + ',0'; $sc.Description='SAP CSV Merger Application'; $sc.Save()" >nul 2>&1
if errorlevel 1 echo WARNING: Could not create the Desktop shortcut.

echo [5/5] Registering uninstaller with Windows...
(
reg add "%UNINSTALL_REG_KEY%" /v "DisplayName" /t REG_SZ /d "%APP_NAME%" /f >nul
reg add "%UNINSTALL_REG_KEY%" /v "DisplayVersion" /t REG_SZ /d "%APP_VERSION%" /f >nul
reg add "%UNINSTALL_REG_KEY%" /v "DisplayIcon" /t REG_SZ /d "\"%INSTALL_DIR%\%APP_EXE_NAME%\",0" /f >nul
reg add "%UNINSTALL_REG_KEY%" /v "InstallLocation" /t REG_SZ /d "\"%INSTALL_DIR%\"" /f >nul
reg add "%UNINSTALL_REG_KEY%" /v "Publisher" /t REG_SZ /d "ITSyndicate25" /f >nul
reg add "%UNINSTALL_REG_KEY%" /v "UninstallString" /t REG_SZ /d "\"%INSTALL_DIR%\uninstall.bat\"" /f >nul
reg add "%UNINSTALL_REG_KEY%" /v "QuietUninstallString" /t REG_SZ /d "\"%INSTALL_DIR%\uninstall.bat\" /S" /f >nul
reg add "%UNINSTALL_REG_KEY%" /v "NoModify" /t REG_DWORD /d 1 /f >nul
reg add "%UNINSTALL_REG_KEY%" /v "NoRepair" /t REG_DWORD /d 1 /f >nul
reg add "%UNINSTALL_REG_KEY%" /v "EstimatedSize" /t REG_DWORD /d 30000 /f >nul
) >nul 2>&1
if errorlevel 1 echo WARNING: Could not register the uninstaller in the registry.

echo.
echo ============================================================
echo           Installation Complete!
echo ============================================================
echo.
echo SAP CSV Merger has been installed to:
echo   %INSTALL_DIR%
echo.
echo Shortcuts created:
echo   - Start Menu: %START_MENU_DIR%
echo   - Desktop: SAP CSV Merger.lnk
echo.
echo Windows uninstall registered:
echo   - Control Panel ^> Programs ^> Programs and Features
echo   - Or run: %INSTALL_DIR%\uninstall.bat
echo.
echo ============================================================
echo.

set "LAUNCH="
set /p "LAUNCH=Would you like to launch SAP CSV Merger now? (Y/N): "
if /I "%LAUNCH%"=="Y" (
    echo Launching SAP CSV Merger...
    start "" "%INSTALL_DIR%\%APP_EXE_NAME%"
)

echo.
echo Thank you for installing SAP CSV Merger!
pause

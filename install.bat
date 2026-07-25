@echo off
setlocal enabledelayedexpansion

:: SAP CSV Merger Installer
:: Version 1.0.1

title SAP CSV Merger Installer
color 0A

echo.
echo ============================================================
echo           SAP CSV Merger Installer v1.0.1
echo ============================================================
echo.
echo This installer will install SAP CSV Merger on your computer.
echo.
echo Requirements:
echo   - Windows 10 or later
echo   - 50 MB free disk space
echo.
echo ============================================================
echo.

:: Set installation directory (user's AppData - no admin required)
set "INSTALL_DIR=%LOCALAPPDATA%\SAP CSV Merger"
set "DESKTOP_SHORTCUT=%USERPROFILE%\Desktop\SAP CSV Merger.lnk"
set "START_MENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\SAP CSV Merger"
set "UNINSTALL_REG_KEY=HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\SAP_CSV_Merger"

:: Ask for installation directory
echo Installation directory:
echo   Default: %INSTALL_DIR%
echo.
set /p "CUSTOM_DIR=Press Enter to use default, or type custom path: "

if not "%CUSTOM_DIR%"=="" (
    set "INSTALL_DIR=%CUSTOM_DIR%"
)

echo.
echo Installing to: %INSTALL_DIR%
echo.

:: Create installation directory
echo [1/5] Creating installation directory...
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
)

:: Copy files
echo [2/5] Copying application files...
xcopy /E /I /Y "dist\SAP_CSV_Merger\*" "%INSTALL_DIR%\" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to copy files!
    echo Please run as administrator.
    pause
    exit /b 1
)

:: Create Start Menu shortcuts
echo [3/5] Creating Start Menu shortcuts...
if not exist "%START_MENU_DIR%" (
    mkdir "%START_MENU_DIR%"
)

:: App shortcut
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut('%START_MENU_DIR%\SAP CSV Merger.lnk'); $sc.TargetPath = '%INSTALL_DIR%\SAP_CSV_Merger.exe'; $sc.WorkingDirectory = '%INSTALL_DIR%'; $sc.Description = 'SAP CSV Merger Application'; $sc.IconLocation = '%INSTALL_DIR%\SAP_CSV_Merger.exe,0'; $sc.Save()"

:: Create Desktop shortcut
echo [4/5] Creating Desktop shortcut...
if not exist "%USERPROFILE%\Desktop" mkdir "%USERPROFILE%\Desktop"
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut('%DESKTOP_SHORTCUT%'); $sc.TargetPath = '%INSTALL_DIR%\SAP_CSV_Merger.exe'; $sc.WorkingDirectory = '%INSTALL_DIR%'; $sc.Description = 'SAP CSV Merger Application'; $sc.IconLocation = '%INSTALL_DIR%\SAP_CSV_Merger.exe,0'; $sc.Save()"

:: Register with Windows Add/Remove Programs
echo [5/5] Registering uninstaller with Windows...
(
reg add "%UNINSTALL_REG_KEY%" /v "DisplayName" /t REG_SZ /d "SAP CSV Merger" /f >nul
reg add "%UNINSTALL_REG_KEY%" /v "DisplayVersion" /t REG_SZ /d "1.0.1" /f >nul
reg add "%UNINSTALL_REG_KEY%" /v "DisplayIcon" /t REG_SZ /d "\"%INSTALL_DIR%\SAP_CSV_Merger.exe\",0" /f >nul
reg add "%UNINSTALL_REG_KEY%" /v "InstallLocation" /t REG_SZ /d "\"%INSTALL_DIR%\"" /f >nul
reg add "%UNINSTALL_REG_KEY%" /v "Publisher" /t REG_SZ /d "ITSyndicate25" /f >nul
reg add "%UNINSTALL_REG_KEY%" /v "UninstallString" /t REG_SZ /d "\"%INSTALL_DIR%\uninstall.bat\"" /f >nul
reg add "%UNINSTALL_REG_KEY%" /v "QuietUninstallString" /t REG_SZ /d "\"%INSTALL_DIR%\uninstall.bat\" /S" /f >nul
reg add "%UNINSTALL_REG_KEY%" /v "NoModify" /t REG_DWORD /d 1 /f >nul
reg add "%UNINSTALL_REG_KEY%" /v "NoRepair" /t REG_DWORD /d 1 /f >nul
reg add "%UNINSTALL_REG_KEY%" /v "EstimatedSize" /t REG_DWORD /d 30000 /f >nul
) >nul 2>&1

:: Create uninstall.bat
(
echo @echo off
echo title SAP CSV Merger Uninstaller
echo color 0C
echo.
echo echo ============================================================
echo echo           SAP CSV Merger Uninstaller
echo echo ============================================================
echo echo.
echo echo This will uninstall SAP CSV Merger from your computer.
echo echo.
echo if /I "%%1"=="/S" goto uninstall
echo set /p "CONFIRM=Are you sure you want to uninstall? (Y/N): "
echo if /I not "%%CONFIRM%"=="Y" (
echo     echo Uninstall cancelled.
echo     pause
echo     exit /b 0
echo ^)
echo :uninstall
echo echo.
echo echo Removing files and registry entries...
echo.
echo :: Remove desktop shortcut
echo del /Q "%DESKTOP_SHORTCUT%" 2^>nul
echo.
echo :: Remove start menu shortcuts
echo rmdir /S /Q "%START_MENU_DIR%" 2^>nul
echo.
echo :: Remove application files
echo rmdir /S /Q "%INSTALL_DIR%" 2^>nul
echo.
echo :: Remove uninstall registry key
echo reg delete "%UNINSTALL_REG_KEY%" /f ^>nul 2^>^&1
echo.
echo echo.
echo echo SAP CSV Merger has been uninstalled successfully.
echo if not "%%1"=="/S" pause
) > "%INSTALL_DIR%\uninstall.bat"

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
echo   - Desktop: %DESKTOP_SHORTCUT%
echo.
echo Windows uninstall registered:
echo   - Control Panel ^> Programs ^> Programs and Features
echo   - Or run: %INSTALL_DIR%\uninstall.bat
echo.
echo ============================================================
echo.

:: Ask to launch now
set /p "LAUNCH=Would you like to launch SAP CSV Merger now? (Y/N): "
if /I "%LAUNCH%"=="Y" (
    echo Launching SAP CSV Merger...
    start "" "%INSTALL_DIR%\SAP_CSV_Merger.exe"
)

echo.
echo Thank you for installing SAP CSV Merger!
pause

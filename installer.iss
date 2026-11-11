; Inno Setup Script for SAP CSV Merger
; Download Inno Setup from: https://jrsoftware.org/isinfo.php
;
; The PyInstaller spec builds a ONE-FILE executable:
;   pyinstaller sap_csv_merger.spec --clean  ->  dist\SAP_CSV_Merger.exe

#define MyAppName "SAP CSV Merger"
#define MyAppVersion "1.0.15"
#define MyAppPublisher "ITSyndicate25"
#define MyAppExeName "SAP_CSV_Merger.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes
; Matches install.bat: per-user install, no administrator rights needed.
PrivilegesRequired=lowest
OutputDir=installer
OutputBaseFilename=SAP_CSV_Merger_Setup_{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

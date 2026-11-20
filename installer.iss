; Inno Setup Script for SAP CSV Merger
; Compile: iscc installer.iss   (or open in the Inno Setup IDE)
;
; The PyInstaller spec builds a ONE-FILE executable:
;   pyinstaller sap_csv_merger.spec --clean  ->  dist\SAP_CSV_Merger.exe
;
; install.bat installs the same app to the same place. Only one of the two may
; own an installation at a time, so this script takes over cleanly: it deletes
; install.bat's uninstaller and its Add/Remove entry, and install.bat refuses to
; run while this installer's entry exists.

#define MyAppName "SAP CSV Merger"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "ITSyndicate25"
#define MyAppExeName "SAP_CSV_Merger.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
; Same directory install.bat uses, so either installer upgrades the other.
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes
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

[InstallDelete]
; install.bat's uninstaller belongs to a registration this installer replaces.
Type: files; Name: "{app}\uninstall.bat"

[UninstallDelete]
Type: files; Name: "{app}\uninstall.bat"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
const
  LegacyKey = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\SAP_CSV_Merger';

{ install.bat registers itself under its own key. Leaving it in place would put
  two identical entries in Programs and Features, one of them pointing at a
  deleted uninstaller. }
procedure RemoveLegacyRegistration();
begin
  if RegKeyExists(HKEY_CURRENT_USER, LegacyKey) then
    RegDeleteKeyIncludingSubkeys(HKEY_CURRENT_USER, LegacyKey);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    RemoveLegacyRegistration();
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    RemoveLegacyRegistration();
end;

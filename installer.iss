[Setup]
AppName=Intelligent File Search
AppVersion=1.0.0
DefaultDirName={pf}\Intelligent File Search
DefaultGroupName=Intelligent File Search
OutputDir=installer
OutputBaseFilename=FileSearch-Setup-Windows
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\main.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Intelligent File Search"; Filename: "{app}\main.exe"
Name: "{group}\{cm:UninstallProgram,Intelligent File Search}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Intelligent File Search"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\main.exe"; Description: "{cm:LaunchProgram,Intelligent File Search}"; Flags: nowait postinstall skipifsilent

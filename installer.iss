#define MyAppName "Vox Bridge"
#define MyAppVersion "0.0.1"
#define MyAppPublisher "HIGS Dev"
#define MyAppExeName "main.exe"

[Setup]
AppId={{B8F3A6B2-9C7A-4D3E-9C7B-123456789ABC}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename={#MyAppName}-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "dist\main\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\Vox Bridge"; Filename: "{app}\main.exe"
Name: "{commondesktop}\Vox Bridge"; Filename: "{app}\main.exe"


[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

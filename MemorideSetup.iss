; Memoride Installation Script 
; Created for easy one-click installation 
 
#define MyAppName "Memoride" 
#define MyAppVersion "1.0" 
#define MyAppPublisher "Memoride Team" 
#define MyAppURL "https://github.com/yourusername/memoride" 
#define MyAppExeName "Memoride.exe" 
 
[Setup] 
; Basic application information 
AppId={{6B3A6F56-9937-4586-9E55-5544ED931E98}} 
AppName={#MyAppName} 
AppVersion={#MyAppVersion} 
AppPublisher={#MyAppPublisher} 
AppPublisherURL={#MyAppURL} 
AppSupportURL={#MyAppURL} 
AppUpdatesURL={#MyAppURL} 
 
; Default installation directory 
DefaultDirName={autopf}\{#MyAppName} 
DefaultGroupName={#MyAppName} 
DisableProgramGroupPage=yes 
AllowNoIcons=yes 
 
; Output settings 
OutputDir=installer 
OutputBaseFilename=Memoride_Setup 
 
; Compression settings for smaller installer 
Compression=lzma 
SolidCompression=yes 
 
; Modern appearance 
WizardStyle=modern 
WizardResizable=no 
 
; Create desktop icon by default 
ChangesAssociations=yes 
CloseApplications=yes 
 
[Languages] 
Name: "english"; MessagesFile: "compiler:Default.isl" 
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl" 
 
[Tasks] 
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}" 
 
[Files] 
Source: "dist\Memoride\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion 
Source: "dist\Memoride\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs 
 
[Icons] 
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}" 
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}" 
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon 
 
[Run] 
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent 
 
[CustomMessages] 
english.WelcomeMessage=Welcome to the Memoride Setup Wizard 
english.InstallingMessage=Installing Memoride on your computer... 
english.FinishedMessage=Memoride has been successfully installed 
chinesesimp.WelcomeMessage=欢迎使用Memoride安装向导 
chinesesimp.InstallingMessage=正在安装Memoride到您的计算机... 
chinesesimp.FinishedMessage=Memoride已成功安装！ 
 
[Code] 
procedure InitializeWizard; 
begin 
  WizardForm.WelcomeLabel2.Caption := CustomMessage('WelcomeMessage'); 
end; 
 
procedure CurStepChanged(CurStep: TSetupStep); 
begin 
  if CurStep = ssInstall then begin 
    // Show installing message 
    WizardForm.StatusLabel.Caption := CustomMessage('InstallingMessage'); 
  end; 
 
  if CurStep = ssDone then begin 
    // Show finished message 
    WizardForm.FinishedLabel.Caption := CustomMessage('FinishedMessage'); 
  end; 
end; 

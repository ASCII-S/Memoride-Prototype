@echo off
setlocal EnableDelayedExpansion
echo Starting installer creation for Memoride...

:: Check if the built files exist
if not exist "dist\Memoride\Memoride.exe" (
  echo Error: Built application not found.
  echo Please build the application first using the build.bat script.
  echo The application should be in dist\Memoride directory.
  pause
  exit /b 1
)

:: Create installer output directory if not exists
if not exist installer mkdir installer

:: 直接使用用户提供的Inno Setup路径
set "ISCC=E:\EXE\Inno Setup 6\ISCC.exe"
set ISCC_FOUND=1
echo Using custom Inno Setup path: "%ISCC%"

:: 检查提供的路径是否存在
if not exist "%ISCC%" (
  echo Error: The specified Inno Setup compiler path does not exist.
  echo Path: "%ISCC%"
  echo.
  echo Falling back to automatic detection...
  set ISCC_FOUND=0
)

:: 只有在自定义路径无效时才尝试查找Inno Setup
if %ISCC_FOUND%==0 (
  :: Check if Inno Setup is installed - Enhanced detection
  echo Checking if Inno Setup is installed...
  
  :: Try multiple possible Inno Setup installation paths
  echo Looking for Inno Setup in standard locations...
  
  :: Check standard locations for Inno Setup 6
  if exist "%PROGRAMFILES(X86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%PROGRAMFILES(X86)%\Inno Setup 6\ISCC.exe"
    set ISCC_FOUND=1
    echo Found Inno Setup 6 in Program Files ^(x86^)
  ) else if exist "%PROGRAMFILES%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%PROGRAMFILES%\Inno Setup 6\ISCC.exe"
    set ISCC_FOUND=1
    echo Found Inno Setup 6 in Program Files
  )
  
  :: Check for Inno Setup 5 if 6 is not found
  if %ISCC_FOUND%==0 (
    if exist "%PROGRAMFILES(X86)%\Inno Setup 5\ISCC.exe" (
      set "ISCC=%PROGRAMFILES(X86)%\Inno Setup 5\ISCC.exe"
      set ISCC_FOUND=1
      echo Found Inno Setup 5 in Program Files ^(x86^)
    ) else if exist "%PROGRAMFILES%\Inno Setup 5\ISCC.exe" (
      set "ISCC=%PROGRAMFILES%\Inno Setup 5\ISCC.exe"
      set ISCC_FOUND=1
      echo Found Inno Setup 5 in Program Files
    )
  )
  
  :: Last resort - check PATH for ISCC.exe
  if %ISCC_FOUND%==0 (
    echo Checking PATH for ISCC.exe...
    where iscc.exe >nul 2>nul
    if !ERRORLEVEL!==0 (
      set ISCC=iscc.exe
      set ISCC_FOUND=1
      echo Found Inno Setup in PATH
    )
  )
  
  :: Let the user specify the path if not found
  if %ISCC_FOUND%==0 (
    echo Inno Setup compiler not found in standard locations.
    echo If you have installed Inno Setup, please enter the full path to ISCC.exe below.
    echo Example: C:\Program Files ^(x86^)\Inno Setup 6\ISCC.exe
    echo.
    set /p CUSTOM_ISCC="Enter path to ISCC.exe (or press Enter to cancel): "
    
    if not "!CUSTOM_ISCC!"=="" (
      if exist "!CUSTOM_ISCC!" (
        set "ISCC=!CUSTOM_ISCC!"
        set ISCC_FOUND=1
        echo Using custom Inno Setup path
      ) else (
        echo The specified file does not exist.
      )
    )
  )
)

:: Final check if Inno Setup was found
if %ISCC_FOUND%==0 (
  echo Inno Setup compiler not found.
  echo Please install Inno Setup 6 first.
  echo You can download it from: https://jrsoftware.org/isdl.php
  echo.
  echo After installation, run this script again.
  pause
  exit /b 1
)

echo Using Inno Setup at: "%ISCC%"

:: Create Inno Setup script
echo Creating Inno Setup script...

echo ; Memoride Installation Script > MemorideSetup.iss
echo ; Created for easy one-click installation >> MemorideSetup.iss
echo. >> MemorideSetup.iss
echo #define MyAppName "Memoride" >> MemorideSetup.iss
echo #define MyAppVersion "1.0" >> MemorideSetup.iss
echo #define MyAppPublisher "Memoride Team" >> MemorideSetup.iss
echo #define MyAppURL "https://github.com/yourusername/memoride" >> MemorideSetup.iss
echo #define MyAppExeName "Memoride.exe" >> MemorideSetup.iss
echo. >> MemorideSetup.iss
echo [Setup] >> MemorideSetup.iss
echo ; Basic application information >> MemorideSetup.iss
echo AppId={{6B3A6F56-9937-4586-9E55-5544ED931E98}} >> MemorideSetup.iss
echo AppName={#MyAppName} >> MemorideSetup.iss
echo AppVersion={#MyAppVersion} >> MemorideSetup.iss
echo AppPublisher={#MyAppPublisher} >> MemorideSetup.iss
echo AppPublisherURL={#MyAppURL} >> MemorideSetup.iss
echo AppSupportURL={#MyAppURL} >> MemorideSetup.iss
echo AppUpdatesURL={#MyAppURL} >> MemorideSetup.iss
echo. >> MemorideSetup.iss
echo ; Default installation directory >> MemorideSetup.iss
echo DefaultDirName={autopf}\{#MyAppName} >> MemorideSetup.iss
echo DefaultGroupName={#MyAppName} >> MemorideSetup.iss
echo DisableProgramGroupPage=yes >> MemorideSetup.iss
echo AllowNoIcons=yes >> MemorideSetup.iss
echo. >> MemorideSetup.iss
echo ; Output settings >> MemorideSetup.iss
echo OutputDir=installer >> MemorideSetup.iss
echo OutputBaseFilename=Memoride_Setup >> MemorideSetup.iss
echo. >> MemorideSetup.iss
echo ; Compression settings for smaller installer >> MemorideSetup.iss
echo Compression=lzma >> MemorideSetup.iss
echo SolidCompression=yes >> MemorideSetup.iss
echo. >> MemorideSetup.iss
echo ; Modern appearance >> MemorideSetup.iss
echo WizardStyle=modern >> MemorideSetup.iss
echo WizardResizable=no >> MemorideSetup.iss
echo. >> MemorideSetup.iss
echo ; Create desktop icon by default >> MemorideSetup.iss
echo ChangesAssociations=yes >> MemorideSetup.iss
echo CloseApplications=yes >> MemorideSetup.iss
echo. >> MemorideSetup.iss
echo [Languages] >> MemorideSetup.iss
echo Name: "english"; MessagesFile: "compiler:Default.isl" >> MemorideSetup.iss
echo Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl" >> MemorideSetup.iss
echo. >> MemorideSetup.iss
echo [Tasks] >> MemorideSetup.iss
echo Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}" >> MemorideSetup.iss
echo. >> MemorideSetup.iss
echo [Files] >> MemorideSetup.iss
echo Source: "dist\Memoride\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion >> MemorideSetup.iss
echo Source: "dist\Memoride\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs >> MemorideSetup.iss
echo. >> MemorideSetup.iss
echo [Icons] >> MemorideSetup.iss
echo Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}" >> MemorideSetup.iss
echo Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}" >> MemorideSetup.iss
echo Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon >> MemorideSetup.iss
echo. >> MemorideSetup.iss
echo [Run] >> MemorideSetup.iss
echo Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent >> MemorideSetup.iss
echo. >> MemorideSetup.iss
echo [CustomMessages] >> MemorideSetup.iss
echo english.WelcomeMessage=Welcome to the Memoride Setup Wizard >> MemorideSetup.iss
echo english.InstallingMessage=Installing Memoride on your computer... >> MemorideSetup.iss
echo english.FinishedMessage=Memoride has been successfully installed! >> MemorideSetup.iss
echo chinesesimp.WelcomeMessage=欢迎使用Memoride安装向导 >> MemorideSetup.iss
echo chinesesimp.InstallingMessage=正在安装Memoride到您的计算机... >> MemorideSetup.iss
echo chinesesimp.FinishedMessage=Memoride已成功安装！ >> MemorideSetup.iss
echo. >> MemorideSetup.iss
echo [Code] >> MemorideSetup.iss
echo procedure InitializeWizard; >> MemorideSetup.iss
echo begin >> MemorideSetup.iss
echo   WizardForm.WelcomeLabel2.Caption := CustomMessage('WelcomeMessage'); >> MemorideSetup.iss
echo end; >> MemorideSetup.iss
echo. >> MemorideSetup.iss
echo procedure CurStepChanged(CurStep: TSetupStep); >> MemorideSetup.iss
echo begin >> MemorideSetup.iss
echo   if CurStep = ssInstall then begin >> MemorideSetup.iss
echo     // Show installing message >> MemorideSetup.iss
echo     WizardForm.StatusLabel.Caption := CustomMessage('InstallingMessage'); >> MemorideSetup.iss
echo   end; >> MemorideSetup.iss
echo. >> MemorideSetup.iss
echo   if CurStep = ssDone then begin >> MemorideSetup.iss
echo     // Show finished message >> MemorideSetup.iss
echo     WizardForm.FinishedLabel.Caption := CustomMessage('FinishedMessage'); >> MemorideSetup.iss
echo   end; >> MemorideSetup.iss
echo end; >> MemorideSetup.iss

:: Use Inno Setup to compile installer
echo Using Inno Setup to compile installer...
"%ISCC%" MemorideSetup.iss

:: Check Inno Setup compilation result
if %errorlevel% neq 0 (
  echo Inno Setup compilation failed! Please check error messages.
  pause
  exit /b %errorlevel%
)

echo.
echo Installer creation completed!
echo Installer location: installer\Memoride_Setup.exe
echo.

:: Ask if user wants to run the installer
set /p run_installer=Do you want to run the installer now? (Y/N):

if /i "%run_installer%"=="Y" (
  echo Starting installer...
  start "" "installer\Memoride_Setup.exe"
)

echo.
echo Script execution completed!

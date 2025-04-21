@echo off
echo Starting Memoride application build...

:: Clean previous build files
echo Cleaning old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

:: Ensure system_prompts folder content is included
echo Checking system_prompts folder...
if not exist system_prompts (
  echo Warning: system_prompts folder does not exist!
  pause
  exit /b 1
)

:: Execute PyInstaller packaging command
echo Executing PyInstaller...
pyinstaller --name=Memoride --windowed --clean ^
  --icon=resources\icon.ico ^
  --add-data "resources;resources" ^
  --add-data "system_prompts\*.txt;system_prompts" ^
  --add-data "output_cards;output_cards" ^
  --exclude PyQt6 --exclude PySide6 ^
  main.py

:: Check build result
if %errorlevel% neq 0 (
  echo Build failed! Please check error messages.
  exit /b %errorlevel%
)

:: Manually copy system_prompts folder content (backup solution)
echo Ensuring system_prompts folder content is correctly copied...
if not exist "dist\Memoride\system_prompts" mkdir "dist\Memoride\system_prompts"
xcopy /Y /E "system_prompts\*.*" "dist\Memoride\system_prompts\"

echo.
echo Memoride application build successful!
echo Executable location: dist\Memoride\Memoride.exe
echo.

:: Ask whether to run the application
set /p run_app=Do you want to run the application now? (Y/N):

if /i "%run_app%"=="Y" (
  echo Launching Memoride...
  start dist\Memoride\Memoride.exe
)

echo.
echo Build script completed! 
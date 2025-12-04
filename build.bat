@echo off
cd /d "%~dp0"

echo ============================
echo   SpellingTrainer BUILD
echo ============================

echo === CLEAN OLD BUILDS ===
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
del /q SpellingTrainer.spec 2>nul

echo === CREATE/ACTIVATE VENV ===
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat

echo === UPDATE PIP (без переустановки) ===
python -m pip install --upgrade pip --no-input

echo === INSTALL DEPENDENCIES ===
if exist requirements.txt (
    echo Installing from requirements.txt...
    pip install -r requirements.txt --no-input
) else (
    echo Installing default dependencies...
    pip install PySide6 pillow requests pyinstaller --no-input
)

echo === BUILDING EXE ===
pyinstaller ^
 --noconfirm ^
 --onedir ^
 --windowed ^
 --name "SpellingTrainer" ^
 --icon "app_icon.png" ^
 --add-data "ui;ui" ^
 --add-data "core;core" ^
 --add-data "utils;utils" ^
 --hidden-import PySide6.QtCore ^
 --hidden-import PySide6.QtGui ^
 --hidden-import PySide6.QtWidgets ^
 --hidden-import requests ^
 --hidden-import PIL ^
 --hidden-import PIL._imaging ^
 --hidden-import PIL.Image ^
 --clean ^
 main.py

echo.
echo === DONE! ===
echo Installer build directory: dist\SpellingTrainer\
echo Executable: dist\SpellingTrainer\SpellingTrainer.exe
echo.
pause
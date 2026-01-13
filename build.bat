@echo off
chcp 65001 >nul
echo ======================================
echo Сборка Xiaomi Flasher в EXE
echo ======================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python не найден! Установите Python 3.8+
    pause
    exit /b 1
)

echo [*] Установка зависимостей...
pip install paramiko scp pyinstaller
if errorlevel 1 (
    echo [ERROR] Ошибка установки зависимостей
    pause
    exit /b 1
)

echo.
echo [*] Сборка EXE файла...
pyinstaller --onefile ^
    --console ^
    --name "Xiaomi_Stock_Flasher" ^
    --icon=NONE ^
    --clean ^
    xiaomi_flasher.py

if errorlevel 1 (
    echo [ERROR] Ошибка сборки
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Сборка завершена!
echo [*] EXE файл находится в папке: dist\Xiaomi_Stock_Flasher.exe
echo.
echo Инструкция по использованию:
echo   1. Положите файл прошивки (.bin) в папку с EXE
echo   2. Подключите компьютер к роутеру по кабелю или WiFi
echo   3. Запустите Xiaomi_Stock_Flasher.exe
echo.
pause

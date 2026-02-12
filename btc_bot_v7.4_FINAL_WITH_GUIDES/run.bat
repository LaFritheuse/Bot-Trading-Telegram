@echo off
echo ========================================
echo   BTC Trader Bot V7.4
echo ========================================
echo.

REM VÃ©rifier si .env existe
if not exist .env (
    echo [ERREUR] Fichier .env manquant !
    echo.
    echo Copiez .env.example vers .env et configurez vos credentials.
    pause
    exit /b 1
)

echo [OK] Fichier .env detecte
echo.

REM VÃ©rifier et installer les dÃ©pendances
echo [INFO] Verification des dependances...
py check_deps.py
if errorlevel 1 (
    echo.
    echo [ERREUR] Probleme avec les dependances !
    pause
    exit /b 1
)

echo [INFO] Demarrage du bot...
echo.
py main.py

pause
